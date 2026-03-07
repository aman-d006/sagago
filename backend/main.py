from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import os
import logging
from fastapi import Request
from core.config import settings, ALLOWED_ORIGINS_LIST
from routers import story, job, auth, like, comment, follow, feed, notification, analytics, user, bookmark, message, template
from db.database import create_tables, engine
from db.init_templates import init_templates

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Starting up SagaGo API...")
    logger.info(f"🌍 Environment: {'Render' if os.getenv('RENDER') else 'Development'}")
    
    logger.info("📊 Initializing database...")
    create_tables()
    
    logger.info("✅ Database is ready")
    logger.info("📝 Checking templates...")
    init_templates()
    
    logger.info("✅ Startup complete")
    
    yield
    
    logger.info("🛑 Shutting down...")
    engine.dispose()
    logger.info("✅ Shutdown complete")

app = FastAPI(
    title="SagaGo - Interactive Story Platform",
    description="Create and share interactive stories",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

@app.options("/{rest_of_path:path}")
async def preflight_handler():
    return {}

@app.middleware("http")
async def add_cors_headers(request, call_next):
    response = await call_next(request)
    
    origin = request.headers.get("origin")
    
 
    allowed_origins = [
        "https://sagago.vercel.app",
        "http://localhost:5173", 
        "http://localhost:3000",
        "https://sagago-7.onrender.com"
    ]
    
  
    if origin in allowed_origins:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, PATCH"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-Requested-With, Accept, Origin"
        response.headers["Access-Control-Expose-Headers"] = "Content-Length, Content-Type"
        response.headers["Access-Control-Max-Age"] = "3600"
    
    return response

# Standard CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://sagago.vercel.app",
        "http://localhost:5173",
        "http://localhost:3000",
        "https://sagago-7.onrender.com"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Debug endpoint to verify CORS configuration
@app.get("/api/debug-cors")
async def debug_cors(request: Request):
    origin = request.headers.get("origin")
    return {
        "message": "CORS endpoint is working",
        "allowed_origins": [
            "https://sagago.vercel.app",
            "http://localhost:5173",
            "http://localhost:3000",
            "https://sagago-7.onrender.com"
        ],
        "request_origin": origin,
        "cors_headers_set": origin in [
            "https://sagago.vercel.app",
            "http://localhost:5173",
            "http://localhost:3000",
            "https://sagago-7.onrender.com"
        ]
    }

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, settings.UPLOAD_DIR)

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(os.path.join(UPLOAD_DIR, "stories"), exist_ok=True)
os.makedirs(os.path.join(UPLOAD_DIR, "avatars"), exist_ok=True)

app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

logger.info(f"📁 Upload directory: {UPLOAD_DIR}")

API_PREFIX = settings.API_PREFIX or ""
app.include_router(auth.router, prefix=API_PREFIX)
app.include_router(story.router, prefix=API_PREFIX)
app.include_router(job.router, prefix=API_PREFIX)
app.include_router(like.router, prefix=API_PREFIX)
app.include_router(comment.router, prefix=API_PREFIX)
app.include_router(follow.router, prefix=API_PREFIX)
app.include_router(feed.router, prefix=API_PREFIX)
app.include_router(notification.router, prefix=API_PREFIX)
app.include_router(analytics.router, prefix=API_PREFIX)
app.include_router(user.router, prefix=API_PREFIX)
app.include_router(bookmark.router, prefix=API_PREFIX)
app.include_router(message.router, prefix=API_PREFIX)
app.include_router(template.router, prefix=API_PREFIX)

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "environment": "render" if os.getenv("RENDER") else "development",
        "upload_dir": UPLOAD_DIR
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(
        "main:app", 
        host="0.0.0.0", 
        port=port, 
        reload=not os.getenv("RENDER")
    )