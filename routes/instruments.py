from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models.instrument import Instrument, InstrumentStatus
from models.user import UserRole
from schemas.instrument import InstrumentCreate, InstrumentOut
from routes.auth import get_current_user

router = APIRouter(prefix="/api/instruments", tags=["instruments"])

@router.post("/", response_model=InstrumentOut)
def create_instrument(instrument: InstrumentCreate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    if current_user.role != UserRole.OWNER:
        raise HTTPException(status_code=403, detail="Only owners can register instruments")
    duplicate = db.query(Instrument).filter(
        (Instrument.instrument_id == instrument.instrument_id) |
        (Instrument.serial_number == instrument.serial_number)
    ).first()
    if duplicate:
        raise HTTPException(status_code=409, detail="Instrument already exists")
    new_inst = Instrument(**instrument.dict(), owner_id=current_user.id)
    db.add(new_inst)
    db.commit()
    db.refresh(new_inst)
    return new_inst

@router.get("/", response_model=list[InstrumentOut])
def list_instruments(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    if current_user.role == UserRole.ADMIN:
        return db.query(Instrument).all()
    elif current_user.role == UserRole.OWNER:
        return db.query(Instrument).filter(Instrument.owner_id == current_user.id).all()
    elif current_user.role == UserRole.INSPECTOR:
        return db.query(Instrument).all()
    else:
        raise HTTPException(status_code=403, detail="Not authorized")
