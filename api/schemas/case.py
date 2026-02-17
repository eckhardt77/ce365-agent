"""
CE365 Agent - Case Schemas (Learning System)
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime


class CaseBase(BaseModel):
    """Base Case Schema"""
    problem_description: str = Field(..., min_length=10)
    root_cause: str = Field(..., min_length=10)
    os_type: str = Field(..., pattern="^(windows|macos|linux)$")
    os_version: Optional[str] = None
    solution_plan: str = Field(..., min_length=10)
    solution_steps: List[Dict[str, Any]]
    tools_used: List[str]


class CaseCreate(CaseBase):
    """Case Creation Schema"""
    problem_keywords: List[str] = Field(..., min_items=1, max_items=20)
    success: bool = True
    execution_time_minutes: Optional[int] = None
    complexity_score: Optional[float] = Field(None, ge=0.0, le=1.0)


class CaseResponse(CaseBase):
    """Case Response Schema"""
    id: str
    problem_keywords: List[str]
    success: bool
    execution_time_minutes: Optional[int]
    complexity_score: Optional[float]
    reuse_count: int
    success_count: int
    success_rate: float
    created_at: datetime
    last_reused_at: Optional[datetime]

    class Config:
        from_attributes = True


class CaseSearchRequest(BaseModel):
    """Case Search Request"""
    problem_description: str = Field(..., min_length=10)
    os_type: Optional[str] = Field(None, pattern="^(windows|macos|linux)$")
    limit: int = Field(default=5, ge=1, le=20)


class CaseSearchResult(BaseModel):
    """Case Search Result (mit Similarity Score)"""
    case: CaseResponse
    similarity: float = Field(..., ge=0.0, le=1.0)


class CaseListResponse(BaseModel):
    """Case List Response"""
    cases: List[CaseResponse]
    total: int
    page: int
    page_size: int
