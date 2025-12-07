from datetime import datetime
from typing import Optional, Dict, Any
from sqlmodel import Field, SQLModel, JSON, Column
from sqlalchemy import JSON as SQLJSON


class MLMetrics(SQLModel, table=True):
    __tablename__ = "ml_metrics"

    metric_id: Optional[int] = Field(default=None, primary_key=True)
    training_accuracy: float = Field(description="Training accuracy")
    test_accuracy: float = Field(description="Test accuracy")
    train_samples: int = Field(description="Number of training samples")
    test_samples: int = Field(description="Number of test samples")
    training_report: Dict[str, Any] = Field(
        sa_column=Column(SQLJSON),
        description="Detailed training classification report"
    )
    test_report: Dict[str, Any] = Field(
        sa_column=Column(SQLJSON),
        description="Detailed test classification report"
    )
    label_distribution: Dict[str, int] = Field(
        sa_column=Column(SQLJSON),
        default={},
        description="Distribution of predicted labels"
    )
    predicted_count: int = Field(default=0, description="Number of predictions made")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Metric timestamp")


class MLMetricsRead(SQLModel):
    metric_id: int
    training_accuracy: float
    test_accuracy: float
    train_samples: int
    test_samples: int
    training_report: Dict[str, Any]
    test_report: Dict[str, Any]
    label_distribution: Dict[str, int]
    predicted_count: int
    created_at: datetime

