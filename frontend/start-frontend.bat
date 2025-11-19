@echo off
echo ========================================
echo 巧满装载平台 - 前端开发服务器
echo ========================================
echo.

cd /d "%~dp0"

echo [1/3] 检查Node.js环境...
node --version
if %errorlevel% neq 0 (
    echo 错误: 未检测到Node.js，请先安装Node.js 16+
    pause
    exit /b 1
)

echo.
echo [2/3] 检查依赖包...
if not exist "node_modules" (
    echo 正在安装依赖包...
    npm install
    if %errorlevel% neq 0 (
        echo 错误: 依赖包安装失败
        pause
        exit /b 1
    )
) else (
    echo 依赖包已存在
)

echo.
echo [3/3] 启动开发服务器...
echo 前端服务将启动在: http://localhost:3000
echo 后端API服务应运行在: http://localhost:8001
echo.
echo 按 Ctrl+C 停止服务
echo.

npm run dev