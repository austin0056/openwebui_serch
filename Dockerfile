FROM python:3.11-slim

ENV DEBIAN_FRONTEND=noninteractive
ENV SEARXNG_SETTINGS_PATH=/etc/searxng/settings.yml

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    git supervisor libxslt-dev zlib1g-dev libffi-dev libssl-dev \
    build-essential && \
    rm -rf /var/lib/apt/lists/*

# 从源码安装 SearXNG
RUN git clone --depth 1 https://github.com/searxng/searxng.git /usr/local/searxng/searxng-src && \
    cd /usr/local/searxng/searxng-src && \
    pip install --no-cache-dir -U pip setuptools wheel pyyaml && \
    pip install --no-cache-dir -e .

# 创建配置目录
RUN mkdir -p /etc/searxng /data

# 复制 SearXNG 配置
COPY searxng/settings.yml /etc/searxng/settings.yml

# 复制 FastAPI 应用
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .
COPY config.py .
COPY searxng_client.py .
COPY templates/ templates/
COPY static/ static/

# 复制 supervisord 配置
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Zeabur 持久化硬盘挂载到 /data 目录

EXPOSE 8080

CMD ["supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
