"""
零担物流优化系统 Flask Web API
Logistics Optimization System Flask Web API

提供RESTful API接口支持前端调用和异步任务管理
"""

from flask import Flask, request, jsonify, send_file, abort
from flask_cors import CORS
import threading
import uuid
import json
import os
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, List
import traceback
import pandas as pd

# 导入配置和主系统
from config import (API_CONFIG, FRONTEND_CONFIG, TASK_CONFIG,
                   create_all_directories, validate_extended_config)
from main import LogisticsOptimizationSystemV2

# 创建Flask应用
app = Flask(__name__)

# 启用CORS支持
if API_CONFIG['enable_cors']:
    CORS(app)

# 配置Flask
app.config['SECRET_KEY'] = API_CONFIG['secret_key']
app.config['MAX_CONTENT_LENGTH'] = API_CONFIG['max_request_size_mb'] * 1024 * 1024


class OptimizationTaskManager:
    """优化任务管理器"""

    def __init__(self):
        self.running_tasks: Dict[str, Dict] = {}
        self.completed_tasks: Dict[str, Dict] = {}
        self.task_lock = threading.Lock()
        self.max_concurrent = TASK_CONFIG['max_concurrent_optimization_tasks']

    def submit_task(self, task_id: str, config: Dict = None) -> bool:
        """提交新的优化任务"""
        with self.task_lock:
            # 检查并发限制
            if len(self.running_tasks) >= self.max_concurrent:
                return False

            # 创建任务记录
            task_record = {
                'task_id': task_id,
                'status': 'submitted',
                'progress': 0,
                'current_step': '任务初始化中...',
                'steps_completed': 0,
                'total_steps': 13,
                'start_time': datetime.now().isoformat(),
                'config': config or {},
                'thread': None,
                'results': None,
                'error': None
            }

            self.running_tasks[task_id] = task_record

            # 启动后台线程执行优化
            thread = threading.Thread(
                target=self._run_optimization_task,
                args=(task_id,)
            )
            thread.daemon = True
            task_record['thread'] = thread
            thread.start()

            return True

    def _run_optimization_task(self, task_id: str):
        """在后台线程中执行优化任务"""
        try:
            with self.task_lock:
                task = self.running_tasks[task_id]
                task['status'] = 'running'
                task['current_step'] = '正在初始化优化系统...'
                task['progress'] = 5

            # 创建优化系统实例
            system = LogisticsOptimizationSystemV2(verbose=False)

            # 自定义进度回调
            def progress_callback(step: str, progress: int, steps_completed: int):
                with self.task_lock:
                    if task_id in self.running_tasks:
                        self.running_tasks[task_id].update({
                            'current_step': step,
                            'progress': progress,
                            'steps_completed': steps_completed
                        })

            # 执行完整优化流程
            with self.task_lock:
                task = self.running_tasks[task_id]
                task['current_step'] = '开始执行优化...'
                task['progress'] = 10

            results = system.run_complete_optimization()

            # 任务完成，移动到已完成任务
            with self.task_lock:
                if task_id in self.running_tasks:
                    completed_task = self.running_tasks.pop(task_id)
                    completed_task.update({
                        'status': 'completed',
                        'progress': 100,
                        'current_step': '优化完成',
                        'steps_completed': 13,
                        'end_time': datetime.now().isoformat(),
                        'results': results
                    })
                    self.completed_tasks[task_id] = completed_task

        except Exception as e:
            # 任务失败
            error_msg = str(e)
            error_traceback = traceback.format_exc()

            with self.task_lock:
                if task_id in self.running_tasks:
                    failed_task = self.running_tasks.pop(task_id)
                    failed_task.update({
                        'status': 'failed',
                        'current_step': f'优化失败: {error_msg}',
                        'end_time': datetime.now().isoformat(),
                        'error': error_msg,
                        'error_details': error_traceback
                    })
                    self.completed_tasks[task_id] = failed_task

    def get_task_status(self, task_id: str) -> Optional[Dict]:
        """获取任务状态"""
        with self.task_lock:
            if task_id in self.running_tasks:
                task = self.running_tasks[task_id].copy()
                # 移除不需要返回的字段
                task.pop('thread', None)
                return task
            elif task_id in self.completed_tasks:
                task = self.completed_tasks[task_id].copy()
                # 移除敏感信息
                task.pop('error_details', None)
                return task
            return None

    def get_task_result(self, task_id: str) -> Optional[Dict]:
        """获取任务详细结果"""
        with self.task_lock:
            if task_id in self.completed_tasks:
                task = self.completed_tasks[task_id]
                if task['status'] == 'completed':
                    return task.get('results')
        return None

    def cleanup_old_tasks(self):
        """清理过期任务"""
        cutoff_time = datetime.now() - timedelta(hours=TASK_CONFIG['task_result_retention_hours'])

        with self.task_lock:
            to_remove = []
            for task_id, task in self.completed_tasks.items():
                task_time = datetime.fromisoformat(task.get('end_time', task.get('start_time')))
                if task_time < cutoff_time:
                    to_remove.append(task_id)

            for task_id in to_remove:
                self.completed_tasks.pop(task_id, None)


