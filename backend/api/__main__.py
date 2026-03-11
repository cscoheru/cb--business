# api/__main__.py
"""Railway compatible entry point"""
import sys
import os
import traceback

print("=== Starting FastAPI Application ===", flush=True)
print(f"Python version: {sys.version}", flush=True)
print(f"Working directory: {os.getcwd()}", flush=True)
print(f"PORT: {os.getenv('PORT', '8000')}", flush=True)

try:
    import uvicorn
    print("uvicorn imported successfully", flush=True)

    port = int(os.getenv("PORT", 8000))
    print(f"Starting on port {port}...", flush=True)

    # 先测试导入
    print("Testing api import...", flush=True)
    from api import app
    print("api imported successfully", flush=True)
    print(f"App: {app}", flush=True)

    # 启动服务器
    uvicorn.run(
        app,  # 直接传递 app 对象而不是字符串
        host="0.0.0.0",
        port=port,
        log_level="info",
        access_log=True,
        timeout_keep_alive=30,
    )

except ImportError as e:
    print(f"=== IMPORT ERROR ===", flush=True)
    print(f"Error: {e}", flush=True)
    print(f"Traceback:\n{traceback.format_exc()}", flush=True)
    sys.exit(1)

except Exception as e:
    print(f"=== STARTUP ERROR ===", flush=True)
    print(f"Error: {e}", flush=True)
    print(f"Traceback:\n{traceback.format_exc()}", flush=True)
    sys.exit(1)
