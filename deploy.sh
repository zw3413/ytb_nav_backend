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
