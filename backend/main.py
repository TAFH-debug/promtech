import os
import io
import json
import pandas as pd
from contextlib import asynccontextmanager
from typing import AsyncGenerator
import asyncpg
from fastapi import FastAPI, HTTPException, Request, Depends, File, UploadFile
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
ALLOWED_EXTENSIONS = {"csv", "xlsx"}
MAX_UPLOAD_BYTES = 5 * 1024 * 1024

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Connecting to DB...")
    pool = await asyncpg.create_pool(
        dsn=DATABASE_URL,
        min_size=1,
        max_size=10
    )
    app.state.db_pool = pool
    
    async with pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS objects (
                object_id INTEGER PRIMARY KEY,
                object_name TEXT,
                object_type TEXT,
                pipeline_id TEXT,
                lat FLOAT,
                lon FLOAT,
                year INTEGER,
                material TEXT
            );
        """)
        
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS diagnostics (
                diag_id INTEGER PRIMARY KEY,
                object_id INTEGER REFERENCES objects(object_id),
                method TEXT,
                date DATE,
                temperature FLOAT,
                defect_found INTEGER,
                defect_type TEXT,
                depth FLOAT,
                length FLOAT,
                width FLOAT
            );
        """)

    yield
    print("Closing DB connection...")
    await pool.close()

app = FastAPI(lifespan=lifespan)
async def get_connection(request: Request) -> AsyncGenerator[asyncpg.Connection, None]:
    pool: asyncpg.Pool = request.app.state.db_pool
    async with pool.acquire() as connection:
        yield connection

@app.get("/")
async def read_root():
    return {"status": "ok"}

@app.get("/db-health")
async def db_health(conn: asyncpg.Connection = Depends(get_connection)) -> dict:
    try:
        result = await conn.fetchval("SELECT 1;")
        return {"db": "ok", "result": result}
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Database error") from exc

@app.post("/upload-file")
async def upload_file(
    file: UploadFile = File(...), 
    conn: asyncpg.Connection = Depends(get_connection) 
) -> dict:
    
    try:
        if ext == "csv":
            try:
                df = pd.read_csv(io.BytesIO(content)) 
            except UnicodeDecodeError:
                df = pd.read_csv(io.BytesIO(content), encoding="cp1251", sep=None, engine='python')
        else:
            df = pd.read_excel(io.BytesIO(content))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not parse file: {str(e)}")

    df.columns = [c.lower().strip() for c in df.columns]
    columns_set = set(df.columns)

    if {"object_id", "lat", "lon"}.issubset(columns_set):
        file_type = "objects"
    elif {"diag_id", "method"}.issubset(columns_set):
        file_type = "diagnostics"
    else:
        raise HTTPException(status_code=400, detail="Unknown file format")

    records = df.where(pd.notnull(df), None).to_dict('records')
    
    try:
        if file_type == "objects":
            await conn.executemany("""
                INSERT INTO objects (object_id, object_name, object_type, pipeline_id, lat, lon, year, material)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                ON CONFLICT (object_id) DO UPDATE 
                SET object_name=$2, lat=$5, lon=$6;
            """, [
                (r['object_id'], r.get('object_name'), r.get('object_type'), r.get('pipeline_id'), 
                 r['lat'], r['lon'], r.get('year'), r.get('material'))
                for r in records
            ])
            
        elif file_type == "diagnostics":
            await conn.executemany("""
                INSERT INTO diagnostics (diag_id, object_id, method, date, temperature, defect_found, defect_type, depth, length, width)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                ON CONFLICT (diag_id) DO NOTHING;
            """, [
                (r['diag_id'], r['object_id'], r['method'], r.get('date'), r.get('temperature'), 
                 r.get('defect_found'), r.get('defect_type'), r.get('depth'), r.get('length'), r.get('width'))
                for r in records
            ])
            
    except Exception as e:
        print(f"DB Error: {e}")
        raise HTTPException(status_code=500, detail=f"Database save error: {e}")

    return {
        "filename": filename,
        "file_type": file_type,
        "status": "success",
        "rows_inserted": len(records), 
        "preview": records[:5] 

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
