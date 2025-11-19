"""
系统性能监控和错误处理模块
System Performance Monitoring and Error Handling Module
"""

import time
import traceback
import logging
import psutil
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path


class SystemMonitor:
    """系统性能监控器"""

    def __init__(self):
        self.logger = self._setup_logger()
        self.start_time = None
        self.checkpoints = []
        self.errors = []

    def _setup_logger(self):
        """设置日志记录器"""
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        return logger

    def start_monitoring(self):
        """开始性能监控"""
        self.start_time = time.time()
        self.checkpoints = []
        self.errors = []

        initial_status = self._get_system_status()
        self.logger.info(f"系统监控开始 - 初始状态: {initial_status}")

    def checkpoint(self, name: str, details: Optional[Dict] = None):
        """记录性能检查点"""
        if not self.start_time:
            self.start_time = time.time()

        current_time = time.time()
        elapsed = current_time - self.start_time

        checkpoint_data = {
            'name': name,
            'timestamp': datetime.now().isoformat(),
            'elapsed_seconds': round(elapsed, 2),
            'memory_usage_mb': self._get_memory_usage(),
            'details': details or {}
        }

        self.checkpoints.append(checkpoint_data)
        self.logger.info(f"检查点 [{name}] - 耗时: {elapsed:.2f}s, 内存: {checkpoint_data['memory_usage_mb']}MB")

    def record_error(self, error: Exception, context: str, severity: str = "ERROR"):
        """记录错误信息"""
        error_data = {
            'timestamp': datetime.now().isoformat(),
            'context': context,
            'severity': severity,
            'error_type': type(error).__name__,
            'error_message': str(error),
            'traceback': traceback.format_exc(),
            'system_status': self._get_system_status()
        }

        self.errors.append(error_data)
        self.logger.error(f"错误记录 [{context}] - {error_data['error_type']}: {error_data['error_message']}")

    def _get_system_status(self) -> Dict:
        """获取系统状态"""
        try:
            memory = psutil.virtual_memory()
            cpu_percent = psutil.cpu_percent(interval=0.1)

            return {
                'memory_total_gb': round(memory.total / (1024**3), 2),
                'memory_available_gb': round(memory.available / (1024**3), 2),
                'memory_percent': memory.percent,
                'cpu_percent': cpu_percent,
                'timestamp': datetime.now().isoformat()
            }
        except Exception:
            return {'status': 'unavailable'}

    def _get_memory_usage(self) -> float:
        """获取当前内存使用量（MB）"""
        try:
            process = psutil.Process()
            return round(process.memory_info().rss / (1024**2), 2)
        except Exception:
            return 0.0

    def generate_performance_report(self) -> Dict:
        """生成性能报告"""
        if not self.start_time:
            return {'status': 'no_monitoring_data'}

        total_time = time.time() - self.start_time

        return {
            'monitoring_summary': {
                'total_duration_seconds': round(total_time, 2),
                'total_checkpoints': len(self.checkpoints),
                'total_errors': len(self.errors),
                'start_time': datetime.fromtimestamp(self.start_time).isoformat(),
                'end_time': datetime.now().isoformat()
            },
            'performance_metrics': {
                'average_checkpoint_interval': round(total_time / len(self.checkpoints), 2) if self.checkpoints else 0,
                'peak_memory_usage_mb': max([cp['memory_usage_mb'] for cp in self.checkpoints]) if self.checkpoints else 0,
                'current_system_status': self._get_system_status()
            },
            'checkpoints': self.checkpoints,
            'errors': self.errors,
            'recommendations': self._generate_recommendations()
        }

    def _generate_recommendations(self) -> List[str]:
        """生成性能优化建议"""
        recommendations = []

        if len(self.errors) > 0:
            recommendations.append(f"系统记录了 {len(self.errors)} 个错误，建议检查错误日志")

        if self.checkpoints:
            max_memory = max([cp['memory_usage_mb'] for cp in self.checkpoints])
            if max_memory > 1000:  # 超过1GB
                recommendations.append(f"内存使用峰值为 {max_memory}MB，考虑优化内存使用")

            long_checkpoints = [cp for cp in self.checkpoints if cp['elapsed_seconds'] > 300]  # 超过5分钟
            if long_checkpoints:
                recommendations.append(f"有 {len(long_checkpoints)} 个检查点耗时超过5分钟，考虑优化性能")

        if not recommendations:
            recommendations.append("系统运行正常，无特殊建议")

        return recommendations


class SafeExecutor:
    """安全执行器 - 提供错误恢复和重试机制"""

    def __init__(self, monitor: SystemMonitor):
        self.monitor = monitor
        self.logger = monitor.logger

    def safe_execute(self, func, *args, max_retries: int = 3,
                    context: str = "unknown", **kwargs) -> Optional[Any]:
        """安全执行函数，带重试机制"""

        for attempt in range(max_retries):
            try:
                self.logger.info(f"执行 [{context}] - 尝试 {attempt + 1}/{max_retries}")
                result = func(*args, **kwargs)

                if attempt > 0:
                    self.logger.info(f"[{context}] 在第 {attempt + 1} 次尝试后成功")

                return result

            except Exception as e:
                self.monitor.record_error(e, f"{context} - 尝试 {attempt + 1}",
                                        "ERROR" if attempt == max_retries - 1 else "WARNING")

                if attempt == max_retries - 1:
                    self.logger.error(f"[{context}] 所有 {max_retries} 次尝试均失败")
                    return None
                else:
                    wait_time = 2 ** attempt  # 指数退避
                    self.logger.warning(f"[{context}] 尝试 {attempt + 1} 失败，{wait_time}秒后重试")
                    time.sleep(wait_time)

        return None

    def safe_file_operation(self, operation: str, file_path: Path,
                          operation_func, *args, **kwargs) -> bool:
        """安全的文件操作"""
        try:
            # 确保目录存在
            if operation in ['write', 'create']:
                file_path.parent.mkdir(parents=True, exist_ok=True)

            # 检查文件权限
            if operation == 'read' and not file_path.exists():
                raise FileNotFoundError(f"文件不存在: {file_path}")

            # 执行操作
            result = operation_func(*args, **kwargs)
            self.logger.info(f"文件操作成功 [{operation}]: {file_path.name}")
            return result

        except Exception as e:
            self.monitor.record_error(e, f"文件操作失败 [{operation}]: {file_path}")
            return False


def test_system_monitor():
    """测试系统监控功能"""
    print("=== 系统监控测试 ===")

    monitor = SystemMonitor()
    monitor.start_monitoring()

    # 模拟一些检查点
    monitor.checkpoint("系统初始化")
    time.sleep(0.1)

    monitor.checkpoint("数据加载", {"records": 1000})
    time.sleep(0.1)

    # 模拟错误
    try:
        raise ValueError("测试错误")
    except Exception as e:
        monitor.record_error(e, "测试错误处理")

    monitor.checkpoint("处理完成")

    # 生成报告
    report = monitor.generate_performance_report()

    print(f"监控总时长: {report['monitoring_summary']['total_duration_seconds']}秒")
    print(f"检查点数量: {report['monitoring_summary']['total_checkpoints']}")
    print(f"错误数量: {report['monitoring_summary']['total_errors']}")
    print(f"建议: {report['recommendations']}")

    return True


if __name__ == "__main__":
    test_system_monitor()