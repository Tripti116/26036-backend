from sqlalchemy.orm import Session
from database import SessionLocal
from models.user import User, UserRole
from models.instrument import Instrument
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def seed():
    db: Session = SessionLocal()

    try:
        users = [
            {
                "full_name": "Admin User",
                "email": "admin@sih.com",
                "phone": "1111111111",
                "password": "admin123",
                "role": UserRole.ADMIN,
                "organization": "SIH Org",
                "address": "HQ",
            },
            {
                "full_name": "Inspector User",
                "email": "inspector@sih.com",
                "phone": "2222222222",
                "password": "inspector123",
                "role": UserRole.INSPECTOR,
                "organization": "Inspection Dept",
                "address": "Branch Office",
            },
            {
                "full_name": "Owner User",
                "email": "owner@sih.com",
                "phone": "3333333333",
                "password": "owner123",
                "role": UserRole.OWNER,
                "organization": "Owner Org",
                "address": "Owner Address",
            },
        ]

        for u in users:
            existing = db.query(User).filter(User.email == u["email"]).first()
            if not existing:
                db.add(
                    User(
                        full_name=u["full_name"],
                        email=u["email"],
                        phone=u["phone"],
                        hashed_password=pwd_context.hash(u["password"][:72]),
                        role=u["role"],
                        organization=u["organization"],
                        address=u["address"],
                    )
                )

        db.commit()

        owner = db.query(User).filter(User.role == UserRole.OWNER).first()
        if owner:
            inst = (
                db.query(Instrument)
                .filter(Instrument.instrument_id == "INST-001")
                .first()
            )
            if not inst:
                db.add(
                    Instrument(
                        instrument_id="INST-001",
                        owner_id=owner.id,
                        instrument_type="Weighing Scale",
                        manufacturer="Demo Manufacturer",
                        model_number="M123",
                        serial_number="SN123456",
                        capacity="100kg",
                        accuracy_class="Class II",
                        location="Delhi",
                    )
                )
        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    seed()
    print("Seed data inserted successfully!")
