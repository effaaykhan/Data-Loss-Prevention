"""
Agents API Endpoints
Manage DLP agents deployed on endpoints
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel, Field, ConfigDict
import structlog

from app.core.security import get_current_user
from app.core.database import get_mongodb

logger = structlog.get_logger()
router = APIRouter()

# Agent is considered dead if no heartbeat received in 5 minutes
AGENT_TIMEOUT_MINUTES = 5


class AgentBase(BaseModel):
    """Base agent model"""
    name: str = Field(..., description="Agent name/hostname")
    os: str = Field(..., description="Operating system (windows/linux)")
    ip_address: str = Field(..., description="Agent IP address")
    version: str = Field(default="1.0.0", description="Agent version")


class AgentCreate(BaseModel):
    """Agent creation model"""
    agent_id: Optional[str] = Field(None, description="Custom agent ID (auto-generated if not provided)")
    name: str = Field(..., description="Agent name/hostname")
    os: str = Field(..., description="Operating system (windows/linux)")
    ip_address: str = Field(..., description="Agent IP address")
    version: str = Field(default="1.0.0", description="Agent version")


class Agent(AgentBase):
    """Agent response model"""
    agent_id: str = Field(..., description="Unique agent ID")
    # TODO: Implement agent resume functionality so agents can resume instead of creating new entries
    # Status field removed - agents are considered active if they've sent heartbeat within timeout period
    last_seen: datetime = Field(..., description="Last heartbeat timestamp")
    created_at: datetime = Field(..., description="Registration timestamp")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "agent_id": "agt-001",
                "name": "WIN-DESK-01",
                "os": "windows",
                "ip_address": "192.168.1.100",
                "version": "1.0.0",
                "status": "online",
                "last_seen": "2025-01-02T10:30:00Z",
                "created_at": "2025-01-01T08:00:00Z"
            }
        }
    )


@router.get("/", response_model=List[Agent])
async def list_agents(
    os: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
) -> List[Agent]:
    """
    List all active DLP agents (only agents that have sent heartbeat within timeout period)

    Query parameters:
    - os: Filter by operating system (windows/linux)
    
    Note: Only shows agents that have sent heartbeat within the last 5 minutes.
    Dead agents are automatically filtered out.
    """
    db = get_mongodb()
    agents_collection = db["agents"]

    # Calculate cutoff time for active agents
    cutoff_time = datetime.utcnow() - timedelta(minutes=AGENT_TIMEOUT_MINUTES)

    # Build query filter - only show agents with recent heartbeat
    query = {
        "last_seen": {"$gte": cutoff_time}
    }
    if os:
        query["os"] = os

    # Query agents from database
    agents_cursor = agents_collection.find(query).sort("last_seen", -1)
    agents = []

    async for agent_doc in agents_cursor:
        # Remove MongoDB _id field and status field (no longer used)
        if "_id" in agent_doc:
            del agent_doc["_id"]
        if "status" in agent_doc:
            del agent_doc["status"]
        
        # Convert datetime objects to ISO format strings with Z suffix (UTC)
        if "last_seen" in agent_doc and isinstance(agent_doc["last_seen"], datetime):
            agent_doc["last_seen"] = agent_doc["last_seen"].isoformat() + "Z"
        if "created_at" in agent_doc and isinstance(agent_doc["created_at"], datetime):
            agent_doc["created_at"] = agent_doc["created_at"].isoformat() + "Z"
        
        agents.append(Agent(**agent_doc))

    # Cleanup dead agents in background (non-blocking)
    try:
        cleanup_result = await agents_collection.delete_many({
            "last_seen": {"$lt": cutoff_time}
        })
        if cleanup_result.deleted_count > 0:
            logger.info("Cleaned up dead agents", count=cleanup_result.deleted_count)
    except Exception as e:
        logger.warning("Failed to cleanup dead agents", error=str(e))

    logger.info("Listed agents", count=len(agents), filters=query)
    return agents


@router.post("/", response_model=Agent, status_code=status.HTTP_201_CREATED)
async def register_agent(
    request: Request,
    agent: AgentCreate,
) -> Agent:
    """
    Register a new DLP agent (public endpoint - no auth required for agent self-registration)
    """
    db = get_mongodb()
    agents_collection = db["agents"]

    # Extract agent_id from raw request body (workaround for Pydantic not picking up the field)
    body = await request.json()
    provided_agent_id = body.get("agent_id")

    # Use provided agent_id or generate one from name
    if provided_agent_id:
        agent_id = provided_agent_id
    else:
        agent_id = f"{agent.os.upper()}-{agent.name.replace(' ', '-')}"

    # Create agent document with custom agent_id
    now = datetime.utcnow()
    agent_doc = {
        "agent_id": agent_id,
        "name": agent.name,
        "os": agent.os,
        "ip_address": agent.ip_address,
        "version": agent.version,
        "last_seen": now,
        "created_at": now,
    }

    # Upsert - update if exists, insert if new
    # Always update name even if agent already exists (allows renaming)
    await agents_collection.update_one(
        {"agent_id": agent_id},
        {"$set": agent_doc},
        upsert=True
    )

    logger.info("Agent registered", agent_id=agent_id, name=agent.name)
    return Agent(**agent_doc)


@router.get("/{agent_id}", response_model=Agent)
async def get_agent(
    agent_id: str,
    current_user: dict = Depends(get_current_user),
) -> Agent:
    """
    Get details of a specific agent
    """
    db = get_mongodb()
    agents_collection = db["agents"]

    agent_doc = await agents_collection.find_one({"agent_id": agent_id})

    if not agent_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent {agent_id} not found"
        )

    # Remove MongoDB _id field
    if "_id" in agent_doc:
        del agent_doc["_id"]

    return Agent(**agent_doc)


class HeartbeatRequest(BaseModel):
    """Heartbeat request model"""
    timestamp: Optional[str] = Field(None, description="Agent timestamp (ISO format)")
    status: Optional[str] = Field(None, description="Agent status")
    ip_address: Optional[str] = Field(None, description="Current IP address")


@router.put("/{agent_id}/heartbeat")
async def agent_heartbeat(
    agent_id: str,
    request: Optional[HeartbeatRequest] = None,
) -> Dict[str, Any]:
    """
    Update agent heartbeat (public endpoint - no auth required for agents)
    
    Accepts optional request body with timestamp. If provided, validates it's within
    reasonable bounds (not more than 5 minutes in the future or past).
    Uses server time if not provided or invalid.
    """
    db = get_mongodb()
    agents_collection = db["agents"]

    # Determine timestamp to use
    from datetime import timezone
    server_time = datetime.now(timezone.utc)
    heartbeat_time = server_time
    
    if request and request.timestamp:
        try:
            # Parse agent-provided timestamp
            agent_time_str = request.timestamp.replace('Z', '+00:00')
            agent_time = datetime.fromisoformat(agent_time_str)
            # Ensure agent_time is timezone-aware for comparison
            if agent_time.tzinfo is None:
                agent_time = agent_time.replace(tzinfo=timezone.utc)
            # Validate timestamp is within reasonable bounds (±5 minutes)
            time_diff = abs((agent_time - server_time).total_seconds())
            if time_diff <= 300:  # 5 minutes
                heartbeat_time = agent_time
            else:
                logger.warning(
                    "Agent timestamp out of bounds, using server time",
                    agent_id=agent_id,
                    agent_time=request.timestamp,
                    server_time=server_time.isoformat(),
                    diff_seconds=time_diff
                )
        except (ValueError, AttributeError) as e:
            logger.debug(f"Invalid timestamp format, using server time: {e}")

    # Update last_seen and optionally other fields
    update_data = {
        "last_seen": heartbeat_time
    }
    
    if request and request.ip_address:
        update_data["ip_address"] = request.ip_address

    result = await agents_collection.update_one(
        {"agent_id": agent_id},
        {"$set": update_data}
    )

    if result.matched_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent {agent_id} not found"
        )

    logger.debug("Agent heartbeat", agent_id=agent_id, timestamp=heartbeat_time.isoformat())
    return {
        "status": "success",
        "message": "Heartbeat recorded",
        "timestamp": heartbeat_time.isoformat()
    }


@router.delete("/{agent_id}/unregister", status_code=status.HTTP_204_NO_CONTENT)
async def unregister_agent(
    agent_id: str,
):
    """
    Unregister an agent (public endpoint - called by agent on shutdown)
    This allows agents to cleanly remove themselves when they stop running.
    """
    db = get_mongodb()
    agents_collection = db["agents"]

    result = await agents_collection.delete_one({"agent_id": agent_id})

    if result.deleted_count == 0:
        # Agent not found - that's okay, might have been already deleted
        logger.debug("Agent not found for unregister", agent_id=agent_id)
    else:
        logger.info("Agent unregistered", agent_id=agent_id)

    return None


@router.delete("/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_agent(
    agent_id: str,
    current_user: dict = Depends(get_current_user),
):
    """
    Delete an agent entry from the database (admin action)
    Note: This only removes the database entry. The agent process itself must be stopped manually.
    """
    db = get_mongodb()
    agents_collection = db["agents"]

    result = await agents_collection.delete_one({"agent_id": agent_id})

    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent {agent_id} not found"
        )

    logger.info("Agent deleted", agent_id=agent_id, user=current_user.get("email"))
    return None


@router.get("/stats/summary")
async def get_agents_summary(
    current_user: dict = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Get summary statistics of active agents
    """
    db = get_mongodb()
    agents_collection = db["agents"]

    # Calculate cutoff time for active agents
    cutoff_time = datetime.utcnow() - timedelta(minutes=AGENT_TIMEOUT_MINUTES)

    # Count active agents (have sent heartbeat within timeout)
    active = await agents_collection.count_documents({
        "last_seen": {"$gte": cutoff_time}
    })

    # Count total agents (including dead ones)
    total = await agents_collection.count_documents({})

    return {
        "total": total,
        "active": active,
    }