# 全局任务管理器实例
task_manager = OptimizationTaskManager()


@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查接口"""
    return jsonify({
        'status': 'healthy',
        'service': 'Logistics Optimization System API',
        'version': '3.0',
        'timestamp': datetime.now().isoformat(),
        'running_tasks': len(task_manager.running_tasks),
        'completed_tasks': len(task_manager.completed_tasks)
    })


@app.route('/api/optimize', methods=['POST'])
def submit_optimization():
    """
    提交优化任务
    支持上传Excel文件或使用默认数据
    """
    try:
        task_id = str(uuid.uuid4())

        # 解析请求参数
        config = {}
        if request.is_json:
            config = request.get_json() or {}

        # 处理文件上传（如果有）
        if 'file' in request.files:
            file = request.files['file']
            if file.filename:
                # 验证文件类型
                if not file.filename.lower().endswith(('.xlsx', '.xls')):
                    return jsonify({
                        'error': '不支持的文件格式，请上传Excel文件'
                    }), 400

                # 保存上传的文件
                upload_dir = Path(FRONTEND_CONFIG['upload_folder'])
                upload_dir.mkdir(parents=True, exist_ok=True)

                file_path = upload_dir / f"{task_id}_{file.filename}"
                file.save(str(file_path))
                config['data_file'] = str(file_path)

        # 提交任务
        if task_manager.submit_task(task_id, config):
            return jsonify({
                'task_id': task_id,
                'status': 'submitted',
                'message': '优化任务已提交',
                'estimated_time': '10-30分钟',
                'status_url': f'/api/status/{task_id}',
                'result_url': f'/api/result/{task_id}'
            }), 202
        else:
            return jsonify({
                'error': '系统繁忙，请稍后重试',
                'reason': '已达到最大并发任务数限制'
            }), 503

    except Exception as e:
        return jsonify({
            'error': '提交任务失败',
            'details': str(e)
        }), 500


@app.route('/api/status/<task_id>', methods=['GET'])
def get_task_status(task_id: str):
    """查询任务执行状态"""
    try:
        task_status = task_manager.get_task_status(task_id)

        if not task_status:
            return jsonify({
                'error': '任务不存在'
            }), 404

        # 计算预计剩余时间
        estimated_remaining = '未知'
        if task_status['status'] == 'running' and task_status['progress'] > 0:
            elapsed_time = (datetime.now() - datetime.fromisoformat(task_status['start_time'])).total_seconds()
            if task_status['progress'] > 5:  # 避免除零
                total_estimated = elapsed_time * 100 / task_status['progress']
                remaining_seconds = max(0, total_estimated - elapsed_time)
                estimated_remaining = f"{remaining_seconds // 60:.0f}分钟"

        response = {
            'task_id': task_id,
            'status': task_status['status'],
            'progress': task_status['progress'],
            'current_step': task_status['current_step'],
            'steps_completed': task_status['steps_completed'],
            'total_steps': task_status['total_steps'],
            'estimated_remaining': estimated_remaining,
            'start_time': task_status['start_time']
        }

        if task_status['status'] in ['completed', 'failed']:
            response['end_time'] = task_status.get('end_time')

        if task_status['status'] == 'failed':
            response['error'] = task_status.get('error')

        return jsonify(response)

    except Exception as e:
        return jsonify({
            'error': '查询状态失败',
            'details': str(e)
        }), 500


@app.route('/api/result/<task_id>', methods=['GET'])
def get_optimization_result(task_id: str):
    """获取优化结果摘要"""
    try:
        results = task_manager.get_task_result(task_id)

        if not results:
            task_status = task_manager.get_task_status(task_id)
            if not task_status:
                return jsonify({'error': '任务不存在'}), 404
            elif task_status['status'] == 'running':
                return jsonify({'error': '任务仍在运行中'}), 202
            elif task_status['status'] == 'failed':
                return jsonify({
                    'error': '任务执行失败',
                    'details': task_status.get('error')
                }), 500
            else:
                return jsonify({'error': '结果不可用'}), 404

        # 提取关键指标
        performance_metrics = results.get('performance_metrics', {})
        large_cargo_results = results.get('large_cargo_results', {})
        ltl_results = results.get('ltl_optimization_results', {})
        route_reports = results.get('route_reports', [])

        response = {
            'task_id': task_id,
            'status': 'completed',
            'summary': {
                'total_trucks_used': performance_metrics.get('total_trucks_used', 0),
                'total_items_loaded': performance_metrics.get('total_items_loaded', 0),
                'loading_efficiency': round(performance_metrics.get('overall_loading_efficiency', 0) * 100, 1),
                'large_cargo_trucks': large_cargo_results.get('trucks_used', 0),
                'ltl_trucks': ltl_results.get('trucks_used', 0),
                'optimization_time': results.get('system_info', {}).get('total_runtime_formatted', '未知')
            },
            'files': {
                'route_reports_count': len(route_reports),
                'visualization_files_count': len(results.get('visualization_files', [])),
                'excel_download': f'/api/download/{task_id}/excel'
            },
            'detailed_results': {
                'large_cargo': {
                    'dispatched_orders': large_cargo_results.get('successfully_dispatched_orders', 0),
                    'trucks_used': large_cargo_results.get('trucks_used', 0),
                    'efficiency': round(large_cargo_results.get('dispatch_efficiency', 0) * 100, 1)
                },
                'ltl_optimization': {
                    'loaded_items': ltl_results.get('loaded_items', 0),
                    'trucks_used': ltl_results.get('trucks_used', 0),
                    'loading_rate': round(ltl_results.get('total_loading_rate', 0) * 100, 1)
                }
            }
        }

        return jsonify(response)

    except Exception as e:
        return jsonify({
            'error': '获取结果失败',
            'details': str(e)
        }), 500


@app.route('/api/download/<task_id>/<file_type>', methods=['GET'])
def download_result_file(task_id: str, file_type: str):
    """下载结果文件"""
    try:
        results = task_manager.get_task_result(task_id)

        if not results:
            return jsonify({'error': '任务结果不存在'}), 404

        if file_type == 'excel':
            # 查找Excel报告文件
            route_reports = results.get('route_reports', [])
            excel_files = [f for f in route_reports if f.endswith('.xlsx')]

            if excel_files:
                excel_file = excel_files[0]  # 使用第一个Excel文件
                if os.path.exists(excel_file):
                    return send_file(
                        excel_file,
                        as_attachment=True,
                        download_name=f"optimization_report_{task_id}.xlsx"
                    )

            return jsonify({'error': 'Excel报告文件不存在'}), 404

        elif file_type == 'routes':
            # 返回所有路径文件的下载链接
            route_reports = results.get('route_reports', [])
            return jsonify({
                'route_files': [
                    {
                        'filename': Path(f).name,
                        'download_url': f'/api/download/{task_id}/route_file/{Path(f).name}'
                    }
                    for f in route_reports if f.endswith('.json')
                ]
            })

        elif file_type == 'visualizations':
            # 返回可视化文件列表
            viz_files = results.get('visualization_files', [])
            return jsonify({
                'visualization_files': [
                    {
                        'filename': Path(f).name,
                        'download_url': f'/api/download/{task_id}/viz_file/{Path(f).name}'
                    }
                    for f in viz_files
                ]
            })

        else:
            return jsonify({'error': '不支持的文件类型'}), 400

    except Exception as e:
        return jsonify({
            'error': '下载文件失败',
            'details': str(e)
        }), 500


@app.route('/api/config', methods=['GET', 'POST'])
def manage_config():
    """管理系统配置"""
    if request.method == 'GET':
        # 返回当前配置（仅返回安全的配置项）
        safe_config = {
            'route_generation': {
                'avg_speed_kmh': 40,
                'service_time_pickup': 20,
                'service_time_delivery': 30,
                'max_working_hours': 10,
                'start_time': '08:00'
            },
            'optimization': {
                'max_trucks_available': 20,
                'objective': 'maximize_loading_rate'
            }
        }
        return jsonify(safe_config)

    elif request.method == 'POST':
        # 更新配置（这里可以添加配置更新逻辑）
        return jsonify({
            'message': '配置更新功能暂未实现',
            'status': 'not_implemented'
        }), 501


@app.route('/api/tasks', methods=['GET'])
def list_tasks():
    """列出所有任务"""
    try:
        all_tasks = []

        # 添加运行中的任务
        with task_manager.task_lock:
            for task_id, task in task_manager.running_tasks.items():
                all_tasks.append({
                    'task_id': task_id,
                    'status': task['status'],
                    'progress': task['progress'],
                    'start_time': task['start_time'],
                    'current_step': task['current_step']
                })

            # 添加已完成的任务
            for task_id, task in task_manager.completed_tasks.items():
                all_tasks.append({
                    'task_id': task_id,
                    'status': task['status'],
                    'start_time': task['start_time'],
                    'end_time': task.get('end_time'),
                    'error': task.get('error') if task['status'] == 'failed' else None
                })

        # 按开始时间排序
        all_tasks.sort(key=lambda x: x['start_time'], reverse=True)

        return jsonify({
            'tasks': all_tasks,
            'total_count': len(all_tasks),
            'running_count': len(task_manager.running_tasks),
            'completed_count': len(task_manager.completed_tasks)
        })

    except Exception as e:
        return jsonify({
            'error': '获取任务列表失败',
            'details': str(e)
        }), 500


# ===== 高级可视化接口 =====

@app.route('/api/visualizations/types', methods=['GET'])
def get_visualization_types():
    """获取可用的可视化类型"""
    visualization_types = {
        'single_category_3dpp': {
            'name': '单品类3DPP装载可视化',
            'description': '专门展示大货物的详细3D装载方案，包括空间利用率分析',
            'requires': 'truck_assignments'
        },
        'multi_category_3dpp': {
            'name': '多品类3DPP装载可视化',
            'description': '同时展示大、中、小货物的混合装载方案，按类别颜色编码',
            'requires': 'truck_assignments'
        },
        'loading_density_heatmap': {
            'name': '装载密度热力图',
            'description': '展示货车空间利用的密度分布',
            'requires': 'truck_assignments'
        },
        '3d_efficiency_analysis': {
            'name': '3D装载效率分析',
            'description': '展示不同车辆的装载效率对比',
            'requires': 'truck_assignments'
        },
        'route_optimization': {
            'name': '路径优化结果可视化',
            'description': '展示路径优化结果和效率分析',
            'requires': 'route_solutions'
        },
        'route_efficiency_heatmap': {
            'name': '路径效率热力图',
            'description': '地理效率热力图',
            'requires': 'route_solutions'
        },
        'vehicle_performance_dashboard': {
            'name': '车辆性能仪表盘',
            'description': '车辆性能指标可视化',
            'requires': 'route_solutions'
        },
        'comprehensive_route_analysis': {
            'name': '综合路径分析',
            'description': '多角度路径分析',
            'requires': 'route_solutions'
        }
    }

    return jsonify({
        'available_types': visualization_types,
        'total_types': len(visualization_types),
        'categories': ['3d_packing', 'route_optimization', 'analytics']
    })


@app.route('/api/visualizations/<task_id>/generate', methods=['POST'])
def generate_custom_visualization(task_id: str):
    """为指定任务生成自定义可视化"""
    try:
        # 检查任务是否存在且已完成
        if task_id not in task_manager.completed_tasks:
            return jsonify({
                'error': '任务不存在或未完成',
                'task_id': task_id
            }), 404

        # 获取请求参数
        request_data = request.get_json() or {}
        viz_types = request_data.get('visualization_types', [])

        if not viz_types:
            return jsonify({
                'error': '请指定要生成的可视化类型',
                'available_types': list(get_visualization_types().get_json()['available_types'].keys())
            }), 400

        # 获取任务结果
        task_result = task_manager.completed_tasks[task_id]
        complete_solution = task_result.get('result', {})

        # 生成可视化
        from main import LogisticsOptimizationSystemV2
        system = LogisticsOptimizationSystemV2(verbose=False)

        generated_files = []
        generation_status = {}

        for viz_type in viz_types:
            try:
                if viz_type == 'single_category_3dpp':
                    files = system._generate_enhanced_single_category_visualization(complete_solution)
                    generated_files.extend(files)
                    generation_status[viz_type] = 'success'

                elif viz_type == 'multi_category_3dpp':
                    files = system._generate_multi_category_visualization(complete_solution)
                    generated_files.extend(files)
                    generation_status[viz_type] = 'success'

                elif viz_type == 'loading_density_heatmap':
                    file_path = system._generate_loading_density_heatmap(complete_solution)
                    if file_path:
                        generated_files.append(file_path)
                    generation_status[viz_type] = 'success'

                elif viz_type == '3d_efficiency_analysis':
                    file_path = system._generate_3d_efficiency_analysis(complete_solution)
                    if file_path:
                        generated_files.append(file_path)
                    generation_status[viz_type] = 'success'

                elif viz_type in ['route_optimization', 'route_efficiency_heatmap',
                                'vehicle_performance_dashboard', 'comprehensive_route_analysis']:
                    files = system._generate_route_optimization_visualizations(complete_solution)
                    generated_files.extend(files)
                    generation_status[viz_type] = 'success'

                else:
                    generation_status[viz_type] = 'unsupported'

            except Exception as e:
                generation_status[viz_type] = f'error: {str(e)}'

        return jsonify({
            'task_id': task_id,
            'generated_files': generated_files,
            'generation_status': generation_status,
            'total_generated': len(generated_files),
            'timestamp': datetime.now().isoformat()
        })

    except Exception as e:
        return jsonify({
            'error': '生成可视化时发生错误',
            'message': str(e)
        }), 500


@app.route('/api/visualizations/<task_id>/files', methods=['GET'])
def list_visualization_files(task_id: str):
    """列出任务的所有可视化文件"""
    try:
        # 检查任务是否存在
        if task_id not in task_manager.completed_tasks:
            return jsonify({
                'error': '任务不存在或未完成',
                'task_id': task_id
            }), 404

        # 查找可视化文件
        viz_dir = VISUALIZATIONS_DIR
        viz_files = []

        if viz_dir.exists():
            # 查找所有相关的可视化文件
            for file_path in viz_dir.glob('*.html'):
                file_info = {
                    'filename': file_path.name,
                    'size': file_path.stat().st_size,
                    'created': datetime.fromtimestamp(file_path.stat().st_ctime).isoformat(),
                    'type': 'html'
                }

                # 根据文件名判断可视化类型
                if 'single_category' in file_path.name:
                    file_info['category'] = 'single_category_3dpp'
                elif 'multi_category' in file_path.name:
                    file_info['category'] = 'multi_category_3dpp'
                elif 'density_heatmap' in file_path.name:
                    file_info['category'] = 'loading_density_heatmap'
                elif 'efficiency_analysis' in file_path.name:
                    file_info['category'] = '3d_efficiency_analysis'
                elif 'route' in file_path.name:
                    file_info['category'] = 'route_optimization'
                else:
                    file_info['category'] = 'other'

                viz_files.append(file_info)

        # 按创建时间排序
        viz_files.sort(key=lambda x: x['created'], reverse=True)

        return jsonify({
            'task_id': task_id,
            'visualization_files': viz_files,
            'total_files': len(viz_files),
            'timestamp': datetime.now().isoformat()
        })

    except Exception as e:
        return jsonify({
            'error': '获取可视化文件列表时发生错误',
            'message': str(e)
        }), 500


@app.route('/api/visualizations/download/<filename>', methods=['GET'])
def download_visualization_file(filename: str):
    """下载可视化文件"""
    try:
        # 验证文件名安全性
        if '..' in filename or '/' in filename or '\\' in filename:
            return jsonify({
                'error': '无效的文件名'
            }), 400

        file_path = VISUALIZATIONS_DIR / filename

        if not file_path.exists():
            return jsonify({
                'error': '文件不存在',
                'filename': filename
            }), 404

        # 发送文件
        return send_file(
            str(file_path),
            as_attachment=True,
            download_name=filename,
            mimetype='text/html' if filename.endswith('.html') else 'application/octet-stream'
        )

    except Exception as e:
        return jsonify({
            'error': '下载文件时发生错误',
            'message': str(e)
        }), 500


@app.errorhandler(413)
def request_entity_too_large(error):
    """请求实体过大错误处理"""
    return jsonify({
        'error': '上传文件过大',
        'max_size': f"{API_CONFIG['max_request_size_mb']}MB"
    }), 413


@app.errorhandler(500)
def internal_server_error(error):
    """内部服务器错误处理"""
    return jsonify({
        'error': '内部服务器错误',
        'message': '请联系系统管理员'
    }), 500


def cleanup_task():
    """定期清理过期任务"""
    def cleanup_loop():
        while True:
            try:
                task_manager.cleanup_old_tasks()
                time.sleep(3600)  # 每小时清理一次
            except Exception:
                pass  # 静默处理清理错误

    cleanup_thread = threading.Thread(target=cleanup_loop)
    cleanup_thread.daemon = True
    cleanup_thread.start()


def create_app():
    """创建Flask应用工厂函数"""
    # 初始化系统
    create_all_directories()
    validate_extended_config()

    # 启动清理任务
    cleanup_task()

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(
        host=API_CONFIG['host'],
        port=API_CONFIG['port'],
        debug=API_CONFIG['debug'],
        threaded=True
    )