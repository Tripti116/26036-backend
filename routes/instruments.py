from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional

from database import get_db
from models.instrument import Instrument, InstrumentStatus
from models.user import User, UserRole
from schemas.instrument import InstrumentCreate, InstrumentOut, InstrumentUpdate
from routes.auth import get_current_user, require_role

router = APIRouter(prefix="/api/instruments", tags=["Instruments"])


@router.post("/", response_model=InstrumentOut)
def create_instrument(
    instrument: InstrumentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.OWNER)),
):
    duplicate = db.query(Instrument).filter(
        (Instrument.instrument_id == instrument.instrument_id)
        | (Instrument.serial_number == instrument.serial_number)
    ).first()
    if duplicate:
        raise HTTPException(status_code=409, detail="Instrument with this ID or serial number already exists")

    new_inst = Instrument(**instrument.model_dump(), owner_id=current_user.id)
    db.add(new_inst)
    db.commit()
    db.refresh(new_inst)
    return new_inst


@router.get("/", response_model=list[InstrumentOut])
def list_instruments(
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Instrument)
    if current_user.role == UserRole.OWNER:
        query = query.filter(Instrument.owner_id == current_user.id)
    elif current_user.role == UserRole.INSPECTOR:
        pass
    elif current_user.role == UserRole.ADMIN:
        pass
    else:
        raise HTTPException(status_code=403, detail="Not authorized")

    if status:
        query = query.filter(Instrument.status == status)

    return query.order_by(Instrument.created_at.desc()).all()


@router.get("/{instrument_db_id}", response_model=InstrumentOut)
def get_instrument(
    instrument_db_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    instrument = db.query(Instrument).filter(Instrument.id == instrument_db_id).first()
    if not instrument:
        raise HTTPException(status_code=404, detail="Instrument not found")

    if current_user.role == UserRole.OWNER and instrument.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to view this instrument")

    return instrument


@router.put("/{instrument_db_id}", response_model=InstrumentOut)
def update_instrument(
    instrument_db_id: int,
    update_data: InstrumentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    instrument = db.query(Instrument).filter(Instrument.id == instrument_db_id).first()
    if not instrument:
        raise HTTPException(status_code=404, detail="Instrument not found")

    if current_user.role == UserRole.OWNER and instrument.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this instrument")

    if current_user.role == UserRole.INSPECTOR:
        raise HTTPException(status_code=403, detail="Inspectors cannot update instruments")

    for field, value in update_data.model_dump(exclude_unset=True).items():
        setattr(instrument, field, value)

    db.commit()
    db.refresh(instrument)
    return instrument


@router.delete("/{instrument_db_id}")
def delete_instrument(
    instrument_db_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN, UserRole.OWNER)),
):
    instrument = db.query(Instrument).filter(Instrument.id == instrument_db_id).first()
    if not instrument:
        raise HTTPException(status_code=404, detail="Instrument not found")

    if current_user.role == UserRole.OWNER and instrument.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this instrument")

    db.delete(instrument)
    db.commit()
    return {"detail": "Instrument deleted successfully"}
