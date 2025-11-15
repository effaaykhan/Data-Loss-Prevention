"""
DLP Agents API Endpoints (Wazuh-Style)
Agent registration, management, and monitoring
Supports auto-enrollment without pre-shared keys
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Body
from pydantic import BaseModel, Field, ConfigDict
import structlog
import uuid

from app.core.security import get_current_user, optional_auth
from app.core.database import get_mongodb
from app.core.cache import redis_client

logger = structlog.get_logger()
router = APIRouter()


# ============================================================================
# Pydantic Models
# ============================================================================

class AgentRegisterRequest(BaseModel):
    """Agent registration request"""
    name: str = Field(..., description="Agent hostname or friendly name")
    os: str = Field(..., description="Operating system (windows/linux/macos)")
    os_version: Optional[str] = Field(None, description="OS version")
    ip_address: str = Field(..., description="Agent IP address")
    version: str = Field(default="2.0.0", description="Agent version")
    capabilities: Optional[List[str]] = Field(
        default=None,
        description="Agent capabilities (file, clipboard, usb, network, etc.)"
    )
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "WIN-DESKTOP-01",
                "os": "windows",
                "os_version": "Windows 11 Pro",
                "ip_address": "192.168.1.100",
                "version": "2.0.0",
                "capabilities": ["file", "clipboard", "usb"],
                "metadata": {
                    "hostname": "WIN-DESKTOP-01",
                    "domain": "WORKGROUP"
                }
            }
        }
    )


class AgentRegisterResponse(BaseModel):
    """Agent registration response"""
    agent_id: str = Field(..., description="Assigned agent ID")
    name: str = Field(..., description="Agent name")
    status: str = Field(..., description="Agent status")
    registration_key: str = Field(..., description="Registration key for authentication")
    manager_url: str = Field(..., description="Manager URL for agent configuration")
    created_at: datetime = Field(..., description="Registration timestamp")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "agent_id": "AGENT-0001",
                "name": "WIN-DESKTOP-01",
                "status": "pending",
                "registration_key": "eyJ0eXAiOiJKV1QiLCJhbGc...",
                "manager_url": "https://localhost:55000",
                "created_at": "2025-01-12T10:00:00Z"
            }
        }
    )


class AgentAuthRequest(BaseModel):
    """Agent authentication request"""
    agent_id: str = Field(..., description="Agent ID")
    registration_key: str = Field(..., description="Registration key from registration")


class AgentAuthResponse(BaseModel):
    """Agent authentication response"""
    access_token: str = Field(..., description="JWT access token for API calls")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration in seconds")


class AgentInfo(BaseModel):
    """Agent information"""
    agent_id: str = Field(..., description="Agent ID")
    name: str = Field(..., description="Agent name/hostname")
    os: str = Field(..., description="Operating system")
    os_version: Optional[str] = Field(None, description="OS version")
    ip_address: str = Field(..., description="Agent IP address")
    version: str = Field(..., description="Agent version")
    status: str = Field(..., description="Agent status (active, inactive, pending)")
    last_seen: datetime = Field(..., description="Last heartbeat timestamp")
    last_ip: str = Field(..., description="Last known IP")
    registered_at: datetime = Field(..., description="Registration timestamp")
    capabilities: List[str] = Field(..., description="Agent capabilities")
    group: Optional[str] = Field(None, description="Agent group")
    tags: List[str] = Field(default_factory=list, description="Agent tags")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    config_version: str = Field(default="1", description="Current configuration version")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "agent_id": "AGENT-0001",
                "name": "WIN-DESKTOP-01",
                "os": "windows",
                "os_version": "Windows 11 Pro",
                "ip_address": "192.168.1.100",
                "version": "2.0.0",
                "status": "active",
                "last_seen": "2025-01-12T10:30:00Z",
                "last_ip": "192.168.1.100",
                "registered_at": "2025-01-12T10:00:00Z",
                "capabilities": ["file", "clipboard", "usb"],
                "group": "production",
                "tags": ["windows", "endpoint"],
                "metadata": {},
                "config_version": "1"
            }
        }
    )


class AgentHeartbeatRequest(BaseModel):
    """Agent heartbeat request"""
    ip_address: str = Field(..., description="Current IP address")
    status: str = Field(default="active", description="Agent status")
    metrics: Optional[Dict[str, Any]] = Field(None, description="Agent metrics (CPU, memory, etc.)")


class AgentStatusUpdate(BaseModel):
    """Agent status update"""
    status: str = Field(..., description="New status (active, inactive, suspended)")
    reason: Optional[str] = Field(None, description="Reason for status change")


class AgentConfigResponse(BaseModel):
    """Agent configuration response"""
    agent_id: str
    config_version: str
    config: Dict[str, Any]
    policies: List[Dict[str, Any]]
    updated_at: datetime


# ============================================================================
# Helper Functions
# ============================================================================

def generate_agent_id(db) -> str:
    """
    Generate next sequential agent ID (AGENT-0001, AGENT-0002, etc.)
    """
    # Get the count of existing agents
    agents_collection = db["agents"]
    count = agents_collection.count_documents({})

    # Generate ID with zero-padding
    agent_id = f"AGENT-{str(count + 1).zfill(4)}"

    return agent_id


def generate_registration_key(agent_id: str) -> str:
    """
    Generate registration key for agent
    This is a simple implementation - in production, use proper JWT
    """
    import hashlib
    import time

    # Create a unique key based on agent_id and timestamp
    data = f"{agent_id}:{time.time()}:{uuid.uuid4()}"
    key = hashlib.sha256(data.encode()).hexdigest()

    return key


async def check_agent_exists(agent_id: str, db) -> bool:
    """Check if agent exists"""
    agents_collection = db["agents"]
    agent = await agents_collection.find_one({"agent_id": agent_id})
    return agent is not None


async def get_agent_by_id(agent_id: str, db) -> Optional[Dict[str, Any]]:
    """Get agent by ID"""
    agents_collection = db["agents"]
    agent = await agents_collection.find_one({"agent_id": agent_id})
    return agent


# ============================================================================
# API Endpoints
# ============================================================================

@router.post("/register", response_model=AgentRegisterResponse, status_code=status.HTTP_201_CREATED)
async def register_agent(
    request: AgentRegisterRequest,
    current_user: Optional[Dict[str, Any]] = Depends(optional_auth)
) -> AgentRegisterResponse:
    """
    Register a new agent (auto-enrollment)

    This endpoint allows agents to self-register without pre-shared keys.
    Each agent receives a unique agent_id and registration_key.

    The agent should use the registration_key to authenticate via /agents/auth
    before making other API calls.

    Features:
    - Auto-generates sequential agent IDs (AGENT-0001, AGENT-0002, etc.)
    - No authentication required for registration
    - Returns registration key for subsequent authentication
    - Supports agent capabilities and metadata
    """
    db = get_mongodb()

    try:
        # Generate agent ID
        agent_id = generate_agent_id(db)

        # Generate registration key
        registration_key = generate_registration_key(agent_id)

        # Create agent document
        agent_doc = {
            "agent_id": agent_id,
            "name": request.name,
            "os": request.os,
            "os_version": request.os_version,
            "ip_address": request.ip_address,
            "last_ip": request.ip_address,
            "version": request.version,
            "status": "pending",  # Will become "active" after first heartbeat
            "capabilities": request.capabilities or [],
            "group": None,
            "tags": [],
            "metadata": request.metadata or {},
            "registration_key": registration_key,
            "registered_at": datetime.utcnow(),
            "last_seen": datetime.utcnow(),
            "config_version": "1",
            "created_by": current_user.get("email") if current_user else "agent_self_registration"
        }

        # Insert into database
        agents_collection = db["agents"]
        await agents_collection.insert_one(agent_doc)

        # Cache agent info in Redis for quick lookup
        if redis_client:
            await redis_client.setex(
                f"agent:{agent_id}",
                3600,  # 1 hour TTL
                agent_id
            )

        logger.info(
            "Agent registered",
            agent_id=agent_id,
            name=request.name,
            os=request.os,
            ip=request.ip_address,
            registered_by=current_user.get("email") if current_user else "self"
        )

        return AgentRegisterResponse(
            agent_id=agent_id,
            name=request.name,
            status="pending",
            registration_key=registration_key,
            manager_url="https://localhost:55000",  # TODO: Get from config
            created_at=agent_doc["registered_at"]
        )

    except Exception as e:
        logger.error("Agent registration failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )


@router.post("/auth", response_model=AgentAuthResponse)
async def authenticate_agent(
    request: AgentAuthRequest
) -> AgentAuthResponse:
    """
    Authenticate agent using registration key

    After registration, agents must authenticate to receive JWT tokens
    for making authenticated API calls.

    The registration_key is verified, and if valid, JWT tokens are issued.
    """
    db = get_mongodb()

    try:
        # Get agent from database
        agent = await get_agent_by_id(request.agent_id, db)

        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agent not found"
            )

        # Verify registration key
        if agent.get("registration_key") != request.registration_key:
            logger.warning(
                "Agent authentication failed - invalid key",
                agent_id=request.agent_id
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid registration key"
            )

        # Generate JWT tokens (simplified - in production use proper JWT)
        access_token = f"agent_token_{agent['agent_id']}_{uuid.uuid4()}"
        refresh_token = f"refresh_{agent['agent_id']}_{uuid.uuid4()}"

        # Store tokens in Redis with expiration
        if redis_client:
            # Access token expires in 24 hours
            await redis_client.setex(
                f"agent_token:{access_token}",
                86400,  # 24 hours
                request.agent_id
            )
            # Refresh token expires in 7 days
            await redis_client.setex(
                f"agent_refresh:{refresh_token}",
                604800,  # 7 days
                request.agent_id
            )

        # Update agent status to active
        agents_collection = db["agents"]
        await agents_collection.update_one(
            {"agent_id": request.agent_id},
            {
                "$set": {
                    "status": "active",
                    "last_auth": datetime.utcnow()
                }
            }
        )

        logger.info(
            "Agent authenticated",
            agent_id=request.agent_id,
            name=agent.get("name")
        )

        return AgentAuthResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=86400  # 24 hours
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Agent authentication error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Authentication failed: {str(e)}"
        )


@router.get("/", response_model=List[AgentInfo])
async def list_agents(
    status_filter: Optional[str] = None,
    os_filter: Optional[str] = None,
    group: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> List[AgentInfo]:
    """
    List all registered agents

    Supports filtering by status, OS, and group.
    Requires authentication.
    """
    db = get_mongodb()

    try:
        # Build query filter
        query = {}
        if status_filter:
            query["status"] = status_filter
        if os_filter:
            query["os"] = os_filter
        if group:
            query["group"] = group

        # Query agents
        agents_collection = db["agents"]
        cursor = agents_collection.find(query).sort("registered_at", -1).skip(skip).limit(limit)
        agents = await cursor.to_list(length=limit)

        # Remove sensitive fields
        for agent in agents:
            agent.pop("registration_key", None)
            agent.pop("_id", None)

        logger.info(
            "Agents listed",
            user=current_user["email"],
            count=len(agents),
            filters=query
        )

        return [AgentInfo(**agent) for agent in agents]

    except Exception as e:
        logger.error("Failed to list agents", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list agents: {str(e)}"
        )


@router.get("/{agent_id}", response_model=AgentInfo)
async def get_agent(
    agent_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> AgentInfo:
    """
    Get detailed information about a specific agent
    """
    db = get_mongodb()

    try:
        agent = await get_agent_by_id(agent_id, db)

        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent {agent_id} not found"
            )

        # Remove sensitive fields
        agent.pop("registration_key", None)
        agent.pop("_id", None)

        logger.info(
            "Agent details retrieved",
            user=current_user["email"],
            agent_id=agent_id
        )

        return AgentInfo(**agent)

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get agent", agent_id=agent_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve agent: {str(e)}"
        )


@router.post("/{agent_id}/heartbeat", status_code=status.HTTP_204_NO_CONTENT)
async def agent_heartbeat(
    agent_id: str,
    request: AgentHeartbeatRequest
):
    """
    Agent heartbeat endpoint

    Agents should call this endpoint every 60 seconds to indicate they're alive.
    Updates last_seen timestamp and IP address.

    No authentication required (agents can use this before full auth).
    """
    db = get_mongodb()

    try:
        # Check if agent exists
        if not await check_agent_exists(agent_id, db):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent {agent_id} not found"
            )

        # Update agent
        agents_collection = db["agents"]
        update_data = {
            "last_seen": datetime.utcnow(),
            "last_ip": request.ip_address,
            "status": request.status
        }

        if request.metrics:
            update_data["metrics"] = request.metrics

        await agents_collection.update_one(
            {"agent_id": agent_id},
            {"$set": update_data}
        )

        # Update cache
        if redis_client:
            await redis_client.setex(
                f"agent:heartbeat:{agent_id}",
                180,  # 3 minutes (allow 3 missed heartbeats)
                datetime.utcnow().isoformat()
            )

        logger.debug(
            "Agent heartbeat received",
            agent_id=agent_id,
            ip=request.ip_address,
            status=request.status
        )

        return None

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Heartbeat failed", agent_id=agent_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Heartbeat failed: {str(e)}"
        )


@router.patch("/{agent_id}/status", response_model=AgentInfo)
async def update_agent_status(
    agent_id: str,
    update: AgentStatusUpdate,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> AgentInfo:
    """
    Update agent status (admin only)

    Allows administrators to change agent status to:
    - active: Agent is operational
    - inactive: Agent is stopped/offline
    - suspended: Agent is suspended by admin
    """
    # Check admin permission
    if current_user.get("role") != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can update agent status"
        )

    db = get_mongodb()

    try:
        # Verify agent exists
        agent = await get_agent_by_id(agent_id, db)
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent {agent_id} not found"
            )

        # Update status
        agents_collection = db["agents"]
        await agents_collection.update_one(
            {"agent_id": agent_id},
            {
                "$set": {
                    "status": update.status,
                    "status_updated_at": datetime.utcnow(),
                    "status_updated_by": current_user["email"],
                    "status_reason": update.reason
                }
            }
        )

        # Get updated agent
        agent = await get_agent_by_id(agent_id, db)
        agent.pop("registration_key", None)
        agent.pop("_id", None)

        logger.info(
            "Agent status updated",
            agent_id=agent_id,
            new_status=update.status,
            updated_by=current_user["email"],
            reason=update.reason
        )

        return AgentInfo(**agent)

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to update agent status", agent_id=agent_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update status: {str(e)}"
        )


@router.get("/{agent_id}/config", response_model=AgentConfigResponse)
async def get_agent_config(
    agent_id: str
) -> AgentConfigResponse:
    """
    Get agent configuration

    Agents call this endpoint to fetch their configuration.
    Configuration includes monitoring settings, policies, etc.

    No authentication required (agents use this during bootstrap).
    """
    db = get_mongodb()

    try:
        # Verify agent exists
        agent = await get_agent_by_id(agent_id, db)
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent {agent_id} not found"
            )

        # TODO: Build configuration from YAML files and agent-specific settings
        # For now, return a basic configuration
        config = {
            "monitoring": {
                "file_system": {
                    "enabled": True,
                    "paths": ["C:\\Users\\*\\Desktop", "C:\\Users\\*\\Documents"],
                    "extensions": [".pdf", ".docx", ".xlsx", ".txt"]
                },
                "clipboard": {
                    "enabled": True,
                    "scan_interval": 5
                },
                "usb": {
                    "enabled": True
                }
            },
            "reporting": {
                "heartbeat_interval": 60,
                "batch_size": 100
            }
        }

        # Get policies for this agent (placeholder)
        policies = []

        logger.info(
            "Agent configuration retrieved",
            agent_id=agent_id
        )

        return AgentConfigResponse(
            agent_id=agent_id,
            config_version=agent.get("config_version", "1"),
            config=config,
            policies=policies,
            updated_at=datetime.utcnow()
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get agent config", agent_id=agent_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve configuration: {str(e)}"
        )


@router.delete("/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_agent(
    agent_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Delete an agent (admin only)

    Permanently removes an agent from the system.
    """
    # Check admin permission
    if current_user.get("role") != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can delete agents"
        )

    db = get_mongodb()

    try:
        # Verify agent exists
        if not await check_agent_exists(agent_id, db):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent {agent_id} not found"
            )

        # Delete agent
        agents_collection = db["agents"]
        await agents_collection.delete_one({"agent_id": agent_id})

        # Remove from cache
        if redis_client:
            await redis_client.delete(f"agent:{agent_id}")
            await redis_client.delete(f"agent:heartbeat:{agent_id}")

        logger.info(
            "Agent deleted",
            agent_id=agent_id,
            deleted_by=current_user["email"]
        )

        return None

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to delete agent", agent_id=agent_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete agent: {str(e)}"
        )


