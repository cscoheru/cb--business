# 使用官方 Python 3.11 镜像
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000 \
    PYTHONPATH=/app

# 先复制requirements.txt以利用Docker缓存
COPY requirements.txt .

# 安装依赖
RUN pip install --no-cache-dir -U pip && \
    pip install --no-cache-dir -r requirements.txt

# 验证uvicorn安装
RUN uvicorn --version

# 复制应用代码
COPY . .

# 确保模块可以正确导入
RUN python -c "from api import app; print('App imported successfully')"

# 暴露端口
EXPOSE 8000

# 启动命令 - 使用完整路径
CMD ["python", "-m", "uvicorn", "api:app:app", "--host", "0.0.0.0", "--port", "8000"]
