from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import admin, analytics, auth, cards, friends, graded, holdings, imports, photos

app = FastAPI(title=settings.app_name)

origins = [origin.strip() for origin in settings.allowed_origins.split(",") if origin.strip()]
if not origins:
    origins = ["http://localhost:8080", "http://localhost:5173"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(friends.router, prefix="/api/friends", tags=["friends"])
app.include_router(cards.router, prefix="/api", tags=["catalog"])
app.include_router(holdings.router, prefix="/api/holdings", tags=["holdings"])
app.include_router(graded.router, prefix="/api/graded", tags=["graded"])
app.include_router(photos.router, prefix="/api/photos", tags=["photos"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["analytics"])
app.include_router(imports.router, prefix="/api/import", tags=["import"])
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])


@app.get("/api/health")
def health():
    return {"status": "ok"}
