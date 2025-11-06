"""
Agents API Endpoints
Manage DLP agents deployed on endpoints
"""

from typing import List, Dict, Any, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, ConfigDict
import structlog

from app.core.security import get_current_user
from app.core.database import get_mongodb

logger = structlog.get_logger()
router = APIRouter()


class AgentBase(BaseModel):
    """Base agent model"""
    name: str = Field(..., description="Agent name/hostname")
    os: str = Field(..., description="Operating system (windows/linux)")
    ip_address: str = Field(..., description="Agent IP address")
    version: str = Field(default="1.0.0", description="Agent version")


class AgentCreate(AgentBase):
    """Agent creation model"""
    pass


class Agent(AgentBase):
    """Agent response model"""
    agent_id: str = Field(..., description="Unique agent ID")
    status: str = Field(..., description="Agent status (online/offline/warning)")
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
    status: Optional[str] = None,
    os: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
) -> List[Agent]:
    """
    List all registered DLP agents

    Query parameters:
    - status: Filter by status (online/offline/warning)
    - os: Filter by operating system (windows/linux)
    """
    db = get_mongodb()
    agents_collection = db["agents"]

    # Build query filter
    query = {}
    if status:
        query["status"] = status
    if os:
        query["os"] = os

    # Query agents from database
    agents_cursor = agents_collection.find(query).sort("last_seen", -1)
    agents = []

    async for agent_doc in agents_cursor:
        # Convert MongoDB document to Agent model
        agent_doc["agent_id"] = str(agent_doc["_id"])
        del agent_doc["_id"]
        agents.append(Agent(**agent_doc))

    logger.info("Listed agents", count=len(agents), filters=query)
    return agents


@router.post("/", response_model=Agent, status_code=status.HTTP_201_CREATED)
async def register_agent(
    agent: AgentCreate,
    current_user: dict = Depends(get_current_user),
) -> Agent:
    """
    Register a new DLP agent
    """
    db = get_mongodb()
    agents_collection = db["agents"]

    # Create agent document
    now = datetime.utcnow()
    agent_doc = {
        **agent.model_dump(),
        "status": "online",
        "last_seen": now,
        "created_at": now,
    }

    # Insert into database
    result = await agents_collection.insert_one(agent_doc)
    agent_doc["agent_id"] = str(result.inserted_id)
    del agent_doc["_id"]

    logger.info("Agent registered", agent_id=agent_doc["agent_id"], name=agent.name)
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

    from bson import ObjectId
    agent_doc = await agents_collection.find_one({"_id": ObjectId(agent_id)})

    if not agent_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent {agent_id} not found"
        )

    agent_doc["agent_id"] = str(agent_doc["_id"])
    del agent_doc["_id"]

    return Agent(**agent_doc)


@router.put("/{agent_id}/heartbeat")
async def agent_heartbeat(
    agent_id: str,
    current_user: dict = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Update agent heartbeat (called by agents periodically)
    """
    db = get_mongodb()
    agents_collection = db["agents"]

    from bson import ObjectId
    result = await agents_collection.update_one(
        {"_id": ObjectId(agent_id)},
        {
            "$set": {
                "last_seen": datetime.utcnow(),
                "status": "online"
            }
        }
    )

    if result.matched_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent {agent_id} not found"
        )

    logger.debug("Agent heartbeat", agent_id=agent_id)
    return {"status": "success", "message": "Heartbeat recorded"}


@router.delete("/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_agent(
    agent_id: str,
    current_user: dict = Depends(get_current_user),
):
    """
    Delete/unregister an agent
    """
    db = get_mongodb()
    agents_collection = db["agents"]

    from bson import ObjectId
    result = await agents_collection.delete_one({"_id": ObjectId(agent_id)})

    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent {agent_id} not found"
        )

    logger.info("Agent deleted", agent_id=agent_id)
    return None


@router.get("/stats/summary")
async def get_agents_summary(
    current_user: dict = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Get summary statistics of all agents
    """
    db = get_mongodb()
    agents_collection = db["agents"]

    # Aggregate stats
    total = await agents_collection.count_documents({})
    online = await agents_collection.count_documents({"status": "online"})
    offline = await agents_collection.count_documents({"status": "offline"})
    warning = await agents_collection.count_documents({"status": "warning"})

    return {
        "total": total,
        "online": online,
        "offline": offline,
        "warning": warning,
    }
