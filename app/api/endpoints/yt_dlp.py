from app.services.yt_dlp_service import YoutubeDLPService, SubtitleError, VideoProcessingError
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException
import traceback
import sys
import logging
import os
from app.config.redis_config import redis_client

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),  # 输出到标准输出
        logging.StreamHandler(sys.stderr)   # 输出到标准错误
    ]
)
logger = logging.getLogger(__name__)

# 设置环境变量，确保 uvicorn 的日志也显示
os.environ["PYTHONUNBUFFERED"] = "1"

router = APIRouter()

# Initialize the service
yt_service = YoutubeDLPService(redis_client=redis_client, logger=logger)

class SummaryRequest(BaseModel):
    video_id: str
class VideoRequest(BaseModel):
    video_url: str

@router.post("/videoinfo")
async def video_info(request: VideoRequest):
    logger.info(f"Get video info via video URL: {request.video_url}")
    try:
        video_info = await yt_service.get_video_info(request.video_url)
        return {
            "msg": "",
            "code": "000",
            "data": video_info
        }
    except Exception as e:
        # 获取完整的错误堆栈
        error_traceback = traceback.format_exc()
        logger.error(f"Error processing video: {str(e)}\nTraceback:\n{error_traceback}")
        
        # 打印错误到stderr
        print(f"Error processing video: {str(e)}", file=sys.stderr)
        print(f"Traceback:\n{error_traceback}", file=sys.stderr)
        
        raise HTTPException(
            status_code=500,
            detail=f"Error get video info {str(e)}\nTraceback:\n{error_traceback}"
        )

@router.post("/summary")
async def summary_post(request: SummaryRequest):
    logger.info(f"Processing video ID: {request.video_id}")
    try:
        data = await yt_service.get_video_summary(request.video_id)
        if not data or len(data) == 0:
            return {
                "msg": "No video summary",
                "code": "003",
                "data": None
            }
        return {
            "msg": "",
            "code": "000",
            "data": data
        }
    except VideoProcessingError as e:
        logger.warning(f"Video processing error: {str(e)}")
        return {
            "msg": str(e),
            "code": "002",
            "data": None
        }
    except SubtitleError as e:
        logger.warning(f"Subtitle error: {str(e)}")
        return {
            "msg": str(e),
            "code": "001",
            "data": None
        }
    except Exception as e:
        # 获取完整的错误堆栈
        error_traceback = traceback.format_exc()
        logger.error(f"Error processing video: {str(e)}\nTraceback:\n{error_traceback}")
        
        # 打印错误到stderr
        print(f"Error processing video: {str(e)}", file=sys.stderr)
        print(f"Traceback:\n{error_traceback}", file=sys.stderr)
        
        raise HTTPException(
            status_code=500,
            detail=f"Error processing video: {str(e)}\nTraceback:\n{error_traceback}"
        )

