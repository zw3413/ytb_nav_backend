"""YouTube视频内容分析器，用于生成视频摘要和关键词。"""
import sys
import re
import os
import json
from typing import Dict, List, Tuple, Optional, Any
from dotenv import load_dotenv
from autogen import AssistantAgent, UserProxyAgent, GroupChat, GroupChatManager, config_list_from_json
from app.agents.prompts import (
    SUMMARIZER_SYSTEM_MESSAGE,
    SUMMARY_PROMPT_TEMPLATE,
    INPUT_LIMITS,
    VALIDATOR_SYSTEM_MESSAGE
)

# 加载环境变量
load_dotenv()

class CaptionParsingError(Exception):
    """字幕解析相关的异常。"""
    pass

class SummaryGenerationError(Exception):
    """视频摘要生成相关的异常。"""
    pass

class ValidationError(Exception):
    """输出验证相关的异常。"""
    pass

class AgentManager:
    """管理Agent实例的单例类。"""
    _instance = None
    _summarizer = None
    _validator = None
    _user_proxy = None
    _group_chat = None
    _group_chat_manager = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AgentManager, cls).__new__(cls)
        return cls._instance

    @classmethod
    def get_summarizer(cls) -> AssistantAgent:
        """获取或创建摘要生成器Agent。

        Returns:
            AssistantAgent: 配置好的摘要生成器Agent实例
        """
        if cls._summarizer is None:
            config_list = [
                {
                    "model": os.getenv("OPENAI_MODEL"),
                    "api_key": os.getenv("OPENAI_API_KEY")
                }
            ]
            
            cls._summarizer = AssistantAgent(
                name="VideoSummarizer",
                system_message=SUMMARIZER_SYSTEM_MESSAGE,
                llm_config={"config_list": config_list}
            )
        return cls._summarizer

    @classmethod
    def get_validator(cls) -> AssistantAgent:
        """获取或创建验证器Agent。

        Returns:
            AssistantAgent: 配置好的验证器Agent实例
        """
        if cls._validator is None:
            config_list = [
                {
                    "model": os.getenv("OPENAI_MODEL"),
                    "api_key": os.getenv("OPENAI_API_KEY")
                }
            ]
            
            cls._validator = AssistantAgent(
                name="OutputValidator",
                system_message=VALIDATOR_SYSTEM_MESSAGE,
                llm_config={"config_list": config_list}
            )
        return cls._validator

    @classmethod
    def get_user_proxy(cls) -> UserProxyAgent:
        """获取或创建用户代理Agent。

        Returns:
            UserProxyAgent: 配置好的用户代理Agent实例
        """
        if cls._user_proxy is None:
            cls._user_proxy = UserProxyAgent(
                name="User",
                human_input_mode="NEVER",
                max_consecutive_auto_reply=1,
                code_execution_config=False
            )
        return cls._user_proxy

    @classmethod
    def get_group_chat(cls) -> GroupChat:
        """获取或创建群组对话。

        Returns:
            GroupChat: 配置好的群组对话实例
        """
        if cls._group_chat is None:
            cls._group_chat = GroupChat(
                agents=[cls.get_user_proxy(), cls.get_summarizer(), cls.get_validator()],
                messages=[],
                max_round=50
            )
        return cls._group_chat

    @classmethod
    def get_group_chat_manager(cls) -> GroupChatManager:
        """获取或创建群组对话管理器。

        Returns:
            GroupChatManager: 配置好的群组对话管理器实例
        """
        if cls._group_chat_manager is None:
            cls._group_chat_manager = GroupChatManager(
                group_chat=cls.get_group_chat(),
                llm_config={
                    "config_list": [{
                        "model": os.getenv("OPENAI_MODEL"),
                        "api_key": os.getenv("OPENAI_API_KEY")
                    }]
                }
            )
        return cls._group_chat_manager

    @classmethod
    def reset(cls) -> None:
        """重置所有Agent实例。"""
        cls._summarizer = None
        cls._validator = None
        cls._user_proxy = None
        cls._group_chat = None
        cls._group_chat_manager = None

# 创建Agent管理器实例
agent_manager = AgentManager()

