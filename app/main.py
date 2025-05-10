# main.py
from fastapi import FastAPI
from pydantic import BaseModel
from app.ytb_mcp_server import get_video_summary
from fastapi.middleware.cors import CORSMiddleware
from fastapi import HTTPException
from fastapi.responses import JSONResponse

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 或指定 ["http://localhost:3000"] 等
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class VideoRequest(BaseModel):
    video_url: str

@app.post("/summary")
async def summary_post(request: VideoRequest):
    print(request.video_url)

    try:
        resp = await get_video_summary(request.video_url)
        return resp
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    


@app.post("/summary_mock")
async def summary_mock():
    mock_data = {
        "video_info": {
            "id": "Yx1UEdDii5s",
            "title": "The Rise of AI in Factories",
            "fulltitle": "The Rise of AI in Factories",
            "thumbnail": "https://i.ytimg.com/vi/Yx1UEdDii5s/maxresdefault.jpg",
            "description": "AI and automation are becoming part of the American manufacturing landscape. ...",
            "duration": 518,
            "duration_string": "8:38",
            "view_count": 109455,
            "average_rating": None,
            "age_limit": 0,
            "webpage_url": "https://www.youtube.com/watch?v=Yx1UEdDii5s",
            "categories": ["News & Politics"],
            "tags": [
                "News", "bloomberg", "quicktake", "business", "bloomberg quicktake",
                "quicktake originals", "bloomberg\nquicktake by bloomberg", "documentary",
                "mini documentary", "mini doc", "doc", "us news", "world news",
                "finance", "science"
            ],
            "comment_count": 152,
            "chapters": None,
            "heatmap": None,
            "like_count": 2435,
            "cn_subtitle_url": "",
            "en_subtitle_url": "https://www.youtube.com/api/timedtext?v=Yx1UEdDii5s&...",
            "channel_id": "UCUMZ7gohGI9HcU9VNsr2FJQ",
            "channel_url": "https://www.youtube.com/channel/UCUMZ7gohGI9HcU9VNsr2FJQ",
            "channel": "Bloomberg Originals",
            "channel_follower_count": 4570000,
            "uploader": "Bloomberg Originals",
            "uploader_id": "@business",
            "uploader_url": "https://www.youtube.com/@business",
            "upload_date": "20250502",
            "timestamp": 1746201656,
            "original_url": "https://www.youtube.com/watch?v=Yx1UEdDii5s",
            "webpage_url_basename": "watch",
            "webpage_url_domain": "youtube.com",
            "extractor": "youtube",
            "extractor_key": "Youtube"
        },
        "video_summary": [
            {
                "outline": [
                    {"timestamp": "00:00:02", "topic": "在MIT的研究设施中..."},
                    {"timestamp": "00:01:25", "topic": "Ben Armstrong讨论..."},
                    # ... 其他段落省略，可继续补全
                ],
                "summary": "MIT的研究设施中，工程师正在训练机器人以完成各种基本任务...",
                "keywords": ["AI", "自动化", "制造业"],
                "language": "简体中文"
            }
        ]
    }

    return JSONResponse(content=mock_data)
