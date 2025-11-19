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
from .routes.experiments import router as experiments_router
from .routes.analytics import router as analytics_router
from .routes.auth import router as auth_router
from .routes.system import router as system_router
from .routes.real_data import router as real_data_router

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
app.include_router(auth_router, prefix="/api/auth", tags=["用户认证"])
app.include_router(system_router, prefix="/api/system", tags=["系统管理"])
app.include_router(visualization_router, prefix="/api/visualizations", tags=["可视化"])
app.include_router(data_router, prefix="/api/data", tags=["数据"])
app.include_router(optimization_router, prefix="/api/optimization", tags=["优化"])
app.include_router(experiments_router, prefix="/api/experiments", tags=["实验管理"])
app.include_router(analytics_router, prefix="/api/analytics", tags=["分析报告"])
app.include_router(real_data_router, prefix="/api/real-data", tags=["真实数据监控"])

# 注册新的优化任务管理API
try:
    from api.optimization_api_simple import router as optimization_task_router
    app.include_router(optimization_task_router, prefix="/api/optimization-task", tags=["优化任务管理"])
    print("[API] 优化任务管理API已加载")
except ImportError as e:
    print(f"[警告] 优化任务管理API加载失败: {e}")
    print("[警告] 将使用基础API功能")

# 设置静态文件服务
static_dir = Path(__file__).parent.parent / "frontend" / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# 设置可视化文件服务
visualization_dir = Path(__file__).parent.parent / "output" / "visualizations"
if visualization_dir.exists():
    app.mount("/visualizations", StaticFiles(directory=str(visualization_dir)), name="visualizations")

# 设置模板目录
templates_dir = Path(__file__).parent.parent / "frontend" / "templates"

@app.get("/login", response_class=HTMLResponse)
async def login_page():
    """登录页面"""
    login_file = templates_dir / "login.html"
    if login_file.exists():
        with open(login_file, 'r', encoding='utf-8') as f:
            return HTMLResponse(content=f.read())
    else:
        return HTMLResponse(content="<h1>登录页面不存在</h1>", status_code=404)

@app.get("/admin", response_class=HTMLResponse)
async def admin_page():
    """管理员控制台 - 优先使用真实数据版本"""
    # 优先使用真实数据监控界面
    admin_real_file = templates_dir / "admin_dashboard_real.html"
    if admin_real_file.exists():
        with open(admin_real_file, 'r', encoding='utf-8') as f:
            return HTMLResponse(content=f.read())

    # 备用：使用高级管理员界面
    admin_v2_file = templates_dir / "admin_dashboard_v2.html"
    if admin_v2_file.exists():
        with open(admin_v2_file, 'r', encoding='utf-8') as f:
            return HTMLResponse(content=f.read())

    # 备用：使用改进版界面
    admin_new_file = templates_dir / "admin_dashboard_new.html"
    if admin_new_file.exists():
        with open(admin_new_file, 'r', encoding='utf-8') as f:
            return HTMLResponse(content=f.read())

    # 备用：使用旧版本
    admin_file = templates_dir / "admin.html"
    if admin_file.exists():
        with open(admin_file, 'r', encoding='utf-8') as f:
            return HTMLResponse(content=f.read())
    else:
        return HTMLResponse(content="<h1>管理员页面不存在</h1>", status_code=404)

@app.get("/admin-real", response_class=HTMLResponse)
async def admin_real_page():
    """真实数据监控管理员控制台"""
    admin_real_file = templates_dir / "admin_dashboard_real.html"
    if admin_real_file.exists():
        with open(admin_real_file, 'r', encoding='utf-8') as f:
            return HTMLResponse(content=f.read())
    else:
        return HTMLResponse(content="<h1>真实数据监控页面不存在</h1>", status_code=404)

@app.get("/admin-v2", response_class=HTMLResponse)
async def admin_v2_page():
    """高级管理员控制台 - 直接访问V2版本"""
    admin_v2_file = templates_dir / "admin_dashboard_v2.html"
    if admin_v2_file.exists():
        with open(admin_v2_file, 'r', encoding='utf-8') as f:
            return HTMLResponse(content=f.read())
    else:
        return HTMLResponse(content="<h1>高级管理员页面不存在</h1>", status_code=404)

@app.get("/admin.html", response_class=HTMLResponse)
async def admin_page_alt():
    """管理员控制台（备用路径）"""
    return await admin_page()

@app.get("/admin/vehicles", response_class=HTMLResponse)
async def admin_vehicles_page():
    """管理员 - 车辆管理页面"""
    vehicles_file = templates_dir / "admin_vehicles.html"
    if vehicles_file.exists():
        with open(vehicles_file, 'r', encoding='utf-8') as f:
            return HTMLResponse(content=f.read())
    else:
        return HTMLResponse(content="<h1>车辆管理页面不存在</h1>", status_code=404)

@app.get("/admin/analytics", response_class=HTMLResponse)
async def admin_analytics_page():
    """管理员 - 智能分析页面"""
    analytics_file = templates_dir / "admin_analytics.html"
    if analytics_file.exists():
        with open(analytics_file, 'r', encoding='utf-8') as f:
            return HTMLResponse(content=f.read())
    else:
        return HTMLResponse(content="<h1>智能分析页面不存在</h1>", status_code=404)

# ===== 新增多角色页面路由 =====

