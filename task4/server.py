import os
import sys
import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from api.routes import router as api_router

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass


app = FastAPI(
    title="Intern Interview Question Generator API",
    description="Automated custom technical and behavioral interview question generator tailored for intern candidates.",
    version="1.0.0",
)

# Enable CORS for local testing and developer integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Router
app.include_router(api_router)

# Mount static frontend
STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
if os.path.exists(STATIC_DIR):
    app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    print(f"🚀 Starting Intern Interview Generator Server on http://localhost:{port}")
    uvicorn.run("server:app", host="0.0.0.0", port=port, reload=True)
