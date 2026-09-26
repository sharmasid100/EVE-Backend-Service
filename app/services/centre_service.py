from uuid import UUID

from sqlalchemy.orm import Session, joinedload

from app.core.exceptions import not_found
from app.models import DiagnosticCentre, DiagnosticTest
from app.schemas import (
    CentreCreate,
    CentreDetailOut,
    CentreOut,
    PaginatedCentres,
    PaginatedTests,
    TestCreate,
    TestOut,
)


def create_centre(db: Session, payload: CentreCreate) -> CentreOut:
    centre = DiagnosticCentre(name=payload.name, location=payload.location)
    db.add(centre)
    db.commit()
    db.refresh(centre)
    return CentreOut.model_validate(centre)


def list_centres(db: Session, limit: int, offset: int) -> PaginatedCentres:
    query = db.query(DiagnosticCentre)
    total = query.count()
    items = query.order_by(DiagnosticCentre.created_at.desc()).offset(offset).limit(limit).all()
    return PaginatedCentres(
        items=[CentreOut.model_validate(c) for c in items],
        total=total,
        limit=limit,
        offset=offset,
    )


def get_centre(db: Session, centre_id: UUID) -> CentreDetailOut:
    centre = (
        db.query(DiagnosticCentre)
        .options(joinedload(DiagnosticCentre.tests))
        .filter(DiagnosticCentre.id == centre_id)
        .first()
    )
    if centre is None:
        raise not_found("Diagnostic centre not found")
    return CentreDetailOut(
        id=centre.id,
        name=centre.name,
        location=centre.location,
        created_at=centre.created_at,
        tests=[TestOut.model_validate(t) for t in centre.tests],
    )


def create_test(db: Session, centre_id: UUID, payload: TestCreate) -> TestOut:
    centre = db.get(DiagnosticCentre, centre_id)
    if centre is None:
        raise not_found("Diagnostic centre not found")
    test = DiagnosticTest(centre_id=centre_id, name=payload.name, price=payload.price)
    db.add(test)
    db.commit()
    db.refresh(test)
    return TestOut.model_validate(test)


def list_tests(db: Session, centre_id: UUID, limit: int, offset: int) -> PaginatedTests:
    centre = db.get(DiagnosticCentre, centre_id)
    if centre is None:
        raise not_found("Diagnostic centre not found")
    query = db.query(DiagnosticTest).filter(DiagnosticTest.centre_id == centre_id)
    total = query.count()
    items = query.order_by(DiagnosticTest.created_at.desc()).offset(offset).limit(limit).all()
    return PaginatedTests(
        items=[TestOut.model_validate(t) for t in items],
        total=total,
        limit=limit,
        offset=offset,
    )
