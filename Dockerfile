# KOL 复盘分析 · 线上部署镜像（Railway / 腾讯云 Docker 都可用）
FROM python:3.11-slim

# 装 Node + Claude Code（用「Claude Code 订阅 token」在服务器上生成分析时需要；
# 若只用官方 API key 或离线兜底，可不装，但装着不影响）
RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates \
    && curl -fsSL https://deb.nodesource.com/setup_22.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && npm install -g @anthropic-ai/claude-code \
    && apt-get purge -y curl && apt-get autoremove -y \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

# 工作区默认指向持久盘挂载点（Railway/腾讯云挂一个卷到 /data）
ENV KOL_WORKSPACE=/data
RUN mkdir -p /data

EXPOSE 8000
# 单 worker + 多线程：保证内存里的会话/历史状态一致；生成在后台线程跑
CMD ["sh", "-c", "gunicorn -b 0.0.0.0:${PORT:-8000} -w 1 --threads 8 --timeout 300 kol_analyze.web:app"]
