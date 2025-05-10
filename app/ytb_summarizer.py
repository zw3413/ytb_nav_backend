import autogen, sys

import re
import json
from typing import Dict, List, Tuple, Optional

# from autogen import AssistantAgent, config_list_openai_aoai
# config_list = [
#     {
#         "model": "qwen2.5:14b",
#         "base_url": "https://ollama.bakers.top/v1",  # Ollama 的 OpenAI API 接口
#         "api_key": "ollama",  # 只是一个占位符，Ollama 不检查 key
#     }
# ]

from autogen import AssistantAgent, UserProxyAgent, config_list_from_json
# Configure the agents
config_list = config_list_from_json(
    "app/oai_config.json",  # This should be a path to your config file
    filter_dict={"model": ["gpt-4o-mini"]}  # Using GPT-4 for better summarization
)

# Function to parse VTT captions
def parse_vtt(vtt_content: str) -> List[Dict[str, str]]:
    """Parse VTT content into structured format, removing control tags."""
    
    # Remove WebVTT header
    if vtt_content.startswith("WEBVTT"):
        vtt_content = vtt_content.split("\n\n", 1)[1]
    
    # Split by double newline (each caption block)
    caption_blocks = vtt_content.strip().split("\n\n")
    parsed_captions = []
    
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
        
        # Get caption text (can be multiline)
        text_lines = lines[1:] if "-->" in lines[0] else lines[2:]
        raw_text = " ".join(text_lines)
        
        # Clean text:
        text = clean_vtt_text(raw_text)
        
        parsed_captions.append({
            "start_time": start_time,
            "text": text
        })
    
    return parsed_captions

def clean_vtt_text(text: str) -> str:
    """Remove VTT control tags and unwanted characters."""
    # Remove tags like <c>, <i>, <b>, <u> and custom timestamp tags <00:00:01.000>
    text = re.sub(r"</?[^>]+?>", "", text)
    # Replace HTML entities if needed (optional, simple common ones)
    text = text.replace("&nbsp;", " ").replace("&gt;", ">").replace("&lt;", "<").replace("&amp;", "&")
    # Collapse multiple spaces
    text = re.sub(r"\s+", " ", text)
    return text.strip()

# Function to convert seconds to HH:MM:SS format
def format_timestamp(timestamp: str) -> str:
    """Convert a timestamp to a standardized HH:MM:SS format."""
    # Remove milliseconds if present
    if "." in timestamp:
        timestamp = timestamp.split(".")[0]
    
    # Ensure HH:MM:SS format (some might be MM:SS)
    parts = timestamp.split(":")
    if len(parts) == 2:
        return f"00:{parts[0]}:{parts[1]}"
    return timestamp

# Define the assistant that will handle the summarization
summarizer_assistant = AssistantAgent(
    name="VideoSummarizer",
    system_message="""
You are an expert video content analyst.

Your task is to analyze the provided video information — including the title, description, and full transcript captions — and generate a comprehensive content summary in JSON format. Your output must contain the following components:

---

1. **Outline with Timestamps**  
   - Identify the **main sections and key ideas** of the video.
   - Each item must include a `"timestamp"` in `"HH:MM:SS"` format and a brief `"topic"` description.
   - **Summarize content blocks**, not individual sentences.
   - Target **5 to 15 items**; do **not exceed 20**.
   - **Exclude** all introductory remarks, greetings, audience engagement (e.g., likes/subscribes), sponsor mentions, and closing summaries.
   - **Group temporally adjacent or topically related content** under a single outline point when appropriate (especially with the same subject or theme).
   - The outline must highlight **only the core informational, educational, or narrative content**.

---

2. **Summary**  
   - Write a **concise and professional** summary of the video's **core content**, structured by **themes or topics**, not by time.
   - Use **formal, factual, and objective language**.
   - Do **not** reference the video itself or its structure (e.g., "the video explains..." or "in the beginning...").
   - Include all essential information, avoiding filler or repetition.

---

3. **Keywords**  
   - Extract **1 to 3 high-value keywords** that best represent the core themes or topics of the video.
   - Use lowercase unless the keyword is a proper noun.

---

4. **Language Compliance**  
   - All content (outline, summary, keywords) must be written in the specified **output language: {language}**.
   - The structure and field names in the JSON must remain in **English**.

---

Return your result in the following JSON structure **only** — without any additional commentary or text:

```json
{
  "outline": [
    { "timestamp": "HH:MM:SS", "topic": "Brief description of the section" }
  ],
  "summary": "Comprehensive summary of the video content. Use professional tone and concise language. Cover all key points accurately.",
  "keywords": ["keyword1", "keyword2", "keyword3"],
  "language": "Language used in the content above"
}
    """,
    llm_config={"config_list": config_list}
)

# Define the user proxy agent that will interact with the assistant
#user_proxy = UserProxyAgent(
 
