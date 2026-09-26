"""Seed sample diagnostic centres and tests.

Usage (inside eve folder, with DATABASE_URL set):
    python -m scripts.seed
"""

from decimal import Decimal

from app.db import SessionLocal
from app.models import DiagnosticCentre, DiagnosticTest


def seed() -> None:
    db = SessionLocal()
    try:
        if db.query(DiagnosticCentre).count() > 0:
            print("Seed skipped: centres already exist")
            return

        centres = [
            DiagnosticCentre(name="EVE Labs Downtown", location="Bangalore, MG Road"),
            DiagnosticCentre(name="EVE Labs North", location="Delhi, Connaught Place"),
        ]
        db.add_all(centres)
        db.flush()

        tests = [
            DiagnosticTest(centre_id=centres[0].id, name="Complete Blood Count", price=Decimal("499.00")),
            DiagnosticTest(centre_id=centres[0].id, name="Lipid Profile", price=Decimal("799.00")),
            DiagnosticTest(centre_id=centres[1].id, name="Thyroid Panel", price=Decimal("699.00")),
            DiagnosticTest(centre_id=centres[1].id, name="HbA1c", price=Decimal("450.00")),
        ]
        db.add_all(tests)
        db.commit()
        print(f"Seeded {len(centres)} centres and {len(tests)} tests")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
