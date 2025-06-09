# main.py
import app.config.settings 
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi import HTTPException
from fastapi.responses import JSONResponse
from app.api.endpoints import yt_dlp

app = FastAPI()

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
    prefix=f"/api/v1/youtube",
    tags=["youtube"]
)


@app.get("/")
async def root():
    return {"message": "Welcome to YouTube Data Tool API"}