user_proxy = AssistantAgent(
    name="User",
    human_input_mode="NEVER",
    max_consecutive_auto_reply=0,
        # other parameters...
    # code_execution_config={
    #     "use_docker": False,  # Add this line to disable Docker requirement
    #     # Keep any other code_execution_config settings you have
    # }
)

def format_summary_prompt(video_title, video_description, formatted_captions_text, language):
    """
    Format the prompt for video summarization.
    
    Args:
        video_title (str): The title of the video
        video_description (str): The description of the video
        formatted_captions_text (str): The formatted captions text
        language (str): The target language for the summary
        
    Returns:
        str: The formatted prompt message
    """
    # Input validation
    if not video_title or not isinstance(video_title, str):
        video_title = "No title available"
    if not video_description or not isinstance(video_description, str):
        video_description = "No description available"
    if not formatted_captions_text or not isinstance(formatted_captions_text, str):
        raise ValueError("Captions text is required")
    if not language or not isinstance(language, str):
        raise ValueError("Target language is required")
        
    # Truncate long inputs if necessary
    max_title_length = 200
    max_description_length = 1000
    max_captions_length = 100000
    
    video_title = video_title[:max_title_length]
    video_description = video_description[:max_description_length]
    formatted_captions_text = formatted_captions_text[:max_captions_length]
    
    # Define the JSON structure template
    json_structure = '''{
  "outline": [
    { "timestamp": "HH:MM:SS", "topic": "Brief description of the section" }
  ],
  "summary": "Comprehensive summary of the video content. Use professional and concise language. Cover all key points accurately.",
  "keywords": ["keyword1", "keyword2", "keyword3", "..."],
  "language": "Actual language used in the summary above"
}'''

    # Format the complete message
    message = f"""
You are tasked with summarizing a YouTube video using the transcript captions provided below.

VIDEO TITLE:
{video_title}

VIDEO DESCRIPTION:
{video_description}

CAPTIONS:
{formatted_captions_text}

OUTPUT CONTENT LANGUAGE:
{language}

Instructions:
- Generate the summary content in the specified language: **{language}**.
- Follow the JSON output format strictly as described below.
- Do **not** introduce any content not derived from the captions.
- Maintain a **professional tone**, use **concise and accurate language**, and **do not omit important details**.
- The **structure, field names, and formatting must be strictly followed**.
- Do **not** include any introductory or trailing text—**only the JSON object** is expected in your final output.

Return your result using the following JSON structure:

```json
{json_structure}
```
"""
    return message

def summarize_youtube_video(
    video_title: str,
    video_description: str,
    video_tags: List[str],
    video_captions: str,
    output_language: str
) -> Dict:
    """
    Summarize a YouTube video using its metadata and captions.
    
    Args:
        video_title: The title of the YouTube video
        video_description: The description of the YouTube video
        video_captions: VTT format captions/subtitles
        
    Returns:
        Dictionary containing outline with timestamps, summary, and keywords
    """

    language = ""

    if output_language == 'cn':
        language = "simplified Chinese"
    elif output_language =='en':
        language = "English"

    # Parse the VTT captions
    parsed_captions = parse_vtt(video_captions)
    
    # Format captions for better readability
    formatted_captions = []
    for caption in parsed_captions:
        formatted_captions.append(f"[{format_timestamp(caption['start_time'])}] {caption['text']}")
    
    formatted_captions_text = "\n".join(formatted_captions)
    
    # Create the initial message with all the video data
    message = format_summary_prompt(video_title, video_description, formatted_captions_text, language)
    
    # Start the conversation
    user_proxy.initiate_chat(
        summarizer_assistant,
        message=message
    )
    
    # Extract the JSON from the assistant's last message
    # Get the last message with error handling
    try:
        if summarizer_assistant.name in user_proxy.chat_messages and user_proxy.chat_messages[summarizer_assistant.name]:
            last_message = user_proxy.chat_messages[summarizer_assistant.name][-1]["content"]
        else:
            # Check if there are any messages at all
            for agent_name in user_proxy.chat_messages:
                if user_proxy.chat_messages[agent_name]:
                    last_message = user_proxy.chat_messages[agent_name][-1]["content"]
                    break
            else:
                raise ValueError("No messages found in the conversation history")
    except (IndexError, KeyError) as e:
        raise ValueError(f"Failed to retrieve conversation messages: {e}")
    
    # Extract the JSON content
    json_match = re.search(r'```json\n(.*?)\n```', last_message, re.DOTALL)
    if json_match:
        json_str = json_match.group(1)
    else:
        # Try to find JSON without markdown code blocks
        json_match = re.search(r'({.*})', last_message, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            raise ValueError("Could not extract JSON from assistant's response")
    
    try:
        result = json.loads(json_str)
        return result
    except json.JSONDecodeError:
        print("error happened when call llm", file=sys.stderr)
        # Clean up the string and try again
        json_str = re.sub(r'\\n', '\n', json_str)
        json_str = re.sub(r'\\', '', json_str)
        return json.loads(json_str)

def main():
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
    #main()
    pass