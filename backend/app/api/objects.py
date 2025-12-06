from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select
from app.api.deps import get_db
from app.models.object import Object, ObjectCreate, ObjectUpdate, ObjectRead, ObjectType

router = APIRouter()


@router.get("/", response_model=List[ObjectRead])
def read_objects(
    skip: int = 0,
    limit: int = 100,
    object_type: Optional[ObjectType] = Query(None, description="Filter by object type"),
    pipeline_id: Optional[str] = Query(None, description="Filter by pipeline ID"),
    db: Session = Depends(get_db),
):
    """Get all objects with optional filters"""
    statement = select(Object)
    
    if object_type:
        statement = statement.where(Object.object_type == object_type)
    if pipeline_id:
        statement = statement.where(Object.pipeline_id == pipeline_id)
    
    statement = statement.offset(skip).limit(limit)
    objects = db.exec(statement).all()
    return objects


@router.get("/{object_id}", response_model=ObjectRead)
def read_object(
    object_id: int,
    db: Session = Depends(get_db),
):
    """Get a specific object by ID"""
    obj = db.get(Object, object_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Object not found")
    return obj


@router.post("/", response_model=ObjectRead, status_code=201)
def create_object(
    obj: ObjectCreate,
    db: Session = Depends(get_db),
):
    """Create a new object"""
    db_obj = Object(**obj.model_dump())
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


@router.post("/bulk", response_model=List[ObjectRead], status_code=201)
def create_objects_bulk(
    objects: List[ObjectCreate],
    db: Session = Depends(get_db),
):
    """Create multiple objects at once (for CSV import)"""
    db_objects = []
    for obj_data in objects:
        db_obj = Object(**obj_data.model_dump())
        db.add(db_obj)
        db_objects.append(db_obj)
    
    db.commit()
    for db_obj in db_objects:
        db.refresh(db_obj)
    
    return db_objects


@router.put("/{object_id}", response_model=ObjectRead)
def update_object(
    object_id: int,
    object_update: ObjectUpdate,
    db: Session = Depends(get_db),
):
    """Update an object"""
    db_obj = db.get(Object, object_id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="Object not found")
    
    object_data = object_update.model_dump(exclude_unset=True)
    for field, value in object_data.items():
        setattr(db_obj, field, value)
    
    from datetime import datetime
    db_obj.updated_at = datetime.utcnow()
    
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


@router.delete("/{object_id}", status_code=204)
def delete_object(
    object_id: int,
    db: Session = Depends(get_db),
):
    """Delete an object"""
    db_obj = db.get(Object, object_id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="Object not found")
    
    db.delete(db_obj)
    db.commit()
    return None

