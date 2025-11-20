"""
Agents API Endpoints
Manage DLP agents deployed on endpoints
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel, Field, ConfigDict
import structlog

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.core.database import get_mongodb, get_db
from app.services.policy_service import PolicyService
from app.policies.agent_policy_transformer import AgentPolicyTransformer
from app.core.cache import get_cache, CacheService

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
    capabilities: Dict[str, bool] = Field(default_factory=dict, description="Agent capability flags")


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
    policy_version: Optional[str] = Field(None, description="Last policy bundle version applied")
    policy_sync_status: Optional[str] = Field(None, description="Most recent policy sync status")
    policy_last_synced_at: Optional[str] = Field(None, description="ISO timestamp for last policy sync")
    policy_sync_error: Optional[str] = Field(None, description="Last policy sync error message, if any")

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
        if "capabilities" not in agent_doc:
            agent_doc["capabilities"] = {}
        
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
    capabilities = body.get("capabilities") or {}

    agent_doc = {
        "agent_id": agent_id,
        "name": agent.name,
        "os": agent.os,
        "ip_address": agent.ip_address,
        "version": agent.version,
        "last_seen": now,
        "created_at": now,
        "capabilities": capabilities,
        "policy_version": None,
        "policy_sync_status": "never",
        "policy_last_synced_at": None,
        "policy_sync_error": None,
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
    if "capabilities" not in agent_doc:
        agent_doc["capabilities"] = {}

    return Agent(**agent_doc)


class HeartbeatRequest(BaseModel):
    """Heartbeat request model"""
    timestamp: Optional[str] = Field(None, description="Agent timestamp (ISO format)")
    status: Optional[str] = Field(None, description="Agent status")
    ip_address: Optional[str] = Field(None, description="Current IP address")
    policy_version: Optional[str] = Field(None, description="Agent policy bundle version")
    policy_sync_status: Optional[str] = Field(None, description="Most recent policy sync status")
    policy_last_synced_at: Optional[str] = Field(None, description="ISO timestamp for last policy sync")
    policy_sync_error: Optional[str] = Field(None, description="Error details from last policy sync")


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
    if request and request.policy_version is not None:
        update_data["policy_version"] = request.policy_version
    if request and request.policy_sync_status is not None:
        update_data["policy_sync_status"] = request.policy_sync_status
    if request and request.policy_last_synced_at is not None:
        update_data["policy_last_synced_at"] = request.policy_last_synced_at
    if request and request.policy_sync_error is not None:
        update_data["policy_sync_error"] = request.policy_sync_error

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


class AgentPolicySyncRequest(BaseModel):
    """Agent policy sync request"""
    platform: Optional[str] = Field(None, description="Override detected platform (windows/linux)")
    capabilities: Dict[str, bool] = Field(default_factory=dict, description="Agent capability flags")
    installed_version: Optional[str] = Field(None, description="Currently installed bundle version")


class AgentPolicySyncResponse(BaseModel):
    """Agent policy sync response"""
    status: str = Field(default="updated", description="updated|up_to_date")
    version: str
    generated_at: datetime
    policy_count: int
    policies: Dict[str, Any] = Field(default_factory=dict)


_agent_policy_transformer = AgentPolicyTransformer()


def _get_agent_policy_transformer() -> AgentPolicyTransformer:
    return _agent_policy_transformer


@router.post("/{agent_id}/policies/sync", response_model=AgentPolicySyncResponse)
async def sync_agent_policies(
    agent_id: str,
    sync_request: AgentPolicySyncRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Provide agents with a policy bundle tailored to their platform/capabilities.
    """
    mongo = get_mongodb()
    agents_collection = mongo["agents"]

    agent_doc = await agents_collection.find_one({"agent_id": agent_id})
    if not agent_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent {agent_id} not found",
        )

    platform = (sync_request.platform or agent_doc.get("os") or "windows").lower()
    capabilities = {**agent_doc.get("capabilities", {}), **sync_request.capabilities}

    # Normalize capability flags
    capabilities = {k: bool(v) for k, v in capabilities.items()}
    capability_key = "-".join(sorted([k for k, v in capabilities.items() if v])) or "default"

    cache_service: Optional[CacheService] = None
    try:
        cache_service = CacheService(get_cache())
    except RuntimeError:
        cache_service = None

    cache_key = f"agent-policy-bundle:{platform}:{capability_key}"
    bundle: Optional[Dict[str, Any]] = None

    if cache_service:
        bundle = await cache_service.get(cache_key)

    if not bundle:
        policy_service = PolicyService(db)
        enabled_policies = await policy_service.get_enabled_policies()
        transformer = _get_agent_policy_transformer()
        bundle = transformer.build_bundle(enabled_policies, platform, capabilities)
        if cache_service:
            await cache_service.set(cache_key, bundle, expire=30)

    if not bundle:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to build policy bundle",
        )

    version = bundle.get("version")
    generated_at_raw = bundle.get("generated_at")
    generated_at = datetime.fromisoformat(generated_at_raw.replace("Z", "+00:00")) if generated_at_raw else datetime.utcnow()

    if sync_request.installed_version and sync_request.installed_version == version:
        logger.debug("Agent policy bundle up-to-date", agent_id=agent_id, platform=platform, version=version)
        return AgentPolicySyncResponse(
            status="up_to_date",
            version=version,
            generated_at=generated_at,
            policy_count=bundle.get("policy_count", 0),
            policies={},
        )

    logger.info(
        "Agent policy bundle issued",
        agent_id=agent_id,
        platform=platform,
        version=version,
        policy_count=bundle.get("policy_count", 0),
    )

    return AgentPolicySyncResponse(
        status="updated",
        version=version,
        generated_at=generated_at,
        policy_count=bundle.get("policy_count", 0),
        policies=bundle.get("policies", {}),
    )
