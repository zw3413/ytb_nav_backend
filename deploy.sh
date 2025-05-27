#!/bin/bash

echo "🔄 Pulling latest code..."
git pull origin main

echo "🛠️ Rebuilding Docker image..."
docker stop fastapi-app || true
docker rm fastapi-app || true
docker build -t fastapi-app .

# 创建自定义网络（如果不存在）
if ! docker network ls | grep -q ytb_network; then
    echo "🌐 Creating custom network ytb_network..."
    docker network create ytb_network
fi

echo "🚀 Starting new container..."
docker run -d --name fastapi-app --network ytb_network -p 8000:8000 fastapi-app

echo "✅ Deployment complete."
