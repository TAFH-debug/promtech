from fastapi import APIRouter
from . import csv
from . import objects
from . import map
from . import dashboard

api_router = APIRouter()
api_router.include_router(csv.router, prefix="/csv", tags=["csv"])
api_router.include_router(objects.router, prefix="/objects", tags=["objects"])
api_router.include_router(map.router, tags=["map"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
