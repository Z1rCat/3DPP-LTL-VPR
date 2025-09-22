"""
前端集成接口层
Frontend Integration Interface Layer

提供与前端交互的高级接口和任务管理功能
"""

import asyncio
import threading
import json
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, List, Callable
from concurrent.futures import ThreadPoolExecutor
import pandas as pd

from config import (TASK_CONFIG, FRONTEND_CONFIG, API_CONFIG,
                   INTERMEDIATE_DIR, REPORTS_DIR, VISUALIZATIONS_DIR)
from main import LogisticsOptimizationSystemV2


class ProgressTracker:
    """进度跟踪器"""

    def __init__(self):
        self.callbacks: Dict[str, Callable] = {}
        self.progress_data: Dict[str, Dict] = {}

    def register_callback(self, task_id: str, callback: Callable):
        """注册进度回调函数"""
        self.callbacks[task_id] = callback

    def update_progress(self, task_id: str, step: str, progress: int,
                       steps_completed: int = 0, total_steps: int = 13):
        """更新任务进度"""
        progress_info = {
            'task_id': task_id,
            'step': step,
            'progress': min(100, max(0, progress)),
            'steps_completed': steps_completed,
            'total_steps': total_steps,
            'timestamp': datetime.now().isoformat()
        }

        self.progress_data[task_id] = progress_info

        # 调用回调函数
        if task_id in self.callbacks:
            try:
                self.callbacks[task_id](progress_info)
            except Exception:
                pass  # 静默处理回调错误

    def get_progress(self, task_id: str) -> Optional[Dict]:
        """获取任务进度"""
        return self.progress_data.get(task_id)

    def cleanup_progress(self, task_id: str):
        """清理任务进度数据"""
        self.progress_data.pop(task_id, None)
        self.callbacks.pop(task_id, None)


