"""
TechCare Bot - Learning Router
Case Library & Shared Learning
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from api.models import get_db, User, Case
from api.schemas import (
    CaseCreate,
    CaseResponse,
    CaseListResponse,
    CaseSearchRequest,
    CaseSearchResult
)
from api.services.auth_service import get_current_user
from api.config import settings

router = APIRouter()


@router.post("/cases", response_model=CaseResponse, status_code=status.HTTP_201_CREATED)
async def create_case(
    case_data: CaseCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create new case (save to learning library)

    Pro Business & Enterprise only (Shared Learning)
    """
    if not settings.shared_learning_enabled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Shared learning not available in this edition"
        )

    # Create case
    case = Case(
        problem_description=case_data.problem_description,
        problem_keywords=case_data.problem_keywords,
        root_cause=case_data.root_cause,
        os_type=case_data.os_type,
        os_version=case_data.os_version,
        solution_plan=case_data.solution_plan,
        solution_steps=case_data.solution_steps,
        tools_used=case_data.tools_used,
        success=case_data.success,
        execution_time_minutes=case_data.execution_time_minutes,
        complexity_score=case_data.complexity_score
    )

    db.add(case)
    await db.commit()
    await db.refresh(case)

    return CaseResponse.model_validate(case)


@router.get("/cases", response_model=CaseListResponse)
async def list_cases(
    page: int = 1,
    page_size: int = 20,
    os_type: str = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List cases"""
    offset = (page - 1) * page_size

    # Build query
    query = select(Case)
    count_query = select(func.count(Case.id))

    if os_type:
        query = query.where(Case.os_type == os_type)
        count_query = count_query.where(Case.os_type == os_type)

    # Count total
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # Get cases
    query = query.order_by(Case.reuse_count.desc()).offset(offset).limit(page_size)
    result = await db.execute(query)
    cases = result.scalars().all()

    return CaseListResponse(
        cases=[CaseResponse.model_validate(case) for case in cases],
        total=total,
        page=page,
        page_size=page_size
    )


@router.post("/cases/search", response_model=List[CaseSearchResult])
async def search_cases(
    search_request: CaseSearchRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Search similar cases

    Uses keyword matching (simplified)
    In production: Use pgvector for semantic search
    """
    # Extract keywords from problem description (simplified)
    keywords = search_request.problem_description.lower().split()

    # Build query
    query = select(Case)

    if search_request.os_type:
        query = query.where(Case.os_type == search_request.os_type)

    # Filter by keywords (ANY match)
    # In production: Use pgvector similarity search
    query = query.where(
        Case.problem_keywords.overlap(keywords)
    )

    query = query.order_by(Case.success_rate.desc()).limit(search_request.limit)

    result = await db.execute(query)
    cases = result.scalars().all()

    # Calculate similarity (simplified - just keyword overlap)
    results = []
    for case in cases:
        overlap = len(set(keywords) & set(case.problem_keywords))
        similarity = overlap / max(len(keywords), len(case.problem_keywords))

        results.append(
            CaseSearchResult(
                case=CaseResponse.model_validate(case),
                similarity=similarity
            )
        )

    # Sort by similarity
    results.sort(key=lambda x: x.similarity, reverse=True)

    return results


@router.get("/cases/{case_id}", response_model=CaseResponse)
async def get_case(
    case_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get case by ID"""
    result = await db.execute(
        select(Case).where(Case.id == case_id)
    )
    case = result.scalar_one_or_none()

    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found"
        )

    return CaseResponse.model_validate(case)


@router.post("/cases/{case_id}/reuse")
async def mark_case_reused(
    case_id: str,
    success: bool,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Mark case as reused (increment counter)"""
    result = await db.execute(
        select(Case).where(Case.id == case_id)
    )
    case = result.scalar_one_or_none()

    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found"
        )

    case.increment_reuse(success)
    await db.commit()

    return {"message": "Case reuse tracked"}
