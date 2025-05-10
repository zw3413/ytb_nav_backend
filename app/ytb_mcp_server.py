from app.ytb_get_info import *
from app.ytb_types import *
from app.ytb_summarizer import *
import requests,sys
from mcp.server.fastmcp import FastMCP
import asyncio

"""
ytb MCP server
tool1: get_video_summary
通过视频url+语言，获取总结信息
"""

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding='utf-8')
mcp = FastMCP("ytb")


@mcp.tool(
    name="get_video_summary",
    description="Get video summary with a youtube vidoe url, including summary, outline with timestame, keywords.",
)
async def get_video_summary(video_url : str) ->json:
    """
    Args:
        video_url: youtube video url like "https://www.youtube.com/watch?v=5F2S2UUACi4&t=242s"

    return:
        {
            video_info :{
                video_info object fetech through yt-dlp
            },

            video_summary:{   
                "outline": [
                    {"timestamp": "HH:MM:SS", "topic": "Brief description"}
                ],
                "summary": "Comprehensive summary of the video, use a ",
                "keywords": ["keyword1", "keyword2", "keyword3", ...]
            }
        }
    """
    video_info = get_video_info(video_url)
    result_obj = {
        "video_info" : json.loads(video_info.to_json())
    }

    subtitle_url = '' #挑选要使用的字幕链接

    if video_info.cn_subtitle_url and len(video_info.cn_subtitle_url) > 0 : # 优先使用中文字幕
        subtitle_url = video_info.cn_subtitle_url
    elif video_info.en_subtitle_url and len(video_info.en_subtitle_url) > 0: # 如果没有中文字幕，尝试使用英文字幕
        subtitle_url = video_info.en_subtitle_url
    else: # 没有字幕，就先不总结
        print('no subtitles found', file=sys.stderr) 
    
    if len(subtitle_url) > 0 :
        caption_text = download_text(subtitle_url)
        title = video_info.title
        description = video_info.description
        tags = video_info.tags

        # Run the summarization, 目前先默认中文
        summary_result = summarize_youtube_video(
            video_title=title,
            video_description=description,
            video_tags=tags,
            video_captions=caption_text,
            output_language = 'cn'
        )
        result_obj["video_summary"] = [summary_result]

    return result_obj
    

async def test():
    video_url = "https://www.youtube.com/watch?v=AG6AIdQi92Y"
    
    summary_result = await get_video_summary(video_url)

        # Pretty print the results
    print("\n==== VIDEO SUMMARY RESULTS ====\n")
    
    print("OUTLINE WITH TIMESTAMPS:")
    for summary in summary_result["video_summary"] :
        for item in summary["outline"]:
            print(f"[{item['timestamp']}]  {item['topic']}")
        
        print("\nSUMMARY:")
        print(summary["summary"])
    
        print("\nKEYWORDS:")
        print(", ".join(summary["keywords"]))

def download_text(url):
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an error if the response is not 200 OK
        return response.text
    except requests.RequestException as e:
        print(f"Error downloading {url}: {e}", file=sys.stderr)
        return None



if __name__ == "__main__":
    asyncio.run(test())
    #mcp.run(transport='stdio')
    #mcp.run(transport="http", port=8000)
    #mcp.run()
    pass

