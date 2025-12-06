from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select
from app.api.deps import get_db
from app.models.diagnostic import (
    Diagnostic,
    DiagnosticCreate,
    DiagnosticUpdate,
    DiagnosticRead,
    DiagnosticMethod,
    QualityGrade,
    MLLabel,
)

router = APIRouter()


@router.get("/", response_model=List[DiagnosticRead])
def read_diagnostics(
    skip: int = 0,
    limit: int = 100,
    object_id: Optional[int] = Query(None, description="Filter by object ID"),
    method: Optional[DiagnosticMethod] = Query(None, description="Filter by method"),
    quality_grade: Optional[QualityGrade] = Query(None, description="Filter by quality grade"),
    defect_found: Optional[bool] = Query(None, description="Filter by defect found"),
    db: Session = Depends(get_db),
):
    """Get all diagnostics with optional filters"""
    statement = select(Diagnostic)
    
    if object_id:
        statement = statement.where(Diagnostic.object_id == object_id)
    if method:
        statement = statement.where(Diagnostic.method == method)
    if quality_grade:
        statement = statement.where(Diagnostic.quality_grade == quality_grade)
    if defect_found is not None:
        statement = statement.where(Diagnostic.defect_found == defect_found)
    
    statement = statement.order_by(Diagnostic.date.desc()).offset(skip).limit(limit)
    diagnostics = db.exec(statement).all()
    return diagnostics


@router.get("/{diag_id}", response_model=DiagnosticRead)
def read_diagnostic(
    diag_id: int,
    db: Session = Depends(get_db),
):
    """Get a specific diagnostic by ID"""
    diagnostic = db.get(Diagnostic, diag_id)
    if not diagnostic:
        raise HTTPException(status_code=404, detail="Diagnostic not found")
    return diagnostic


@router.post("/", response_model=DiagnosticRead, status_code=201)
def create_diagnostic(
    diagnostic: DiagnosticCreate,
    db: Session = Depends(get_db),
):
    """Create a new diagnostic"""
    # Verify object exists
    from app.models.object import Object
    obj = db.get(Object, diagnostic.object_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Object not found")
    
    db_diagnostic = Diagnostic(**diagnostic.model_dump())
    db.add(db_diagnostic)
    db.commit()
    db.refresh(db_diagnostic)
    return db_diagnostic


@router.post("/bulk", response_model=List[DiagnosticRead], status_code=201)
def create_diagnostics_bulk(
    diagnostics: List[DiagnosticCreate],
    db: Session = Depends(get_db),
):
    """Create multiple diagnostics at once (for CSV import)"""
    from app.models.object import Object
    
    db_diagnostics = []
    for diag_data in diagnostics:
        # Verify object exists
        obj = db.get(Object, diag_data.object_id)
        if not obj:
            continue  # Skip invalid object_id
        
        db_diag = Diagnostic(**diag_data.model_dump())
        db.add(db_diag)
        db_diagnostics.append(db_diag)
    
    db.commit()
    for db_diag in db_diagnostics:
        db.refresh(db_diag)
    
    return db_diagnostics


@router.put("/{diag_id}", response_model=DiagnosticRead)
def update_diagnostic(
    diag_id: int,
    diagnostic_update: DiagnosticUpdate,
    db: Session = Depends(get_db),
):
    """Update a diagnostic"""
    db_diagnostic = db.get(Diagnostic, diag_id)
    if not db_diagnostic:
        raise HTTPException(status_code=404, detail="Diagnostic not found")
    
    # Verify object exists if object_id is being updated
    if diagnostic_update.object_id is not None:
        from app.models.object import Object
        obj = db.get(Object, diagnostic_update.object_id)
        if not obj:
            raise HTTPException(status_code=404, detail="Object not found")
    
    diagnostic_data = diagnostic_update.model_dump(exclude_unset=True)
    for field, value in diagnostic_data.items():
        setattr(db_diagnostic, field, value)
    
    from datetime import datetime
    db_diagnostic.updated_at = datetime.utcnow()
    
    db.add(db_diagnostic)
    db.commit()
    db.refresh(db_diagnostic)
    return db_diagnostic


@router.delete("/{diag_id}", status_code=204)
def delete_diagnostic(
    diag_id: int,
    db: Session = Depends(get_db),
):
    """Delete a diagnostic"""
    db_diagnostic = db.get(Diagnostic, diag_id)
    if not db_diagnostic:
        raise HTTPException(status_code=404, detail="Diagnostic not found")
    
    db.delete(db_diagnostic)
    db.commit()
    return None


@router.get("/object/{object_id}/history", response_model=List[DiagnosticRead])
def get_object_diagnostics_history(
    object_id: int,
    db: Session = Depends(get_db),
):
    """Get diagnostics history for a specific object"""
    from app.models.object import Object
    
    obj = db.get(Object, object_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Object not found")
    
    statement = select(Diagnostic).where(
        Diagnostic.object_id == object_id
    ).order_by(Diagnostic.date.desc())
    
    diagnostics = db.exec(statement).all()
    return diagnostics