# Function to parse VTT captions
def parse_vtt(vtt_content: str) -> List[Dict[str, str]]:
    """解析VTT格式的字幕内容为结构化格式。

    Args:
        vtt_content: VTT格式的字幕内容

    Returns:
        包含时间戳和文本的字幕列表

    Raises:
        CaptionParsingError: 当字幕解析失败时
    """
    try:
        # Remove WebVTT header
        if vtt_content.startswith("WEBVTT"):
            vtt_content = vtt_content.split("\n\n", 1)[1]
        
        # Split by double newline (each caption block)
        caption_blocks = vtt_content.strip().split("\n\n")
        parsed_captions = []
        total_length = 0
        
        for block in caption_blocks:
            lines = block.strip().split("\n")
            if len(lines) < 2:
                continue
            
            # Get timestamp line
            timestamp_line = lines[0]
            if "-->" not in timestamp_line:
                timestamp_line = lines[1]
            
            # Extract start time
            start_time = timestamp_line.split("-->")[0].strip()
            # Remove milliseconds
            start_time = start_time.split(".")[0]
            
            # Get caption text (can be multiline)
            text_lines = lines[1:] if "-->" in lines[0] else lines[2:]
            raw_text = " ".join(text_lines)
            
            # Clean text:
            text = clean_vtt_text(raw_text)
            
            # Skip if this text is the same as the previous one
            if parsed_captions and parsed_captions[-1]["txt"] == text:
                continue
            
            # 计算包含JSON格式的key在内的字符数
            # caption_length = len('"stime":"' + start_time + '","txt":"' + text + '"')
            # if total_length + caption_length > 90000:
            #     break
                
            parsed_captions.append({
                "stime": start_time,
                "txt": text
            })
            #total_length += caption_length
        
        return parsed_captions
    except Exception as e:
        raise CaptionParsingError(f"Failed to parse VTT content: {str(e)}")

def clean_vtt_text(text: str) -> str:
    """清理VTT文本，移除控制标签和不需要的字符。

    Args:
        text: 原始VTT文本

    Returns:
        清理后的文本
    """
    # 移除时间戳标签 <00:00:01.000>
    text = re.sub(r'<\d{2}:\d{2}:\d{2}\.\d{3}>', '', text)
    
    # 移除所有HTML标签
    text = re.sub(r'</?[^>]+?>', '', text)
    
    # 移除HTML实体
    text = text.replace('&nbsp;', ' ').replace('&gt;', '>').replace('&lt;', '<').replace('&amp;', '&')
    
    # 移除align和position信息
    text = re.sub(r'align:start position:\d+%', '', text)
    
    # 移除重复的空格和换行
    text = re.sub(r'\s+', ' ', text)
    
    # 移除行首和行尾的空白字符
    text = text.strip()
    
    # 移除重复的标点符号
    text = re.sub(r'([.,!?;:])\1+', r'\1', text)
    
    # 移除多余的空格和标点组合
    text = re.sub(r'\s+([.,!?;:])', r'\1', text)
    
    # 移除空行
    text = re.sub(r'\n\s*\n', '\n', text)
    
    # 移除时间戳行（如果存在）
    text = re.sub(r'\d{2}:\d{2}:\d{2}\.\d{3} --> \d{2}:\d{2}:\d{2}\.\d{3}', '', text)
    
    return text.strip()

# Function to convert seconds to HH:MM:SS format
def format_timestamp(timestamp: str) -> str:
    """将时间戳转换为标准HH:MM:SS格式。

    Args:
        timestamp: 原始时间戳

    Returns:
        标准格式的时间戳
    """
    # Remove milliseconds if present
    if "." in timestamp:
        timestamp = timestamp.split(".")[0]
    
    # Ensure HH:MM:SS format (some might be MM:SS)
    parts = timestamp.split(":")
    if len(parts) == 2:
        return f"00:{parts[0]}:{parts[1]}"
    return timestamp

