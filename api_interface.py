"""
物流优化系统 API 接口说明
Logistics Optimization System API Interface Documentation

本文件提供完整的API接口规范，用于前端开发集成。
包含Flask Web API和前端交互接口的详细说明。

版本: V4.0
最后更新: 2025-09-22
"""

# ==============================================================================
# API 接口概览
# ==============================================================================

API_OVERVIEW = {
    "version": "4.0.0",
    "description": "零担物流3D装箱优化系统API",
    "base_url": "http://localhost:5000/api/v1",
    "supported_formats": ["JSON"],
    "authentication": "Optional (Token-based)",
    "cors_enabled": True
}

# ==============================================================================
# 核心API端点
# ==============================================================================

API_ENDPOINTS = {
    # 系统状态
    "system_status": {
        "method": "GET",
        "path": "/status",
        "description": "获取系统运行状态",
        "response": {
            "status": "active|busy|error",
            "version": "4.0.0",
            "memory_usage": "float (MB)",
            "active_tasks": "int"
        }
    },

    # 优化任务
    "create_optimization_task": {
        "method": "POST",
        "path": "/optimize",
        "description": "创建新的优化任务",
        "request": {
            "data_file": "string (文件路径或base64)",
            "config": {
                "enable_visualization": "boolean",
                "sample_ratio": "float (0.1-1.0)",
                "max_trucks": "int",
                "timeout": "int (秒)"
            }
        },
        "response": {
            "task_id": "string (UUID)",
            "status": "queued|running|completed|failed",
            "estimated_time": "int (秒)"
        }
    },

    # 任务状态查询
    "task_status": {
        "method": "GET",
        "path": "/tasks/{task_id}",
        "description": "查询任务执行状态",
        "response": {
            "task_id": "string",
            "status": "queued|running|completed|failed",
            "progress": "float (0-100)",
            "stage": "string (当前阶段)",
            "results": "object (完成时返回)",
            "error": "string (失败时返回)"
        }
    },

    # 结果下载
    "download_results": {
        "method": "GET",
        "path": "/results/{task_id}/{file_type}",
        "description": "下载任务结果文件",
        "parameters": {
            "file_type": ["json", "excel", "visualization", "report"]
        },
        "response": "File download or JSON with download URLs"
    },

    # 可视化配置
    "visualization_config": {
        "method": "POST",
        "path": "/visualization/config",
        "description": "配置可视化参数",
        "request": {
            "sample_ratio": "float (0.1-1.0)",
            "max_items": "int",
            "enable_density_analysis": "boolean",
            "chart_types": ["3d", "efficiency", "route", "density"]
        }
    }
}

# ==============================================================================
# 数据格式规范
# ==============================================================================

DATA_FORMATS = {
    "input_excel_format": {
        "description": "输入Excel文件格式要求",
        "columns": {
            "取送货类型": "string (取货/送货)",
            "经度": "float",
            "纬度": "float",
            "货物类型": "string (食品/酒水/农产品等)",
            "体积": "float (dm³)",
            "重量": "float (kg)",
            "价值": "float (元)"
        },
        "example": {
            "取送货类型": "取货",
            "经度": 116.3974,
            "纬度": 39.9093,
            "货物类型": "食品",
            "体积": 50.0,
            "重量": 25.0,
            "价值": 1000.0
        }
    },

    "optimization_result_format": {
        "description": "优化结果JSON格式",
        "structure": {
            "summary": {
                "total_trucks_used": "int",
                "total_items_loaded": "int",
                "overall_efficiency": "float (%)",
                "optimization_time": "float (秒)"
            },
            "truck_assignments": {
                "TRUCK_ID": {
                    "loaded_items": [],
                    "route_plan": {},
                    "loading_plan": {},
                    "efficiency": "float (%)"
                }
            },
            "unloaded_items": [],
            "visualization_files": []
        }
    }
}

# ==============================================================================
# 错误代码规范
# ==============================================================================

ERROR_CODES = {
    1001: "无效的输入数据格式",
    1002: "文件上传失败",
    1003: "数据预处理错误",
    2001: "优化算法执行失败",
    2002: "内存不足",
    2003: "任务超时",
    3001: "可视化生成失败",
    3002: "结果文件生成失败",
    9001: "系统内部错误"
}

# ==============================================================================
# 前端集成示例
# ==============================================================================

