#!/bin/bash
#! uv pip freeze > requirements.lock
#!chmod +x deploy.sh

echo "🔄 Pulling latest code..."
git pull origin main

echo "🛠️ Rebuilding Docker image..."
docker stop fastapi-app || true
docker rm fastapi-app || true
echo "🛠️ start building Docker image..."
docker build -t fastapi-app .

echo "🚀 Starting new container..."
docker run -d --name fastapi-app -p 8000:8000 fastapi-app

echo "✅ Deployment complete."

# 安装依赖
echo "Installing dependencies..."
uv pip install numpy==1.24.3  # 使用较低版本的 numpy
uv pip install -r requirements.txt
uv pip install "autogen[openai]"  # 安装 autogen 及其 OpenAI 依赖
# 安装 yt-dlp nightly 版本
uv pip install --pre -U "yt-dlp[default]"
# 更新 requirements.txt
uv pip freeze > requirements.txt
# 生成 requirements.lock
uv pip compile requirements.txt -o requirements.lock