@router.get("/{agent_id}/logs")
async def get_agent_logs(
    agent_id: str,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: int = 100,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get logs/events from a specific agent

    This queries the events index for all events from this agent.
    """
    from app.core.opensearch import search_events

    try:
        # Build query for this agent
        query = {
            "term": {
                "agent.id.keyword": agent_id
            }
        }

        # Search events
        results = await search_events(
            query=query,
            start_date=start_date,
            end_date=end_date,
            size=limit
        )

        logger.info(
            "Agent logs retrieved",
            user=current_user["email"],
            agent_id=agent_id,
            count=results["total"]
        )

        return {
            "agent_id": agent_id,
            "total": results["total"],
            "logs": results["hits"],
            "took": results["took"]
        }

    except Exception as e:
        logger.error("Failed to get agent logs", agent_id=agent_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve logs: {str(e)}"
        )


@router.get("/{agent_id}/telemetry")
async def get_agent_telemetry(
    agent_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get agent telemetry data (metrics, health, etc.)
    """
    db = get_mongodb()

    try:
        agent = await get_agent_by_id(agent_id, db)

        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent {agent_id} not found"
            )

        # Calculate uptime
        registered_at = agent.get("registered_at")
        last_seen = agent.get("last_seen")

        if registered_at and last_seen:
            uptime = (last_seen - registered_at).total_seconds()
        else:
            uptime = 0

        # Get metrics from agent document
        metrics = agent.get("metrics", {})

        telemetry = {
            "agent_id": agent_id,
            "status": agent.get("status"),
            "uptime_seconds": uptime,
            "last_seen": last_seen,
            "metrics": metrics,
            "version": agent.get("version"),
            "capabilities": agent.get("capabilities", [])
        }

        logger.info(
            "Agent telemetry retrieved",
            user=current_user["email"],
            agent_id=agent_id
        )

        return telemetry

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get agent telemetry", agent_id=agent_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve telemetry: {str(e)}"
        )
