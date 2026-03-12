#!/usr/bin/env python3
"""启动脚本 - 用于调试Railway部署问题"""
import os
import sys

print("=" * 50)
print("DEBUG: Starting application...")
print(f"DEBUG: Python version: {sys.version}")
print(f"DEBUG: Working directory: {os.getcwd()}")
print(f"DEBUG: PORT env: {os.getenv('PORT', 'NOT SET')}")
print(f"DEBUG: Files in current directory:")
for f in os.listdir('.')[:10]:
    print(f"  - {f}")
print("=" * 50)

try:
    print("DEBUG: Importing api module...")
    from api import app
    print(f"DEBUG: App imported successfully: {app.title}")
    print(f"DEBUG: Routes count: {len(app.routes)}")

    # Show some routes
    print("DEBUG: Sample routes:")
    for route in list(app.routes)[:5]:
        if hasattr(route, 'path'):
            print(f"  - {route.path}")

    print("=" * 50)
    print("DEBUG: Starting uvicorn server...")
    print("=" * 50)

    import uvicorn
    port = int(os.getenv('PORT', 8000))
    uvicorn.run(
        'api:app',
        host='0.0.0.0',
        port=port,
        log_level='debug'
    )

except Exception as e:
    print("=" * 50)
    print(f"ERROR: Failed to start application!")
    print(f"ERROR: {type(e).__name__}: {e}")
    print("=" * 50)
    import traceback
    traceback.print_exc()
    sys.exit(1)
