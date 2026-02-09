FROM python:3.12-slim AS builder

WORKDIR /app

ENV UV_VERSION=0.8.9

RUN pip install --no-cache-dir uv==${UV_VERSION} -i https://pypi.tuna.tsinghua.edu.cn/simple
# RUN pip install --no-cache-dir uv==${UV_VERSION}

# if you located in China, you can use aliyun mirror to speed up
RUN sed -i 's@deb.debian.org@mirrors.aliyun.com@g' /etc/apt/sources.list.d/debian.sources

RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential && \
    rm -rf /var/lib/apt/lists/*

COPY pyproject.toml uv.lock README.md ./
COPY src ./src

# if you located in China, you can use aliyun mirror to speed up
ENV UV_INDEX_URL=https://mirrors.aliyun.com/pypi/simple/
# ENV UV_INDEX_URL=https://pypi.org/simple/
ENV UV_HTTP_TIMEOUT=300

RUN uv sync && \
    rm -rf /root/.cache/uv /root/.cache/pip

FROM python:3.12-slim

WORKDIR /app

# if you located in China, you can use aliyun mirror to speed up
RUN sed -i 's@deb.debian.org@mirrors.aliyun.com@g' /etc/apt/sources.list.d/debian.sources

RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

COPY --from=builder /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"

COPY src ./src
COPY data ./data
COPY .streamlit ./.streamlit

RUN mkdir -p /tmp/image-search

EXPOSE 8501

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

CMD ["streamlit", "run", "--server.port=8501", "--server.address=0.0.0.0", "--server.headless=true", "--server.runOnSave=false", "src/frontend/streamlit_app.py"]
