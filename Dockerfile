FROM python:3.11-slim

WORKDIR /app

RUN pip install uv

COPY pyproject.toml uv.lock ./

# ✅ 使用 uv venv 安装依赖（会读取 pyproject.toml 和 uv.lock）
RUN uv venv .venv && .venv/bin/uv pip sync

COPY ./app /app

CMD [".venv/bin/uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
