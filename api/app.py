"""
物流优化系统 Web API 主应用
Logistics Optimization System Web API
"""

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import os
from pathlib import Path
import logging

from .routes.visualization import router as visualization_router
from .routes.data import router as data_router
from .routes.optimization import router as optimization_router

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建FastAPI应用
app = FastAPI(
    title="物流优化系统 API",
    description="Logistics Optimization System API for Vehicle Routing and 3D Bin Packing",
    version="4.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应该设置具体的域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(visualization_router, prefix="/api/visualizations", tags=["可视化"])
app.include_router(data_router, prefix="/api/data", tags=["数据"])
app.include_router(optimization_router, prefix="/api/optimization", tags=["优化"])

# 设置静态文件服务
static_dir = Path(__file__).parent.parent / "frontend" / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# 设置可视化文件服务
visualization_dir = Path(__file__).parent.parent / "output" / "visualizations"
if visualization_dir.exists():
    app.mount("/visualizations", StaticFiles(directory=str(visualization_dir)), name="visualizations")

@app.get("/", response_class=HTMLResponse)
async def root():
    """主页"""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>物流优化系统 API</title>
        <meta charset="utf-8">
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            .header { background: #f0f8ff; padding: 20px; border-radius: 10px; }
            .api-links { margin: 20px 0; }
            .api-links a { display: block; margin: 10px 0; padding: 10px;
                          background: #e6f3ff; text-decoration: none;
                          border-radius: 5px; color: #0066cc; }
            .api-links a:hover { background: #cce6ff; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🚛 物流优化系统 API</h1>
            <p>Logistics Optimization System - Vehicle Routing & 3D Bin Packing API</p>
        </div>

        <div class="api-links">
            <h2>📋 API 文档</h2>
            <a href="/docs">📊 Swagger UI (交互式API文档)</a>
            <a href="/redoc">📖 ReDoc (API文档)</a>

            <h2>🎯 API 端点</h2>
            <a href="/api/visualizations/list">📈 可视化文件列表</a>
            <a href="/api/data/trucks">🚛 卡车数据</a>
            <a href="/api/data/routes">🗺️ 路径数据</a>

            <h2>🎨 可视化</h2>
            <a href="/visualizations">📊 查看生成的可视化文件</a>
        </div>

        <div style="margin-top: 40px; padding: 20px; background: #f9f9f9; border-radius: 10px;">
            <h3>🔧 开发信息</h3>
            <p><strong>版本:</strong> 4.0.0</p>
            <p><strong>状态:</strong> 开发中</p>
            <p><strong>技术栈:</strong> FastAPI + Python + Plotly + Folium</p>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {
        "status": "healthy",
        "version": "4.0.0",
        "message": "物流优化系统 API 运行正常"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)