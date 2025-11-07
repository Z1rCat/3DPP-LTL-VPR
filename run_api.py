#!/usr/bin/env python3
"""
简化的API启动脚本
"""

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.app:app", host="0.0.0.0", port=8000, reload=True)
