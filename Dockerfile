FROM python:3.11-slim

WORKDIR /app

# Install uv globally
RUN pip install uv

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Sync environment with uv (locked and reproducible)
RUN uv pip sync

# Copy the FastAPI app
COPY ./app ./app

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]