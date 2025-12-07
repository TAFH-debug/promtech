from typing import List
from fastapi import APIRouter, Depends
from sqlmodel import Session, select, desc

from app.api.deps import get_db
from app.models.ml_metrics import MLMetrics, MLMetricsRead

router = APIRouter()


@router.get("/metrics", response_model=List[dict])
def get_ml_metrics(
    limit: int = 10,
    db: Session = Depends(get_db),
):
    """Get ML training metrics history"""
    metrics = db.exec(
        select(MLMetrics)
        .order_by(desc(MLMetrics.created_at))
        .limit(limit)
    ).all()
    
    return [
        {
            "metric_id": m.metric_id,
            "training_accuracy": m.training_accuracy,
            "test_accuracy": m.test_accuracy,
            "train_samples": m.train_samples,
            "test_samples": m.test_samples,
            "training_report": m.training_report,
            "test_report": m.test_report,
            "label_distribution": m.label_distribution,
            "predicted_count": m.predicted_count,
            "created_at": m.created_at.isoformat(),
        }
        for m in metrics
    ]


@router.get("/metrics/latest", response_model=dict)
def get_latest_ml_metrics(db: Session = Depends(get_db)):
    """Get the latest ML training metrics"""
    latest = db.exec(
        select(MLMetrics)
        .order_by(desc(MLMetrics.created_at))
        .limit(1)
    ).first()
    
    if not latest:
        return {
            "error": "No metrics found",
            "training_accuracy": 0.0,
            "test_accuracy": 0.0,
            "train_samples": 0,
            "test_samples": 0,
        }
    
    return {
        "metric_id": latest.metric_id,
        "training_accuracy": latest.training_accuracy,
        "test_accuracy": latest.test_accuracy,
        "train_samples": latest.train_samples,
        "test_samples": latest.test_samples,
        "training_report": latest.training_report,
        "test_report": latest.test_report,
        "label_distribution": latest.label_distribution,
        "predicted_count": latest.predicted_count,
        "created_at": latest.created_at.isoformat(),
    }

