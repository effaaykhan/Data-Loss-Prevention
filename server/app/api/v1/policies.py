"""
DLP Policies API Endpoints
Create, update, and manage DLP policies
"""

from typing import List, Dict, Any, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.core.security import get_current_user, require_role
from app.core.database import get_db
from app.services.policy_service import PolicyService

logger = structlog.get_logger()
router = APIRouter()


class PolicyCondition(BaseModel):
    """
    Generic condition used by the server-side policy engine.
    Agents typically consume a higher-level view (file types, size, keywords)
    derived from these conditions.
    """

    field: str
    operator: str
    value: Any


class PolicyAction(BaseModel):
    type: str
    parameters: Optional[Dict[str, Any]] = None


class Policy(BaseModel):
    """
    API schema for policies.

    This wraps the internal SQLAlchemy model and exposes a clean JSON structure
    that can also be mirrored to MongoDB or consumed directly by agents.
    """

    id: Optional[str] = None
    name: str
    description: str
    enabled: bool = True
    priority: int = 100
    conditions: List[PolicyCondition]
    actions: List[PolicyAction]
    compliance_tags: List[str] = []
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    created_by: Optional[str] = None


@router.get("/", response_model=List[Policy])
async def get_policies(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    enabled_only: bool = False,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get all DLP policies
    """
    policy_service = PolicyService(db)
    policies = await policy_service.get_all_policies(
        skip=skip,
        limit=limit,
        enabled_only=enabled_only,
    )

    return [
        {
            "id": str(policy.id),
            "name": policy.name,
            "description": policy.description,
            "enabled": policy.enabled,
            "priority": policy.priority,
            # Internally we store a JSON blob with "match" + "rules".
            # Expose only the rules list to the API.
            "conditions": policy.conditions.get("rules", [])
            if isinstance(policy.conditions, dict)
            else [],
            # Actions JSON is a mapping: {"alert": {...}, "block": {...}}
            # Convert to a list for the API.
            "actions": [
                {"type": k, "parameters": v} for k, v in policy.actions.items()
            ]
            if isinstance(policy.actions, dict)
            else [],
            "compliance_tags": policy.compliance_tags or [],
            "created_at": policy.created_at,
            "updated_at": policy.updated_at,
            "created_by": policy.created_by,
        }
        for policy in policies
    ]


@router.get("/{policy_id}", response_model=Policy)
async def get_policy(
    policy_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get a single DLP policy by ID.
    Useful for editing from the dashboard and for agents that want
    to cache individual policies.
    """
    policy_service = PolicyService(db)
    policy = await policy_service.get_policy_by_id(policy_id)

    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")

    return {
        "id": str(policy.id),
        "name": policy.name,
        "description": policy.description,
        "enabled": policy.enabled,
        "priority": policy.priority,
        "conditions": policy.conditions.get("rules", [])
        if isinstance(policy.conditions, dict)
        else [],
        "actions": [
            {"type": k, "parameters": v} for k, v in policy.actions.items()
        ]
        if isinstance(policy.actions, dict)
        else [],
        "compliance_tags": policy.compliance_tags or [],
        "created_at": policy.created_at,
        "updated_at": policy.updated_at,
        "created_by": policy.created_by,
    }


@router.post("/", response_model=Policy, status_code=status.HTTP_201_CREATED)
async def create_policy(
    policy: Policy,
    current_user: dict = Depends(require_role("analyst")),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new DLP policy
    """
    policy_service = PolicyService(db)

    # Convert Pydantic models to dict format expected by service
    conditions_dict = {
        "match": "all",
        "rules": [cond.dict() for cond in policy.conditions]
    }
    actions_dict = {action.type: action.parameters for action in policy.actions}

    try:
        created_policy = await policy_service.create_policy(
            name=policy.name,
            description=policy.description,
            conditions=conditions_dict,
            actions=actions_dict,
            created_by=current_user["sub"],
            enabled=policy.enabled,
            priority=policy.priority,
            compliance_tags=policy.compliance_tags,
        )

        logger.info(
            "Policy created",
            policy_name=policy.name,
            policy_id=str(created_policy.id),
            user=current_user["email"],
        )

        return {
            "id": str(created_policy.id),
            "name": created_policy.name,
            "description": created_policy.description,
            "enabled": created_policy.enabled,
            "priority": created_policy.priority,
            "conditions": policy.conditions,
            "actions": policy.actions,
            "compliance_tags": created_policy.compliance_tags or [],
            "created_at": created_policy.created_at,
            "updated_at": created_policy.updated_at,
            "created_by": created_policy.created_by,
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{policy_id}", response_model=Policy)
async def update_policy(
    policy_id: str,
    policy: Policy,
    current_user: dict = Depends(require_role("analyst")),
    db: AsyncSession = Depends(get_db),
):
    """
    Update existing DLP policy
    """
    policy_service = PolicyService(db)

    # Convert Pydantic models to dict format
    conditions_dict = {
        "match": "all",
        "rules": [cond.dict() for cond in policy.conditions]
    }
    actions_dict = {action.type: action.parameters for action in policy.actions}

    try:
        updated_policy = await policy_service.update_policy(
            policy_id=policy_id,
            name=policy.name,
            description=policy.description,
            conditions=conditions_dict,
            actions=actions_dict,
            enabled=policy.enabled,
            priority=policy.priority,
            compliance_tags=policy.compliance_tags,
        )

        if not updated_policy:
            raise HTTPException(status_code=404, detail="Policy not found")

        logger.info(
            "Policy updated",
            policy_id=policy_id,
            user=current_user["email"],
        )

        return {
            "id": str(updated_policy.id),
            "name": updated_policy.name,
            "description": updated_policy.description,
            "enabled": updated_policy.enabled,
            "priority": updated_policy.priority,
            "conditions": policy.conditions,
            "actions": policy.actions,
            "compliance_tags": updated_policy.compliance_tags or [],
            "created_at": updated_policy.created_at,
            "updated_at": updated_policy.updated_at,
            "created_by": updated_policy.created_by,
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{policy_id}")
async def delete_policy(
    policy_id: str,
    current_user: dict = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete DLP policy
    """
    policy_service = PolicyService(db)
    success = await policy_service.delete_policy(policy_id)

    if not success:
        raise HTTPException(status_code=404, detail="Policy not found")

    logger.info(
        "Policy deleted",
        policy_id=policy_id,
        user=current_user["email"],
    )

    return {"message": "Policy deleted successfully"}


@router.post("/{policy_id}/enable")
async def enable_policy(
    policy_id: str,
    current_user: dict = Depends(require_role("analyst")),
    db: AsyncSession = Depends(get_db),
):
    """
    Enable a policy
    """
    policy_service = PolicyService(db)
    policy = await policy_service.enable_policy(policy_id)

    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")

    logger.info(
        "Policy enabled",
        policy_id=policy_id,
        user=current_user["email"],
    )

    return {"message": "Policy enabled successfully", "policy_id": str(policy.id)}


@router.post("/{policy_id}/disable")
async def disable_policy(
    policy_id: str,
    current_user: dict = Depends(require_role("analyst")),
    db: AsyncSession = Depends(get_db),
):
    """
    Disable a policy
    """
    policy_service = PolicyService(db)
    policy = await policy_service.disable_policy(policy_id)

    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")

    logger.info(
        "Policy disabled",
        policy_id=policy_id,
        user=current_user["email"],
    )

    return {"message": "Policy disabled successfully", "policy_id": str(policy.id)}
