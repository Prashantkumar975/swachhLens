from pathlib import Path
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

from . import config
from .database import init_db
from .routes import analyze, admin_tasks, auth, community, constants, gis, reports

# Initialize FastAPI app
app = FastAPI(title="SwachLens API", version="1.0.0")

# Healthcheck route for Railway
@app.get("/health")
def health():
    return {"status": "OK"}

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.FRONTEND_ORIGINS + ["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# API routes
app.include_router(auth.router, prefix="/api")
app.include_router(reports.router, prefix="/api")
app.include_router(constants.router, prefix="/api")
app.include_router(analyze.router, prefix="/api")
app.include_router(gis.router, prefix="/api")
app.include_router(community.router, prefix="/api")
app.include_router(admin_tasks.router, prefix="/api")

# Serve static frontend files
@app.get("/{filename}.html")
async def serve_html(filename: str):
    file_path = config.STATIC_DIR / f"{filename}.html"
    if file_path.is_file():
        return FileResponse(file_path)
    raise HTTPException(status_code=404, detail="Page not found")

@app.get("/")
async def serve_index():
    return FileResponse(config.STATIC_DIR / "index.html")

# Mount css/ and js/ directories
app.mount("/css", StaticFiles(directory=str(config.STATIC_DIR / "css")), name="css")
app.mount("/js", StaticFiles(directory=str(config.STATIC_DIR / "js")), name="js")
app.mount("/backend", StaticFiles(directory=str(config.BASE_DIR)), name="backend-data")

@app.on_event("startup")
def _on_startup() -> None:
    init_db()

# Entry point for Railway
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
