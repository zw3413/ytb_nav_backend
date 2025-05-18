# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi import HTTPException
from fastapi.responses import JSONResponse
from app.config.settings import get_settings
from app.api.endpoints import yt_dlp

settings = get_settings()

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(
    yt_dlp.router,
    prefix=f"{settings.API_V1_STR}/youtube",
    tags=["youtube"]
)


@app.get("/")
async def root():
    return {"message": "Welcome to YouTube Data Tool API"}
