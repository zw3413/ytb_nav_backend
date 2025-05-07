FROM python:3.11-slim

WORKDIR /app

RUN pip install uv

COPY pyproject.toml requirements.lock ./

# ✅ 使用 freeze 文件
RUN uv pip sync requirements.lock

COPY ./app /app

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
