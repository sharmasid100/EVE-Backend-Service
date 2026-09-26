from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import get_current_user
from app.models import User
from app.schemas import (
    CentreCreate,
    CentreDetailOut,
    CentreOut,
    PaginatedCentres,
    PaginatedTests,
    TestCreate,
    TestOut,
)
from app.services import centre_service

router = APIRouter(prefix="/centres", tags=["centres"])


@router.get("", response_model=PaginatedCentres)
def list_centres(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> PaginatedCentres:
    return centre_service.list_centres(db, limit, offset)


@router.post("", response_model=CentreOut, status_code=status.HTTP_201_CREATED)
def create_centre(
    payload: CentreCreate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> CentreOut:
    return centre_service.create_centre(db, payload)


@router.get("/{centre_id}", response_model=CentreDetailOut)
def get_centre(
    centre_id: UUID,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> CentreDetailOut:
    return centre_service.get_centre(db, centre_id)


@router.get("/{centre_id}/tests", response_model=PaginatedTests)
def list_tests(
    centre_id: UUID,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> PaginatedTests:
    return centre_service.list_tests(db, centre_id, limit, offset)


@router.post("/{centre_id}/tests", response_model=TestOut, status_code=status.HTTP_201_CREATED)
def create_test(
    centre_id: UUID,
    payload: TestCreate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> TestOut:
    return centre_service.create_test(db, centre_id, payload)