@router.post("/summary_mock")
async def summary_mock():
    mock_data = {
        "msg": "",
        "code": "000",
        "data": {
            "video_info": {
                "id": "Yx1UEdDii5s",
                "title": "The Rise of AI in Factories",
                "fulltitle": "The Rise of AI in Factories",
                "thumbnail": "https://i.ytimg.com/vi/Yx1UEdDii5s/maxresdefault.jpg",
                "thumbnails": [
                    {
                        "url": "https://i.ytimg.com/vi/Yx1UEdDii5s/3.jpg",
                        "preference": -37,
                        "id": "0"
                    },
                    {
                        "url": "https://i.ytimg.com/vi_webp/Yx1UEdDii5s/3.webp",
                        "preference": -36,
                        "id": "1"
                    },
                    {
                        "url": "https://i.ytimg.com/vi/Yx1UEdDii5s/2.jpg",
                        "preference": -35,
                        "id": "2"
                    },
                    {
                        "url": "https://i.ytimg.com/vi_webp/Yx1UEdDii5s/2.webp",
                        "preference": -34,
                        "id": "3"
                    },
                    {
                        "url": "https://i.ytimg.com/vi/Yx1UEdDii5s/1.jpg",
                        "preference": -33,
                        "id": "4"
                    },
                    {
                        "url": "https://i.ytimg.com/vi_webp/Yx1UEdDii5s/1.webp",
                        "preference": -32,
                        "id": "5"
                    },
                    {
                        "url": "https://i.ytimg.com/vi/Yx1UEdDii5s/mq3.jpg",
                        "preference": -31,
                        "id": "6"
                    },
                    {
                        "url": "https://i.ytimg.com/vi_webp/Yx1UEdDii5s/mq3.webp",
                        "preference": -30,
                        "id": "7"
                    },
                    {
                        "url": "https://i.ytimg.com/vi/Yx1UEdDii5s/mq2.jpg",
                        "preference": -29,
                        "id": "8"
                    },
                    {
                        "url": "https://i.ytimg.com/vi_webp/Yx1UEdDii5s/mq2.webp",
                        "preference": -28,
                        "id": "9"
                    },
                    {
                        "url": "https://i.ytimg.com/vi/Yx1UEdDii5s/mq1.jpg",
                        "preference": -27,
                        "id": "10"
                    },
                    {
                        "url": "https://i.ytimg.com/vi_webp/Yx1UEdDii5s/mq1.webp",
                        "preference": -26,
                        "id": "11"
                    },
                    {
                        "url": "https://i.ytimg.com/vi/Yx1UEdDii5s/hq3.jpg",
                        "preference": -25,
                        "id": "12"
                    },
                    {
                        "url": "https://i.ytimg.com/vi_webp/Yx1UEdDii5s/hq3.webp",
                        "preference": -24,
                        "id": "13"
                    },
                    {
                        "url": "https://i.ytimg.com/vi/Yx1UEdDii5s/hq2.jpg",
                        "preference": -23,
                        "id": "14"
                    },
                    {
                        "url": "https://i.ytimg.com/vi_webp/Yx1UEdDii5s/hq2.webp",
                        "preference": -22,
                        "id": "15"
                    },
                    {
                        "url": "https://i.ytimg.com/vi/Yx1UEdDii5s/hq1.jpg",
                        "preference": -21,
                        "id": "16"
                    },
                    {
                        "url": "https://i.ytimg.com/vi_webp/Yx1UEdDii5s/hq1.webp",
                        "preference": -20,
                        "id": "17"
                    },
                    {
                        "url": "https://i.ytimg.com/vi/Yx1UEdDii5s/sd3.jpg",
                        "preference": -19,
                        "id": "18"
                    },
                    {
                        "url": "https://i.ytimg.com/vi_webp/Yx1UEdDii5s/sd3.webp",
                        "preference": -18,
                        "id": "19"
                    },
                    {
                        "url": "https://i.ytimg.com/vi/Yx1UEdDii5s/sd2.jpg",
                        "preference": -17,
                        "id": "20"
                    },
                    {
                        "url": "https://i.ytimg.com/vi_webp/Yx1UEdDii5s/sd2.webp",
                        "preference": -16,
                        "id": "21"
                    },
                    {
                        "url": "https://i.ytimg.com/vi/Yx1UEdDii5s/sd1.jpg",
                        "preference": -15,
                        "id": "22"
                    },
                    {
                        "url": "https://i.ytimg.com/vi_webp/Yx1UEdDii5s/sd1.webp",
                        "preference": -14,
                        "id": "23"
                    },
                    {
                        "url": "https://i.ytimg.com/vi/Yx1UEdDii5s/default.jpg",
                        "preference": -13,
                        "id": "24"
                    },
                    {
                        "url": "https://i.ytimg.com/vi_webp/Yx1UEdDii5s/default.webp",
                        "preference": -12,
                        "id": "25"
                    },
                    {
                        "url": "https://i.ytimg.com/vi/Yx1UEdDii5s/mqdefault.jpg",
                        "preference": -11,
                        "id": "26"
                    },
                    {
                        "url": "https://i.ytimg.com/vi_webp/Yx1UEdDii5s/mqdefault.webp",
                        "preference": -10,
                        "id": "27"
                    },
                    {
                        "url": "https://i.ytimg.com/vi/Yx1UEdDii5s/0.jpg",
                        "preference": -9,
                        "id": "28"
                    },
                    {
                        "url": "https://i.ytimg.com/vi_webp/Yx1UEdDii5s/0.webp",
                        "preference": -8,
                        "id": "29"
                    },
                    {
                        "url": "https://i.ytimg.com/vi/Yx1UEdDii5s/hqdefault.jpg?sqp=-oaymwEbCKgBEF5IVfKriqkDDggBFQAAiEIYAXABwAEG&rs=AOn4CLDovyOr6F6e2Gh5EL78wfLPNtfRFA",
                        "height": 94,
                        "width": 168,
                        "preference": -7,
                        "id": "30",
                        "resolution": "168x94"
                    },
                    {
                        "url": "https://i.ytimg.com/vi/Yx1UEdDii5s/hqdefault.jpg?sqp=-oaymwEbCMQBEG5IVfKriqkDDggBFQAAiEIYAXABwAEG&rs=AOn4CLAWAKynPJ6U0P4btdARSEObrC2iSg",
                        "height": 110,
                        "width": 196,
                        "preference": -7,
                        "id": "31",
                        "resolution": "196x110"
                    },
                    {
                        "url": "https://i.ytimg.com/vi/Yx1UEdDii5s/hqdefault.jpg?sqp=-oaymwEcCPYBEIoBSFXyq4qpAw4IARUAAIhCGAFwAcABBg==&rs=AOn4CLBry8hcxlk6aDwlJCe3tF44-YtdCw",
                        "height": 138,
                        "width": 246,
                        "preference": -7,
                        "id": "32",
                        "resolution": "246x138"
                    },
                    {
                        "url": "https://i.ytimg.com/vi/Yx1UEdDii5s/hqdefault.jpg?sqp=-oaymwEcCNACELwBSFXyq4qpAw4IARUAAIhCGAFwAcABBg==&rs=AOn4CLAiE-L5fLyzHiy156htj_HPlZWmSQ",
                        "height": 188,
                        "width": 336,
                        "preference": -7,
                        "id": "33",
                        "resolution": "336x188"
                    },
                    {
                        "url": "https://i.ytimg.com/vi/Yx1UEdDii5s/hqdefault.jpg",
                        "height": 360,
                        "width": 480,
                        "preference": -7,
                        "id": "34",
                        "resolution": "480x360"
                    },
                    {
                        "url": "https://i.ytimg.com/vi_webp/Yx1UEdDii5s/hqdefault.webp",
                        "preference": -6,
                        "id": "35"
                    },
                    {
                        "url": "https://i.ytimg.com/vi/Yx1UEdDii5s/sddefault.jpg",
                        "height": 480,
                        "width": 640,
                        "preference": -5,
                        "id": "36",
                        "resolution": "640x480"
                    },
                    {
                        "url": "https://i.ytimg.com/vi_webp/Yx1UEdDii5s/sddefault.webp",
                        "preference": -4,
                        "id": "37"
                    },
                    {
                        "url": "https://i.ytimg.com/vi/Yx1UEdDii5s/hq720.jpg",
                        "preference": -3,
                        "id": "38"
                    },
                    {
                        "url": "https://i.ytimg.com/vi_webp/Yx1UEdDii5s/hq720.webp",
                        "preference": -2,
                        "id": "39"
                    },
                    {
                        "url": "https://i.ytimg.com/vi/Yx1UEdDii5s/maxresdefault.jpg",
                        "height": 1080,
                        "width": 1920,
                        "preference": -1,
                        "id": "40",
                        "resolution": "1920x1080"
                    },
                    {
                        "url": "https://i.ytimg.com/vi_webp/Yx1UEdDii5s/maxresdefault.webp",
                        "preference": 0,
                        "id": "41"
                    }
                ],
                "description": "AI and automation are becoming part of the American manufacturing landscape. We meet with the chief executive of a predictive maintenance company that uses AI to monitor equipment and visit a research facility developing robotic arms that can anticipate user needs. We also explore what this tech revolution means for workers on the factory floor.\n\nWatch more:\nHow Robots and AI Are Changing Farming - https://youtu.be/A4WUNvwqxIs\nThe World Needs AI, But There's a Problem - https://youtu.be/SpMIs6AnUW8\nHow AI is Revolutionizing Medicine - https://youtu.be/FqsvgFTQv8w\n\n#AI #technology #robots \n--------\nLike this video? Subscribe: http://www.youtube.com/Bloomberg?sub_confirmation=1\n\nGet unlimited access to Bloomberg.com for $1.99/month for the first 3 months: https://www.bloomberg.com/subscriptions?in_source=YoutubeOriginals\n\nBloomberg Originals offers bold takes for curious minds on today's biggest topics. Hosted by experts covering stories you haven't seen and viewpoints you haven't heard, you'll discover cinematic, data-led shows that investigate the intersection of business and culture. Exploring every angle of climate change, technology, finance, sports and beyond, Bloomberg Originals is business as you've never seen it. \n\nSubscribe for business news, but not as you've known it: exclusive interviews, fascinating profiles, data-driven analysis, and the latest in tech innovation from around the world.\n\nVisit our partner channel Bloomberg News for global news and insight in an instant.",
                "duration": 518,
                "duration_string": "8:38",
                "view_count": 138200,
                "average_rating": None,
                "age_limit": 0,
                "webpage_url": "https://www.youtube.com/watch?v=Yx1UEdDii5s",
                "categories": [
                    "News & Politics"
                ],
                "tags": [
                    "News",
                    "bloomberg",
                    "quicktake",
                    "business",
                    "bloomberg quicktake",
                    "quicktake originals",
                    "bloomberg\nquicktake by bloomberg",
                    "documentary",
                    "mini documentary",
                    "mini doc",
                    "doc",
                    "us news",
                    "world news",
                    "finance",
                    "science"
                ],
                "comment_count": 185,
                "chapters": None,
                "heatmap": None,
                "like_count": 3042,
                "cn_subtitle_url": "https://www.youtube.com/api/timedtext?v=Yx1UEdDii5s&ei=Sa0maKKJFMKK2_gPuPSHoQY&caps=asr&opi=112496729&xoaf=5&hl=en&ip=0.0.0.0&ipbits=0&expire=1747390393&sparams=ip%2Cipbits%2Cexpire%2Cv%2Cei%2Ccaps%2Copi%2Cxoaf&signature=82CBD000231ECB6DF56E96A95A8CAE09C2A3AB54.686515E0515261E284AA07671C13319837663951&key=yt8&kind=asr&lang=en&variant=punctuated&tlang=zh-Hans&fmt=vtt",
                "en_subtitle_url": "https://www.youtube.com/api/timedtext?v=Yx1UEdDii5s&ei=Sa0maKKJFMKK2_gPuPSHoQY&caps=asr&opi=112496729&xoaf=5&hl=en&ip=0.0.0.0&ipbits=0&expire=1747390393&sparams=ip%2Cipbits%2Cexpire%2Cv%2Cei%2Ccaps%2Copi%2Cxoaf&signature=82CBD000231ECB6DF56E96A95A8CAE09C2A3AB54.686515E0515261E284AA07671C13319837663951&key=yt8&kind=asr&lang=en&variant=punctuated&fmt=vtt",
                "channel_id": "UCUMZ7gohGI9HcU9VNsr2FJQ",
                "channel_url": "https://www.youtube.com/channel/UCUMZ7gohGI9HcU9VNsr2FJQ",
                "channel": "Bloomberg Originals",
                "channel_follower_count": 4580000,
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
                        {
                            "timestamp": "00:00:00",
                            "topic": "MIT实验室的机器人训练"
                        },
                        {
                            "timestamp": "00:02:00",
                            "topic": "机器臂的功能演示"
                        },
                        {
                            "timestamp": "00:04:00",
                            "topic": "Augury公司的预测性维护技术"
                        },
                        {
                            "timestamp": "00:06:00",
                            "topic": "人工智能对工作岗位的影响"
                        },
                        {
                            "timestamp": "00:08:00",
                            "topic": "未来制造业工作的展望"
                        },
                        {
                            "timestamp": "00:10:00",
                            "topic": "制造业面临的地缘政治和供应链问题"
                        },
                        {
                            "timestamp": "00:12:00",
                            "topic": "人机协作的必要性"
                        }
                    ],
                    "summary": "该视频探讨了人工智能和自动化在美国制造业中的应用。首先，强调了MIT研发的机械臂在执行复杂任务中的潜力。此外，介绍了Augury公司如何通过预测性维护技术，帮助工厂在设备出现故障前进行预警，从而降低维护成本。展望未来，专家指出人工智能对制造业的影响是复杂的，既有可能导致工作岗位的减少，也可能创造新的就业机会。视频还讨论了劳动力老龄化和地缘政治问题对制造业带来的挑战，并提示在全球化的背景下，企业需要灵活应对瞬息万变的市场需求。",
                    "keywords": [
                        "人工智能",
                        "制造业",
                        "自动化"
                    ],
                    "language": "Simplified Chinese"
                }
            ]
        }
    }

    return mock_data

if __name__ == "__main__":
    test()
    pass