class FrontendInterface:
    """前端集成接口类"""

    def __init__(self):
        self.progress_tracker = ProgressTracker()
        self.executor = ThreadPoolExecutor(max_workers=TASK_CONFIG['max_concurrent_optimization_tasks'])
        self.task_futures: Dict[str, Any] = {}
        self.task_results: Dict[str, Dict] = {}

    def submit_optimization_task(self, task_id: str = None,
                               config: Dict = None,
                               progress_callback: Callable = None) -> str:
        """
        提交优化任务

        Args:
            task_id: 任务ID，如果不提供则自动生成
            config: 优化配置参数
            progress_callback: 进度回调函数

        Returns:
            str: 任务ID
        """
        if not task_id:
            task_id = str(uuid.uuid4())

        # 注册进度回调
        if progress_callback:
            self.progress_tracker.register_callback(task_id, progress_callback)

        # 提交异步任务
        future = self.executor.submit(
            self._run_optimization_with_progress,
            task_id, config or {}
        )

        self.task_futures[task_id] = future

        return task_id

    def _run_optimization_with_progress(self, task_id: str, config: Dict) -> Dict:
        """
        带进度跟踪的优化执行

        Args:
            task_id: 任务ID
            config: 配置参数

        Returns:
            Dict: 优化结果
        """
        try:
            # 初始化进度
            self.progress_tracker.update_progress(task_id, "初始化优化系统...", 5, 0)

            # 创建优化系统
            system = LogisticsOptimizationSystemV2(verbose=False)

            # 运行步骤映射
            step_mapping = {
                "系统初始化开始": ("系统初始化中...", 8, 1),
                "数据预处理开始": ("数据预处理中...", 15, 2),
                "货物分类开始": ("货物分类中...", 25, 3),
                "大货物3DPP优化开始": ("大货物3DPP优化中...", 35, 4),
                "小货物合并开始": ("小货物合并中...", 45, 5),
                "LTL数据准备开始": ("LTL数据准备中...", 55, 6),
                "LTL优化开始": ("LTL优化中...", 65, 7),
                "路径数据生成开始": ("路径数据生成中...", 75, 8),
                "路径优化开始": ("路径优化中...", 80, 9),
                "路径报告生成开始": ("生成路径报告中...", 85, 10),
                "可视化生成开始": ("生成可视化中...", 90, 11),
                "最终报告生成开始": ("生成最终报告中...", 95, 12)
            }

            # 重写监控器的checkpoint方法来更新进度
            original_checkpoint = system.monitor.checkpoint

            def progress_checkpoint(step_name: str, data: Dict = None):
                original_checkpoint(step_name, data)
                if step_name in step_mapping:
                    step_desc, progress, steps = step_mapping[step_name]
                    self.progress_tracker.update_progress(task_id, step_desc, progress, steps)

            system.monitor.checkpoint = progress_checkpoint

            # 执行优化
            self.progress_tracker.update_progress(task_id, "开始执行优化流程...", 10, 1)
            results = system.run_complete_optimization()

            # 完成
            self.progress_tracker.update_progress(task_id, "优化完成", 100, 13)

            # 保存结果
            self.task_results[task_id] = {
                'status': 'completed',
                'results': results,
                'completed_at': datetime.now().isoformat()
            }

            return results

        except Exception as e:
            # 错误处理
            error_msg = str(e)
            self.progress_tracker.update_progress(task_id, f"优化失败: {error_msg}", 0)

            self.task_results[task_id] = {
                'status': 'failed',
                'error': error_msg,
                'failed_at': datetime.now().isoformat()
            }

            raise

    def get_task_status(self, task_id: str) -> Dict:
        """
        获取任务状态

        Args:
            task_id: 任务ID

        Returns:
            Dict: 任务状态信息
        """
        # 检查任务是否存在
        if task_id not in self.task_futures:
            return {'status': 'not_found', 'error': '任务不存在'}

        future = self.task_futures[task_id]
        progress = self.progress_tracker.get_progress(task_id)

        if future.done():
            # 任务已完成
            try:
                result = future.result()
                return {
                    'status': 'completed',
                    'progress': 100,
                    'current_step': '优化完成',
                    'steps_completed': 13,
                    'total_steps': 13,
                    'has_results': True
                }
            except Exception as e:
                return {
                    'status': 'failed',
                    'error': str(e),
                    'progress': 0,
                    'current_step': f'优化失败: {str(e)}'
                }
        else:
            # 任务运行中
            if progress:
                return {
                    'status': 'running',
                    'progress': progress['progress'],
                    'current_step': progress['step'],
                    'steps_completed': progress['steps_completed'],
                    'total_steps': progress['total_steps']
                }
            else:
                return {
                    'status': 'running',
                    'progress': 0,
                    'current_step': '任务启动中...',
                    'steps_completed': 0,
                    'total_steps': 13
                }

    def get_task_result(self, task_id: str) -> Optional[Dict]:
        """
        获取任务结果

        Args:
            task_id: 任务ID

        Returns:
            Optional[Dict]: 任务结果或None
        """
        if task_id in self.task_results:
            result_data = self.task_results[task_id]
            if result_data['status'] == 'completed':
                return result_data['results']

        return None

    def cancel_task(self, task_id: str) -> bool:
        """
        取消任务

        Args:
            task_id: 任务ID

        Returns:
            bool: 是否成功取消
        """
        if task_id in self.task_futures:
            future = self.task_futures[task_id]
            if not future.done():
                cancelled = future.cancel()
                if cancelled:
                    self.progress_tracker.update_progress(
                        task_id, "任务已取消", 0
                    )
                    self.cleanup_task(task_id)
                return cancelled
        return False

    def cleanup_task(self, task_id: str):
        """
        清理任务数据

        Args:
            task_id: 任务ID
        """
        self.task_futures.pop(task_id, None)
        self.task_results.pop(task_id, None)
        self.progress_tracker.cleanup_progress(task_id)

    def get_result_summary(self, task_id: str) -> Optional[Dict]:
        """
        获取结果摘要

        Args:
            task_id: 任务ID

        Returns:
            Optional[Dict]: 结果摘要
        """
        results = self.get_task_result(task_id)
        if not results:
            return None

        # 提取关键指标
        performance_metrics = results.get('performance_metrics', {})
        large_cargo_results = results.get('large_cargo_results', {})
        ltl_results = results.get('ltl_optimization_results', {})
        system_info = results.get('system_info', {})

        return {
            'task_id': task_id,
            'optimization_summary': {
                'total_trucks_used': performance_metrics.get('total_trucks_used', 0),
                'total_items_loaded': performance_metrics.get('total_items_loaded', 0),
                'overall_loading_efficiency': round(
                    performance_metrics.get('overall_loading_efficiency', 0) * 100, 1
                ),
                'runtime': system_info.get('total_runtime_formatted', '未知')
            },
            'large_cargo': {
                'dispatched_orders': large_cargo_results.get('successfully_dispatched_orders', 0),
                'trucks_used': large_cargo_results.get('trucks_used', 0),
                'efficiency': round(large_cargo_results.get('dispatch_efficiency', 0) * 100, 1)
            },
            'ltl_optimization': {
                'loaded_items': ltl_results.get('loaded_items', 0),
                'trucks_used': ltl_results.get('trucks_used', 0),
                'loading_rate': round(ltl_results.get('total_loading_rate', 0) * 100, 1)
            },
            'files': {
                'route_reports_count': len(results.get('route_reports', [])),
                'visualization_files_count': len(results.get('visualization_files', []))
            }
        }

    def get_available_files(self, task_id: str) -> Dict[str, List[str]]:
        """
        获取可用的结果文件列表

        Args:
            task_id: 任务ID

        Returns:
            Dict[str, List[str]]: 文件分类列表
        """
        results = self.get_task_result(task_id)
        if not results:
            return {}

        return {
            'route_reports': results.get('route_reports', []),
            'visualization_files': results.get('visualization_files', []),
            'final_reports': list(results.get('final_reports', {}).values())
        }

    def export_results_to_format(self, task_id: str, format_type: str = 'json') -> Optional[str]:
        """
        导出结果到指定格式

        Args:
            task_id: 任务ID
            format_type: 导出格式 ('json', 'excel', 'csv')

        Returns:
            Optional[str]: 导出文件路径
        """
        results = self.get_task_result(task_id)
        if not results:
            return None

        try:
            export_dir = Path(REPORTS_DIR) / "exports"
            export_dir.mkdir(parents=True, exist_ok=True)

            if format_type == 'json':
                export_file = export_dir / f"optimization_results_{task_id}.json"
                with open(export_file, 'w', encoding='utf-8') as f:
                    json.dump(results, f, ensure_ascii=False, indent=2, default=str)
                return str(export_file)

            elif format_type == 'excel':
                # 这里可以实现Excel导出逻辑
                # 暂时返回已有的Excel文件
                route_reports = results.get('route_reports', [])
                excel_files = [f for f in route_reports if f.endswith('.xlsx')]
                return excel_files[0] if excel_files else None

            elif format_type == 'csv':
                # 这里可以实现CSV导出逻辑
                export_file = export_dir / f"optimization_summary_{task_id}.csv"
                summary = self.get_result_summary(task_id)
                if summary:
                    df = pd.DataFrame([summary['optimization_summary']])
                    df.to_csv(export_file, index=False, encoding='utf-8-sig')
                    return str(export_file)

        except Exception:
            return None

        return None

    def cleanup_old_tasks(self, hours: int = 24):
        """
        清理过期任务

        Args:
            hours: 保留时间（小时）
        """
        cutoff_time = datetime.now() - timedelta(hours=hours)

        to_cleanup = []
        for task_id, result_data in self.task_results.items():
            completed_time_str = result_data.get('completed_at') or result_data.get('failed_at')
            if completed_time_str:
                completed_time = datetime.fromisoformat(completed_time_str)
                if completed_time < cutoff_time:
                    to_cleanup.append(task_id)

        for task_id in to_cleanup:
            self.cleanup_task(task_id)

    def get_system_status(self) -> Dict:
        """
        获取系统状态

        Returns:
            Dict: 系统状态信息
        """
        running_tasks = sum(1 for future in self.task_futures.values() if not future.done())
        completed_tasks = len([r for r in self.task_results.values() if r['status'] == 'completed'])
        failed_tasks = len([r for r in self.task_results.values() if r['status'] == 'failed'])

        return {
            'service_status': 'healthy',
            'version': '2.0',
            'tasks': {
                'running': running_tasks,
                'completed': completed_tasks,
                'failed': failed_tasks,
                'total': len(self.task_results)
            },
            'system_resources': {
                'max_concurrent_tasks': TASK_CONFIG['max_concurrent_optimization_tasks'],
                'available_slots': TASK_CONFIG['max_concurrent_optimization_tasks'] - running_tasks
            },
            'timestamp': datetime.now().isoformat()
        }


