"""
Classification API Endpoints
Data classification and sensitive content detection
"""

from typing import List, Dict, Any, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field, ConfigDict
import structlog

from app.core.security import get_current_user
from app.core.database import get_mongodb

logger = structlog.get_logger()
router = APIRouter()


class ClassifiedFile(BaseModel):
    """Classified file model"""
    file_id: str = Field(..., description="Unique file ID")
    filename: str = Field(..., description="Original filename")
    file_path: str = Field(..., description="File path")
    file_type: str = Field(..., description="File extension/type")
    file_size: int = Field(..., description="File size in bytes")
    classification: str = Field(..., description="Classification level (public/internal/confidential/restricted)")
    patterns_detected: List[str] = Field(default=[], description="Detected sensitive patterns")
    agent_id: str = Field(..., description="Agent that scanned the file")
    user_email: str = Field(..., description="User who owns/created the file")
    scanned_at: datetime = Field(..., description="Scan timestamp")
    confidence_score: float = Field(..., description="Classification confidence (0-1)")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "file_id": "file-001",
                "filename": "financial_report_Q4.xlsx",
                "file_path": "C:/Users/john/Documents/financial_report_Q4.xlsx",
                "file_type": ".xlsx",
                "file_size": 524288,
                "classification": "confidential",
                "patterns_detected": ["credit_card", "ssn"],
                "agent_id": "agt-001",
                "user_email": "john.doe@company.com",
                "scanned_at": "2025-01-02T10:30:00Z",
                "confidence_score": 0.95
            }
        }
    )


@router.get("/files", response_model=List[ClassifiedFile])
async def list_classified_files(
    classification: Optional[str] = Query(None, description="Filter by classification level"),
    file_type: Optional[str] = Query(None, description="Filter by file type"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of results"),
    skip: int = Query(0, ge=0, description="Number of results to skip"),
    current_user: dict = Depends(get_current_user),
) -> List[ClassifiedFile]:
    """
    List classified files

    Query parameters:
    - classification: Filter by classification level (public/internal/confidential/restricted)
    - file_type: Filter by file extension (e.g., .pdf, .xlsx)
    - limit: Maximum results (default: 100)
    - skip: Pagination offset (default: 0)
    """
    db = get_mongodb()
    files_collection = db["classified_files"]

    # Build query filter
    query = {}
    if classification:
        query["classification"] = classification
    if file_type:
        query["file_type"] = file_type

    # Query files from database
    files_cursor = files_collection.find(query).sort("scanned_at", -1).skip(skip).limit(limit)
    files = []

    async for file_doc in files_cursor:
        # Convert MongoDB document to ClassifiedFile model
        file_doc["file_id"] = str(file_doc["_id"])
        del file_doc["_id"]
        files.append(ClassifiedFile(**file_doc))

    logger.info("Listed classified files", count=len(files), filters=query)
    return files


@router.get("/files/{file_id}", response_model=ClassifiedFile)
async def get_classified_file(
    file_id: str,
    current_user: dict = Depends(get_current_user),
) -> ClassifiedFile:
    """
    Get details of a specific classified file
    """
    db = get_mongodb()
    files_collection = db["classified_files"]

    from bson import ObjectId
    file_doc = await files_collection.find_one({"_id": ObjectId(file_id)})

    if not file_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File {file_id} not found"
        )

    file_doc["file_id"] = str(file_doc["_id"])
    del file_doc["_id"]

    return ClassifiedFile(**file_doc)


@router.get("/stats/summary")
async def get_classification_summary(
    current_user: dict = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Get summary statistics of classified files
    """
    db = get_mongodb()
    files_collection = db["classified_files"]

    # Aggregate stats by classification level
    total = await files_collection.count_documents({})
    public = await files_collection.count_documents({"classification": "public"})
    internal = await files_collection.count_documents({"classification": "internal"})
    confidential = await files_collection.count_documents({"classification": "confidential"})
    restricted = await files_collection.count_documents({"classification": "restricted"})

    # Get pattern detection stats
    patterns_pipeline = [
        {"$unwind": "$patterns_detected"},
        {"$group": {"_id": "$patterns_detected", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 10}
    ]
    patterns_cursor = files_collection.aggregate(patterns_pipeline)
    top_patterns = []
    async for pattern in patterns_cursor:
        top_patterns.append({
            "pattern": pattern["_id"],
            "count": pattern["count"]
        })

    return {
        "total_files": total,
        "by_classification": {
            "public": public,
            "internal": internal,
            "confidential": confidential,
            "restricted": restricted,
        },
        "top_patterns": top_patterns,
    }


@router.get("/stats/by-type")
async def get_classification_by_type(
    current_user: dict = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Get classification statistics grouped by file type
    """
    db = get_mongodb()
    files_collection = db["classified_files"]

    # Aggregate stats by file type
    pipeline = [
        {
            "$group": {
                "_id": "$file_type",
                "count": {"$sum": 1},
                "total_size": {"$sum": "$file_size"}
            }
        },
        {"$sort": {"count": -1}},
        {"$limit": 20}
    ]

    cursor = files_collection.aggregate(pipeline)
    file_types = []

    async for item in cursor:
        file_types.append({
            "file_type": item["_id"],
            "count": item["count"],
            "total_size_bytes": item["total_size"]
        })

    return {"file_types": file_types}


@router.get("/patterns")
async def list_detection_patterns(
    current_user: dict = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    List all available detection patterns
    """
    # Built-in detection patterns
    patterns = [
        {
            "id": "ssn",
            "name": "Social Security Number (SSN)",
            "description": "Detects US Social Security Numbers",
            "example": "123-45-6789",
            "enabled": True
        },
        {
            "id": "credit_card",
            "name": "Credit Card Number",
            "description": "Detects credit card numbers (Visa, MasterCard, Amex, etc.)",
            "example": "4111-1111-1111-1111",
            "enabled": True
        },
        {
            "id": "email",
            "name": "Email Address",
            "description": "Detects email addresses",
            "example": "user@example.com",
            "enabled": True
        },
        {
            "id": "phone",
            "name": "Phone Number",
            "description": "Detects phone numbers",
            "example": "+1-555-123-4567",
            "enabled": True
        },
        {
            "id": "api_key",
            "name": "API Key",
            "description": "Detects API keys and tokens",
            "example": "sk_live_...",
            "enabled": True
        },
        {
            "id": "password",
            "name": "Password Pattern",
            "description": "Detects password-like strings in code",
            "example": "password=...",
            "enabled": True
        },
        {
            "id": "private_key",
            "name": "Private Key",
            "description": "Detects RSA/SSH private keys",
            "example": "-----BEGIN PRIVATE KEY-----",
            "enabled": True
        },
        {
            "id": "internal",
            "name": "Internal Classification",
            "description": "Files marked as INTERNAL",
            "example": "INTERNAL",
            "enabled": True
        },
        {
            "id": "confidential",
            "name": "Confidential Classification",
            "description": "Files marked as CONFIDENTIAL",
            "example": "CONFIDENTIAL",
            "enabled": True
        },
        {
            "id": "restricted",
            "name": "Restricted Classification",
            "description": "Files marked as RESTRICTED/SECRET",
            "example": "RESTRICTED",
            "enabled": True
        },
    ]

    return {"patterns": patterns}
