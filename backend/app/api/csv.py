from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, UploadFile

router = APIRouter()

@router.post("/import/")
async def csv_import_validation(file: UploadFile):
    new_filename = uuid4().hex + "_" + file.filename
    with open(new_filename, "wb") as buffer:
        buffer.write(await file.read())
    return {"filename": new_filename}

async def validate_csv(file_path: str) -> bool:
    try:
        pass
    except:
        return False