def format_summary_prompt(
    video_title: str,
    video_description: str,
    formatted_captions_text: str,
    language: str
) -> str:
    """格式化视频摘要提示。

    Args:
        video_title: 视频标题
        video_description: 视频描述
        formatted_captions_text: 格式化后的字幕文本
        language: 目标语言

    Returns:
        格式化后的提示消息

    Raises:
        ValueError: 当必要参数缺失或无效时
    """
    # 输入验证
    if not video_title or not isinstance(video_title, str):
        video_title = "No title available"
    if not video_description or not isinstance(video_description, str):
        video_description = "No description available"
    if not formatted_captions_text or not isinstance(formatted_captions_text, str):
        raise ValueError("Captions text is required")
    if not language or not isinstance(language, str):
        raise ValueError("Target language is required")
        
    # 截断过长的输入
    video_title = video_title[:INPUT_LIMITS["title"]]
    video_description = video_description[:INPUT_LIMITS["description"]]
    formatted_captions_text = formatted_captions_text[:INPUT_LIMITS["captions"]]
    
    # 使用模板格式化消息
    return SUMMARY_PROMPT_TEMPLATE.format(
        title=video_title,
        description=video_description,
        captions=formatted_captions_text,
        language=language
    )

def validate_summary(summary_json: str, validator: AssistantAgent, user_proxy: AssistantAgent) -> Tuple[bool, str]:
    """验证摘要输出。

    Args:
        summary_json: 要验证的JSON字符串
        validator: 验证器Agent实例
        user_proxy: 用户代理Agent实例

    Returns:
        Tuple[bool, str]: (是否有效, 错误信息)

    Raises:
        ValidationError: 当验证失败时
    """
    try:
        # 发送验证请求
        user_proxy.initiate_chat(
            validator,
            message=f"Please validate this summary output:\n\n{summary_json}"
        )
        
        # 获取验证结果
        validation_result = user_proxy.chat_messages[validator.name][-1]["content"]
        validation_data = json.loads(validation_result)
        
        if validation_data["is_valid"]:
            return True, validation_data["message"]
        
        # 构建详细的错误信息
        error_parts = []
        
        if "language_issues" in validation_data:
            error_parts.append("Language Issues:\n" + "\n".join(f"- {issue}" for issue in validation_data["language_issues"]))
        
        if "structure_issues" in validation_data:
            error_parts.append("Structure Issues:\n" + "\n".join(f"- {issue}" for issue in validation_data["structure_issues"]))
        
        if "content_issues" in validation_data:
            error_parts.append("Content Issues:\n" + "\n".join(f"- {issue}" for issue in validation_data["content_issues"]))
        
        if "errors" in validation_data:
            error_parts.append("Detailed Errors:\n" + "\n".join(
                f"- {error['field']}: {error['issue']}\n  {error['details']}"
                for error in validation_data["errors"]
            ))
        
        error_message = "\n\n".join(error_parts)
        return False, error_message
        
    except Exception as e:
        raise ValidationError(f"Validation failed: {str(e)}")

class SummaryGroupChat:
    """管理群聊中的代理交互"""
    
    def __init__(self, user_proxy: UserProxyAgent, summarizer: AssistantAgent, validator: AssistantAgent):
        """初始化群聊管理器
        
        Args:
            user_proxy: 用户代理
            summarizer: 视频总结代理
            validator: 验证代理
        """
        self.user_proxy = user_proxy
        self.summarizer = summarizer
        self.validator = validator
        
        # 创建群聊，设置对话顺序和规则
        self.groupchat = GroupChat(
            agents=[user_proxy, summarizer, validator],
            messages=[],
            max_round=3,  # 最多3次尝试
            speaker_selection_method="round_robin",  # 轮流发言
            allow_repeat_speaker=False  # 不允许连续发言
        )
        
        # 创建群聊管理器
        self.manager = GroupChatManager(
            groupchat=self.groupchat,
            llm_config={
                "config_list": summarizer.llm_config["config_list"],
                "timeout": 120,
                "temperature": 0.7,
                "max_tokens": 4000
            }
        )
    
    def process_summary(self, message: str) -> Tuple[bool, str, Dict]:
        """处理视频总结请求
        
        对话流程：
        1. UserProxy 发送初始请求
        2. VideoSummarizer 生成摘要
        3. OutputValidator 验证摘要
        4. 如果验证通过，返回结果
        5. 如果验证失败，返回给 VideoSummarizer 重新生成
        6. 重复步骤 3-5，最多尝试3次
        7. 返回最后一次 VideoSummarizer 生成的结果
        
        Args:
            message: 初始请求消息
            
        Returns:
            Tuple[bool, str, Dict]: (是否成功, 错误信息, 结果数据)
        """
        try:
            # 发送初始请求
            self.user_proxy.initiate_chat(
                self.manager,
                message=message
            )
            
            # 从对话历史中提取结果
            messages = self.groupchat.messages
            last_summary = None
            
            # 遍历消息历史，找到最后一次的总结结果
            for msg in reversed(messages):
                if msg["name"] == "VideoSummarizer":
                    try:
                        # 提取JSON内容
                        json_match = re.search(r'```json\n(.*?)\n```', msg["content"], re.DOTALL)
                        if json_match:
                            json_str = json_match.group(1)
                        else:
                            json_match = re.search(r'({.*})', msg["content"], re.DOTALL)
                            if json_match:
                                json_str = json_match.group(1)
                            else:
                                continue
                                
                        last_summary = json.loads(json_str)
                        # 找到最后一次生成的结果后直接返回
                        return True, "", last_summary
                    except json.JSONDecodeError:
                        continue
            
            # 如果没有找到任何摘要结果
            return False, "No summary result found", None
                
        except Exception as e:
            error_msg = f"Error in summary processing: {str(e)}"
            print(error_msg, file=sys.stderr)
            return False, error_msg, None