@app.get("/driver", response_class=HTMLResponse)
async def driver_page():
    """司机端页面"""
    driver_file = templates_dir / "driver" / "dashboard.html"
    if driver_file.exists():
        with open(driver_file, 'r', encoding='utf-8') as f:
            return HTMLResponse(content=f.read())
    else:
        return HTMLResponse(content="""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>司机端 - 巧满装载平台</title>
            <link rel="stylesheet" href="/static/css/style.css">
        </head>
        <body>
            <div style="text-align: center; margin-top: 100px;">
                <h1>🚛 司机端页面</h1>
                <p>页面正在开发中...</p>
                <a href="/login">返回登录</a>
            </div>
        </body>
        </html>
        """)

@app.get("/manager", response_class=HTMLResponse)
async def manager_page():
    """管理层页面"""
    manager_file = templates_dir / "manager" / "dashboard.html"
    if manager_file.exists():
        with open(manager_file, 'r', encoding='utf-8') as f:
            return HTMLResponse(content=f.read())
    else:
        return HTMLResponse(content="""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>管理层 - 巧满装载平台</title>
            <link rel="stylesheet" href="/static/css/style.css">
        </head>
        <body>
            <div style="text-align: center; margin-top: 100px;">
                <h1>👥 管理层页面</h1>
                <p>页面正在开发中...</p>
                <a href="/login">返回登录</a>
            </div>
        </body>
        </html>
        """)

@app.get("/customer", response_class=HTMLResponse)
async def customer_page():
    """客户端页面"""
    customer_file = templates_dir / "customer" / "order.html"
    if customer_file.exists():
        with open(customer_file, 'r', encoding='utf-8') as f:
            return HTMLResponse(content=f.read())
    else:
        return HTMLResponse(content="""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>客户端 - 巧满装载平台</title>
            <link rel="stylesheet" href="/static/css/style.css">
        </head>
        <body>
            <div style="text-align: center; margin-top: 100px;">
                <h1>📦 客户端页面</h1>
                <p>页面正在开发中...</p>
                <a href="/login">返回登录</a>
            </div>
        </body>
        </html>
        """)

@app.get("/chengdu_route_map", response_class=HTMLResponse)
async def chengdu_route_map():
    """成都路径地图（司机端固定地图）"""
    map_file = Path(__file__).parent.parent / "chengdu_route_map_fixed.html"
    if map_file.exists():
        with open(map_file, 'r', encoding='utf-8') as f:
            return HTMLResponse(content=f.read())
    else:
        return HTMLResponse(content="<h1>成都地图文件不存在</h1>", status_code=404)

@app.get("/demo", response_class=HTMLResponse)
async def demo_page():
    """演示展示页面"""
    demo_file = templates_dir / "demo" / "optimization.html"
    if demo_file.exists():
        with open(demo_file, 'r', encoding='utf-8') as f:
            return HTMLResponse(content=f.read())
    else:
        return HTMLResponse(content="""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>优化演示 - 巧满装载平台</title>
            <link rel="stylesheet" href="/static/css/style.css">
        </head>
        <body>
            <div style="text-align: center; margin-top: 100px;">
                <h1>🎯 优化演示页面</h1>
                <p>页面正在开发中...</p>
                <a href="/login">返回登录</a>
            </div>
        </body>
        </html>
        """)

@app.get("/", response_class=HTMLResponse)
async def root():
    """主页 - 重定向到登录页面"""
    return HTMLResponse(content="""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>巧满装载平台</title>
        <script>
            window.location.href = '/login';
        </script>
    </head>
    <body>
        <p>正在跳转到登录页面...</p>
        <p>如果没有自动跳转，请<a href="/login">点击这里</a></p>
    </body>
    </html>
    """)

@app.get("/api", response_class=HTMLResponse)
async def api_overview():
    """API概览页面"""
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
            <h2>🔐 用户系统</h2>
            <a href="/login">🔑 用户登录</a>
            <a href="/admin">👤 管理控制台</a>

            <h2>📋 API 文档</h2>
            <a href="/docs">📊 Swagger UI (交互式API文档)</a>
            <a href="/redoc">📖 ReDoc (API文档)</a>

            <h2>🎯 主要功能</h2>
            <a href="/api/auth/login">🔐 用户认证</a>
            <a href="/api/visualizations/list">📈 可视化文件列表</a>
            <a href="/api/data/trucks">🚛 卡车数据</a>
            <a href="/api/data/routes">🗺️ 路径数据</a>
            <a href="/api/optimization/algorithms">⚡ 优化算法</a>
            <a href="/api/experiments/">🧪 实验管理</a>
            <a href="/api/analytics/dashboard">📊 分析仪表板</a>

            <h2>🎨 可视化</h2>
            <a href="/visualizations">📊 查看生成的可视化文件</a>
        </div>

        <div style="margin-top: 40px; padding: 20px; background: #f9f9f9; border-radius: 10px;">
            <h3>🔧 系统信息</h3>
            <p><strong>版本:</strong> 4.0.0 - 现代化管理系统</p>
            <p><strong>状态:</strong> 运行中</p>
            <p><strong>技术栈:</strong> FastAPI + JWT认证 + 响应式前端</p>
            <p><strong>新功能:</strong> 用户认证 + 权限管理 + 现代化UI</p>
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
        "message": "物流优化系统 API 运行正常",
        "features": [
            "3D装载优化",
            "路径规划",
            "实验管理",
            "数据分析",
            "趋势报告",
            "可视化展示"
        ],
        "data_layer": "SQLite + JSON hybrid"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)