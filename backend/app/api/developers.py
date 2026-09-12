from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.developer import Developer
from app.schemas.schemas import DeveloperCreate, DeveloperOut, DeveloperUpdate

router = APIRouter(prefix="/api/developers", tags=["developers"])


@router.get("/", response_model=list[DeveloperOut])
def list_developers(db: Session = Depends(get_db)):
    return db.query(Developer).order_by(Developer.name).all()


@router.post("/", response_model=DeveloperOut)
def create_developer(payload: DeveloperCreate, db: Session = Depends(get_db)):
    existing = db.query(Developer).filter_by(name=payload.name.strip()).first()
    if existing:
        raise HTTPException(status_code=409, detail=f"Developer '{payload.name}' already exists.")
    dev = Developer(name=payload.name.strip(), is_active=payload.is_active)
    db.add(dev)
    db.commit()
    db.refresh(dev)
    return dev


@router.put("/{dev_id}", response_model=DeveloperOut)
def update_developer(dev_id: int, payload: DeveloperUpdate, db: Session = Depends(get_db)):
    dev = db.query(Developer).filter(Developer.id == dev_id).first()
    if not dev:
        raise HTTPException(status_code=404, detail="Developer not found.")
    if payload.name is not None:
        dev.name = payload.name.strip()
    if payload.is_active is not None:
        dev.is_active = payload.is_active
    db.commit()
    db.refresh(dev)
    return dev


@router.delete("/{dev_id}")
def delete_developer(dev_id: int, db: Session = Depends(get_db)):
    dev = db.query(Developer).filter(Developer.id == dev_id).first()
    if not dev:
        raise HTTPException(status_code=404, detail="Developer not found.")
    db.delete(dev)
    db.commit()
    return {"message": f"Developer '{dev.name}' deleted."}