# 全局前端接口实例
frontend_interface = FrontendInterface()


def create_frontend_interface() -> FrontendInterface:
    """
    创建前端接口实例的工厂函数

    Returns:
        FrontendInterface: 前端接口实例
    """
    return frontend_interface


# 便捷函数
def submit_optimization(config: Dict = None, progress_callback: Callable = None) -> str:
    """提交优化任务的便捷函数"""
    return frontend_interface.submit_optimization_task(config=config, progress_callback=progress_callback)


def get_optimization_status(task_id: str) -> Dict:
    """获取优化状态的便捷函数"""
    return frontend_interface.get_task_status(task_id)


def get_optimization_result(task_id: str) -> Optional[Dict]:
    """获取优化结果的便捷函数"""
    return frontend_interface.get_task_result(task_id)


if __name__ == "__main__":
    # 测试接口
    def progress_callback(progress_info):
        print(f"进度更新: {progress_info['step']} - {progress_info['progress']}%")

    print("测试前端集成接口...")
    task_id = submit_optimization(progress_callback=progress_callback)
    print(f"任务已提交: {task_id}")

    # 等待任务完成（实际使用中不需要这样做）
    import time
    while True:
        status = get_optimization_status(task_id)
        print(f"任务状态: {status}")

        if status['status'] in ['completed', 'failed']:
            break

        time.sleep(5)

    if status['status'] == 'completed':
        summary = frontend_interface.get_result_summary(task_id)
        print(f"优化结果摘要: {summary}")