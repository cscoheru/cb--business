# 使用官方 Python 镜像
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000

# 复制依赖文件
COPY requirements.txt .

# 安装依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 暴露端口
EXPOSE 8000

# 启动命令 - 使用 main.py 并禁用调度器自动启动
CMD ["python", "-c", "import uvicorn; uvicorn.run('api:app', host='0.0.0.0', port=int(__import__('os').getenv('PORT', 8000)))"]
