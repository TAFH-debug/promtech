# PromTech Backend

FastAPI backend with SQLModel, Alembic, and PostgreSQL.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Create `.env` file from `.env.example`:
```bash
cp .env.example .env
```

3. Update `.env` with your PostgreSQL connection string:
```
DATABASE_URL=postgresql://user:password@localhost:5432/promtech_db
```

4. Create PostgreSQL database:
```sql
CREATE DATABASE promtech_db;
```

5. Create initial migration (first time only):
```bash
alembic revision --autogenerate -m "Initial migration"
```

6. Run migrations:
```bash
alembic upgrade head
```

Or use the script:
```bash
# Windows
scripts\init_db.bat

# Linux/Mac
chmod +x scripts/init_db.sh
./scripts/init_db.sh
```

7. Run the server:
```bash
# Using uvicorn directly
uvicorn main:app --reload

# Or using the run script
python run.py
```

## API Documentation

Once the server is running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API Endpoints

### Points
- `GET /api/v1/points/` - Get all points
- `GET /api/v1/points/{id}` - Get a specific point
- `POST /api/v1/points/` - Create a new point
- `PUT /api/v1/points/{id}` - Update a point
- `DELETE /api/v1/points/{id}` - Delete a point

### Lines
- `GET /api/v1/lines/` - Get all lines
- `GET /api/v1/lines/{id}` - Get a specific line
- `POST /api/v1/lines/` - Create a new line
- `PUT /api/v1/lines/{id}` - Update a line
- `DELETE /api/v1/lines/{id}` - Delete a line

### Objects
- `GET /api/v1/objects/` - Get all objects (with optional filters: `object_type`, `pipeline_id`)
- `GET /api/v1/objects/{object_id}` - Get a specific object
- `POST /api/v1/objects/` - Create a new object
- `POST /api/v1/objects/bulk` - Create multiple objects at once (for CSV import)
- `PUT /api/v1/objects/{object_id}` - Update an object
- `DELETE /api/v1/objects/{object_id}` - Delete an object

### Diagnostics
- `GET /api/v1/diagnostics/` - Get all diagnostics (with optional filters: `object_id`, `method`, `quality_grade`, `defect_found`)
- `GET /api/v1/diagnostics/{diag_id}` - Get a specific diagnostic
- `POST /api/v1/diagnostics/` - Create a new diagnostic
- `POST /api/v1/diagnostics/bulk` - Create multiple diagnostics at once (for CSV import)
- `PUT /api/v1/diagnostics/{diag_id}` - Update a diagnostic
- `DELETE /api/v1/diagnostics/{diag_id}` - Delete a diagnostic
- `GET /api/v1/diagnostics/object/{object_id}/history` - Get diagnostics history for a specific object

### Models

#### Object Model
The Object model corresponds to the Objects.csv structure:
- `object_id` (int) - Object identifier
- `object_name` (string) - Name of equipment or pipeline section
- `object_type` (enum) - Type: `crane`, `compressor`, or `pipeline section`
- `pipeline_id` (string, optional) - Pipeline identifier
- `lat` (float) - Latitude
- `lon` (float) - Longitude
- `year` (int, optional) - Year of manufacture/commissioning
- `material` (string, optional) - Material brand

#### Diagnostic Model
The Diagnostic model corresponds to the Diagnostics.csv structure:
- `diag_id` (int) - Diagnostic record identifier
- `object_id` (int) - Reference to object
- `method` (enum) - Inspection method: `VIK`, `PVK`, `MPK`, `UZK`, `RGK`, `TVK`, `VIBRO`, `MFL`, `TFI`, `GEO`, `UTWM`
- `date` (date) - Date of inspection
- `temperature` (float, optional) - Air temperature
- `humidity` (float, optional) - Humidity
- `illumination` (float, optional) - Illumination
- `defect_found` (bool) - Defect flag
- `defect_description` (string, optional) - Defect description
- `quality_grade` (enum, optional) - Quality assessment: `удовлетворительно`, `допустимо`, `требует мер`, `недопустимо`
- `param1`, `param2`, `param3` (float, optional) - Parameters (depth, vibration velocity, thickness, etc.)
- `ml_label` (enum, optional) - ML target class: `normal`, `medium`, `high`

## Project Structure

```
backend/
├── alembic/          # Alembic migrations
├── app/
│   ├── api/          # API routes
│   │   └── v1/      # API version 1
│   ├── core/         # Core configuration
│   └── models/          # SQLModel models
│       ├── object.py    # Object model (Objects.csv)
│       └── diagnostic.py # Diagnostic model (Diagnostics.csv)
├── main.py           # FastAPI application
└── requirements.txt  # Python dependencies

