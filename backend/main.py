from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from core.config import settings, ALLOWED_ORIGINS_LIST
from routers import story, job, auth, like, comment, follow, feed, notification, analytics, user, bookmark, message, template
from db.database import create_tables
import os

create_tables()

app = FastAPI(
    title="SagaGo - Interactive Story Platform",
    description="Create and share interactive stories",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS_LIST,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Get absolute path for uploads
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, settings.UPLOAD_DIR)

# Create uploads directory if it doesn't exist
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(os.path.join(UPLOAD_DIR, "stories"), exist_ok=True)

# Serve uploaded files from absolute path
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

print(f"📁 Upload directory: {UPLOAD_DIR}")

app.include_router(auth.router, prefix=settings.API_PREFIX)
app.include_router(story.router, prefix=settings.API_PREFIX)
app.include_router(job.router, prefix=settings.API_PREFIX)
app.include_router(like.router, prefix=settings.API_PREFIX)
app.include_router(comment.router, prefix=settings.API_PREFIX)
app.include_router(follow.router, prefix=settings.API_PREFIX)
app.include_router(feed.router, prefix=settings.API_PREFIX)
app.include_router(notification.router, prefix=settings.API_PREFIX)
app.include_router(analytics.router, prefix=settings.API_PREFIX)
app.include_router(user.router, prefix=settings.API_PREFIX)
app.include_router(bookmark.router, prefix=settings.API_PREFIX)
app.include_router(message.router, prefix=settings.API_PREFIX)
app.include_router(template.router, prefix=settings.API_PREFIX)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app="main:app", host="0.0.0.0", port=8000, reload=True)