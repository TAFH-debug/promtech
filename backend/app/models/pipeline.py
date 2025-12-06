from typing import List, Optional, TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.object import Object


class Pipeline(SQLModel, table=True):
    __tablename__ = "pipelines"

    pipeline_id: str = Field(primary_key=True, description="Unique pipeline identifier")
    description: Optional[str] = Field(default=None, description="Pipeline description")

    objects: List["Object"] = Relationship(back_populates="pipeline")