FRONTEND_EXAMPLES = {
    "javascript_fetch": '''
// 创建优化任务
async function createOptimizationTask(dataFile) {
    const formData = new FormData();
    formData.append('file', dataFile);
    formData.append('config', JSON.stringify({
        enable_visualization: true,
        sample_ratio: 0.3,
        max_trucks: 20,
        timeout: 1800
    }));

    const response = await fetch('/api/v1/optimize', {
        method: 'POST',
        body: formData
    });

    return response.json();
}

// 查询任务状态
async function checkTaskStatus(taskId) {
    const response = await fetch(`/api/v1/tasks/${taskId}`);
    return response.json();
}
    ''',

    "react_component": '''
import React, { useState, useEffect } from 'react';

function OptimizationTask({ dataFile }) {
    const [taskId, setTaskId] = useState(null);
    const [status, setStatus] = useState('idle');
    const [progress, setProgress] = useState(0);
    const [results, setResults] = useState(null);

    const startOptimization = async () => {
        const task = await createOptimizationTask(dataFile);
        setTaskId(task.task_id);
        setStatus('running');
    };

    useEffect(() => {
        if (taskId && status === 'running') {
            const interval = setInterval(async () => {
                const statusData = await checkTaskStatus(taskId);
                setStatus(statusData.status);
                setProgress(statusData.progress);

                if (statusData.status === 'completed') {
                    setResults(statusData.results);
                    clearInterval(interval);
                }
            }, 2000);

            return () => clearInterval(interval);
        }
    }, [taskId, status]);

    return (
        <div>
            {status === 'idle' && (
                <button onClick={startOptimization}>开始优化</button>
            )}
            {status === 'running' && (
                <div>
                    <div>优化进行中... {progress}%</div>
                    <progress value={progress} max={100} />
                </div>
            )}
            {status === 'completed' && results && (
                <div>
                    <h3>优化完成</h3>
                    <p>使用车辆: {results.summary.total_trucks_used}</p>
                    <p>装载货物: {results.summary.total_items_loaded}</p>
                    <p>整体效率: {results.summary.overall_efficiency}%</p>
                </div>
            )}
        </div>
    );
}
    '''
}

# ==============================================================================
# 性能优化配置
# ==============================================================================

PERFORMANCE_CONFIG = {
    "description": "V4.0版本性能优化配置",
    "visualization_limits": {
        "max_items_per_chart": 500,
        "sample_ratio": 0.3,
        "timeout_seconds": 30,
        "enable_density_analysis": False
    },
    "memory_management": {
        "max_memory_usage_gb": 8,
        "batch_processing_size": 1000,
        "enable_garbage_collection": True
    },
    "caching": {
        "enable_result_cache": True,
        "cache_duration_hours": 24,
        "max_cache_size_mb": 512
    }
}

# ==============================================================================
# 部署和配置
# ==============================================================================

DEPLOYMENT_GUIDE = {
    "requirements": [
        "Python >= 3.8",
        "Flask >= 2.0",
        "pandas >= 1.3.0",
        "plotly >= 5.0",
        "gurobi >= 9.5",
        "numpy >= 1.21.0"
    ],

    "environment_variables": {
        "FLASK_ENV": "production",
        "API_PORT": "5000",
        "GUROBI_LICENSE_PATH": "/path/to/license",
        "LOG_LEVEL": "INFO",
        "MAX_WORKERS": "4"
    },

    "startup_command": "python api_interface.py",

    "docker_support": {
        "dockerfile": "Dockerfile",
        "image_name": "logistics-optimization:v4.0",
        "container_port": 5000
    }
}

# ==============================================================================
# 主函数 - 启动Flask应用
# ==============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("物流优化系统 API 接口说明 V4.0")
    print("=" * 60)
    print("📋 API概览:")
    for key, value in API_OVERVIEW.items():
        print(f"  {key}: {value}")

    print("\n🔌 API端点数量:", len(API_ENDPOINTS))
    print("📊 数据格式规范:", len(DATA_FORMATS))
    print("⚠️ 错误代码定义:", len(ERROR_CODES))

    print("\n" + "=" * 60)
    print("此文件包含完整的API规范，用于前端开发集成。")
    print("如需启动实际的Flask服务，请运行 main.py")
    print("=" * 60)