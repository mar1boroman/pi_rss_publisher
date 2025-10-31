# Dockerfile
FROM ghcr.io/astral-sh/uv:python3.13-bookworm

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen

COPY src ./src
COPY api.py ./api.py
COPY main.py ./main.py
COPY init_db.py ./init_db.py

CMD ["bash", "-lc", "echo 'Image built. Use docker-compose services to run.'"]