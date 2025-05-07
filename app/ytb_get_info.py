import yt_dlp
from app.ytb_types import YoutubeVideoInfo
import sys
from app.ytb_common import *
import contextlib
import io

def retrieve_video_info(url):
    """
    Lists all available caption languages for a YouTube video.
    
    Args:
        url (str): The URL of the YouTube video.
     
    Returns:
        dict: A dictionary of available language codes and their names.
    """
    try:
        # Set up options for yt-dlp
        ydl_opts = {
            'skip_download': True,  # Don't download the video
            'listsubtitles': True,  # List available subtitles
            'quiet': True,  # Quiet mode, we'll handle the output ourselves
            'logger': StderrLogger(),  # 使用自定义 logger，确保输出不会污染 stdout
            'progress_hooks': [],      # 禁用进度回调
            'no_warnings': True,
        }
        
        # Use yt-dlp to get available subtitles
        with contextlib.redirect_stdout(io.StringIO()):
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
            
        return info
            
    except Exception as e:
        return f"An error occurred: {str(e)}"

def get_subtitle_url(languages, lang_code, format = 'vtt'):
    if lang_code in languages and  languages[lang_code]:
        for sub in languages[lang_code]:
            if sub['ext'] == format:
                return sub['url']
    return ''

def extract_subtitle_url_for_languages(info, lang_codes=['cn','en']):
    en_sub_url = '' 
    cn_sub_url = ''
    lc_cn = 'cn'
    lc_en = 'en'
    languages = None
    # 优先使用自动生成的字幕
    if 'automatic_captions' in info and info['automatic_captions']:
        languages = info['automatic_captions']
    elif 'subtitles' in info and info['subtitles']: # 如果没有的话看有没有附带字幕
        lc_en = 'en-zh-Hans'
        lc_cn = 'zh-Hans-zh-Hans'
        languages = info['subtitles']  
    if languages is not None: #如果找到了字幕，就提取出中文/英文字幕链接出来
        for lang_code in lang_codes:
            if lang_code == 'en':
                en_sub_url = get_subtitle_url(languages, lc_en) # 提取英文字幕文件
            elif lang_code == 'cn':
                cn_sub_url = get_subtitle_url(languages, lc_cn) # 提取中文字幕文件
    return en_sub_url, cn_sub_url

def extract_video_into(info):
    video_info = {}
    video_info['title']= info['']


def get_video_info(video_url):
    info = retrieve_video_info(video_url)
    en_sub_url, cn_sub_url = extract_subtitle_url_for_languages(info) #找中文和英文的字幕，附加到info对象上
    video_info = YoutubeVideoInfo(info)
    video_info.properties['cn_subtitle_url'] = cn_sub_url
    video_info.properties['en_subtitle_url'] = en_sub_url
    return video_info

# Example usage
if __name__ == "__main__":
    video_url = "https://www.youtube.com/watch?v=3fb5YNgvryA"
    video_info = get_video_info(video_url)
    print(video_info, file=sys.stderr)


