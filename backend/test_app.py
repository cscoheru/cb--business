# test_app.py - 极简FastAPI测试应用
from fastapi import FastAPI
import os

app = FastAPI(title="Railway Test")

@app.get("/")
def read_root():
    return {
        "status": "running",
        "port": os.getenv("PORT", "8000"),
        "message": "FastAPI is working!"
    }

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.get("/test")
def test():
    return {"test": "success"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