async def summarize_youtube_video(
    video_title: str,
    video_description: str,
    video_tags: List[str],
    video_captions: str,
    output_language: str = 'Simplified Chinese'
) -> Dict[str, Any]:
    """生成YouTube视频摘要。

    Args:
        video_title: 视频标题
        video_description: 视频描述
        video_tags: 视频标签列表
        video_captions: 视频字幕文本
        output_language: 输出语言，默认为简体中文

    Returns:
        Dict[str, Any]: 包含视频摘要的字典
    """
    # 初始化代理
    agent_manager = AgentManager()
    user_proxy = agent_manager.get_user_proxy()
    summarizer = agent_manager.get_summarizer()
    validator = agent_manager.get_validator()
    
    # 创建群聊管理器
    group_chat = SummaryGroupChat(user_proxy, summarizer, validator)

    parsed_captions = parse_vtt(video_captions)

    # 准备初始消息
    base_message = SUMMARY_PROMPT_TEMPLATE.format(
        title=video_title,
        description=video_description,
        captions=parsed_captions,
        language=output_language
    )
    
    # 处理总结请求
    success, error_msg, result = group_chat.process_summary(base_message)
    
    if not success:
        if result:  # 如果有结果但验证失败，仍然返回结果
            print(f"Warning: {error_msg}", file=sys.stderr)
            return result
        raise ValidationError(f"Summary validation failed: {error_msg}")
        
    return result

def main() -> None:
    """主函数，用于测试。"""
    # These would be the inputs from the user
    sample_title = "Understanding Quantum Computing: A Beginner's Guide"
    sample_description = "This video explains the basics of quantum computing, including qubits, superposition, and quantum algorithms."
    sample_tags = ["quantum computing", "qubits", "technology", "science", "computers"]
    
    # This would be the VTT file content
    sample_captions = """WEBVTT

00:00:01.000 --> 00:00:05.000
Hello and welcome to our beginner's guide to quantum computing.

00:00:06.000 --> 00:00:12.000
Today we'll explore the fascinating world of qubits, superposition, and quantum algorithms.

00:01:00.000 --> 00:01:10.000
Let's start with the basics. Unlike classical bits, quantum bits or qubits can exist in multiple states simultaneously.

00:02:00.000 --> 00:02:15.000
This property, known as superposition, gives quantum computers their incredible potential for solving complex problems.

00:03:00.000 --> 00:03:20.000
Now let's talk about quantum algorithms and how they differ from classical computing approaches.
"""
    
    # Run the summarization
    summary_result = summarize_youtube_video(
        video_title=sample_title,
        video_description=sample_description,
        video_tags=sample_tags,
        video_captions=sample_captions
    )
    
    # Pretty print the results
    print("\n==== VIDEO SUMMARY RESULTS ====\n", file=sys.stderr)
    
    print("OUTLINE WITH TIMESTAMPS:", file=sys.stderr)
    for item in summary_result["outline"]:
        print(f"[{item['timestamp']}] {item['section']}: {item['topic']}", file=sys.stderr)
    
    print("\nSUMMARY:", file=sys.stderr)
    print(summary_result["summary"], file=sys.stderr)
    
    print("\nKEYWORDS:", file=sys.stderr)
    print(", ".join(summary_result["keywords"]), file=sys.stderr)

# Example usage
if __name__ == "__main__":
    main()