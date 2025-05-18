FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    ffmpeg \
    python3-dev \
    libssl-dev \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# 安装 uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh

# 首先复制 .env 文件
COPY .env .env

# 然后复制其他项目文件
COPY . .

# 创建虚拟环境并安装依赖
RUN uv venv && \
    . .venv/bin/activate && \
    uv pip install numpy==1.24.3 && \
    uv pip install -r requirements.txt && \
    uv pip install "autogen[openai]" && \
    # 安装 yt-dlp nightly 版本及其依赖
    uv pip uninstall -y yt-dlp && \
    uv pip install --no-cache-dir --pre -U "yt-dlp[default]" && \
    uv pip install --upgrade "cryptography" && \
    # 更新 requirements.txt
    uv pip freeze > requirements.txt && \
    # 生成 requirements.lock
    uv pip compile requirements.txt -o requirements.lock

# 设置环境变量
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
