from datetime import datetime
from typing import Optional
from sqlmodel import Field, SQLModel


class FileImport(SQLModel, table=True):
    __tablename__ = "file_imports"

    import_id: Optional[int] = Field(default=None, primary_key=True)
    filename: str = Field(description="Original filename")
    file_type: str = Field(description="Type of file: objects or diagnostics")
    file_size: Optional[int] = Field(default=None, description="File size in bytes")
    created: int = Field(default=0, description="Number of records created")
    updated: int = Field(default=0, description="Number of records updated")
    defects_created: int = Field(default=0, description="Number of defects created")
    error_count: int = Field(default=0, description="Number of errors during import")
    imported_at: datetime = Field(default_factory=datetime.utcnow, description="Import timestamp")


class FileImportRead(SQLModel):
    import_id: int
    filename: str
    file_type: str
    file_size: Optional[int]
    created: int
    updated: int
    defects_created: int
    error_count: int
    imported_at: datetime

