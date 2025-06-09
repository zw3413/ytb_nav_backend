FROM python:3.11-slim

WORKDIR /app
# 复制项目文件
COPY . .

# 创建虚拟环境并安装依赖
RUN  pip install -r requirements.txt

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
