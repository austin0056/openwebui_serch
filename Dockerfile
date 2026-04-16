FROM python:3.11-slim

ENV DEBIAN_FRONTEND=noninteractive
ENV SEARXNG_SETTINGS_PATH=/etc/searxng/settings.yml

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    git supervisor && \
    rm -rf /var/lib/apt/lists/*

# 安装 SearXNG
RUN pip install --no-cache-dir searxng

# 创建 SearXNG 配置目录
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

# 数据持久化目录
VOLUME ["/data"]

EXPOSE 8080

CMD ["supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
