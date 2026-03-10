# api/__main__.py
"""Railway compatible entry point"""
import uvicorn
import os
import sys

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    print(f"Starting FastAPI application on port {port}...", flush=True)

    try:
        uvicorn.run(
            "api:app",
            host="0.0.0.0",
            port=port,
            log_level="info",
            access_log=True,
            # 增加超时以适应 Railway 环境
            timeout_keep_alive=30,
        )
    except Exception as e:
        print(f"Failed to start application: {e}", flush=True)
        sys.exit(1)
