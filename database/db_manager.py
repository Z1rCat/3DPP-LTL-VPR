"""
数据库管理器
Database Manager for SQLite operations
"""

import sqlite3
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from contextlib import contextmanager
import threading

class DatabaseManager:
    """SQLite数据库管理器"""

    def __init__(self, db_path: str = "database/experiments.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # 线程锁，确保多用户安全
        self._lock = threading.Lock()

        self.logger = logging.getLogger(__name__)

        # 初始化数据库
        self._initialize_database()

    def _initialize_database(self):
        """初始化数据库表结构"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # 创建实验表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS experiments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    experiment_id TEXT UNIQUE NOT NULL,
                    name TEXT NOT NULL,
                    description TEXT,
                    algorithm TEXT NOT NULL,
                    parameters TEXT, -- JSON格式参数
                    status TEXT DEFAULT 'running',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP,
                    created_by TEXT DEFAULT 'system',
                    total_orders INTEGER,
                    total_vehicles INTEGER,
                    data_path TEXT -- JSON文件路径
                );
            """)

            # 创建车辆表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS vehicles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    experiment_id TEXT NOT NULL,
                    vehicle_id TEXT NOT NULL,
                    vehicle_type TEXT,
                    capacity_volume REAL,
                    capacity_weight REAL,
                    loading_efficiency REAL,
                    total_items INTEGER,
                    actual_volume REAL,
                    actual_weight REAL,
                    route_distance REAL,
                    route_duration REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (experiment_id) REFERENCES experiments (experiment_id)
                );
            """)

            # 创建性能指标表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS performance_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    experiment_id TEXT NOT NULL,
                    metric_name TEXT NOT NULL,
                    metric_value REAL NOT NULL,
                    metric_unit TEXT,
                    category TEXT, -- 'loading', 'routing', 'overall'
                    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (experiment_id) REFERENCES experiments (experiment_id)
                );
            """)

            # 创建优化运行记录表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS optimization_runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    experiment_id TEXT NOT NULL,
                    run_type TEXT NOT NULL, -- 'loading', 'routing', 'integrated'
                    algorithm TEXT NOT NULL,
                    status TEXT DEFAULT 'running',
                    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    end_time TIMESTAMP,
                    execution_time_seconds REAL,
                    success_rate REAL,
                    error_message TEXT,
                    result_summary TEXT, -- JSON格式
                    FOREIGN KEY (experiment_id) REFERENCES experiments (experiment_id)
                );
            """)

            # 创建索引
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_experiments_created_at ON experiments (created_at);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_vehicles_experiment_id ON vehicles (experiment_id);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_performance_experiment_id ON performance_metrics (experiment_id);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_optimization_experiment_id ON optimization_runs (experiment_id);")

            conn.commit()

    @contextmanager
    def get_connection(self):
        """获取数据库连接的上下文管理器"""
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # 支持字典式访问
            try:
                yield conn
            finally:
                conn.close()

    def create_experiment(self, name: str, description: str = None,
                         algorithm: str = "integrated", parameters: Dict = None,
                         created_by: str = "system") -> str:
        """
        创建新实验

        Args:
            name: 实验名称
            description: 实验描述
            algorithm: 算法名称
            parameters: 算法参数
            created_by: 创建者

        Returns:
            experiment_id: 实验ID
        """
        experiment_id = f"exp_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO experiments (experiment_id, name, description, algorithm,
                                       parameters, created_by)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (experiment_id, name, description, algorithm,
                  json.dumps(parameters) if parameters else None, created_by))
            conn.commit()

        self.logger.info(f"创建实验: {experiment_id}")
        return experiment_id

    def update_experiment_status(self, experiment_id: str, status: str,
                                total_orders: int = None, total_vehicles: int = None,
                                data_path: str = None):
        """更新实验状态"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            completed_at = datetime.now() if status == 'completed' else None

            cursor.execute("""
                UPDATE experiments
                SET status = ?, completed_at = ?, total_orders = ?,
                    total_vehicles = ?, data_path = ?
                WHERE experiment_id = ?
            """, (status, completed_at, total_orders, total_vehicles,
                  data_path, experiment_id))
            conn.commit()

    def add_vehicle_data(self, experiment_id: str, vehicle_data: Dict):
        """添加车辆数据"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO vehicles (
                    experiment_id, vehicle_id, vehicle_type, capacity_volume,
                    capacity_weight, loading_efficiency, total_items,
                    actual_volume, actual_weight, route_distance, route_duration
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                experiment_id,
                vehicle_data.get('vehicle_id'),
                vehicle_data.get('vehicle_type'),
                vehicle_data.get('capacity_volume'),
                vehicle_data.get('capacity_weight'),
                vehicle_data.get('loading_efficiency'),
                vehicle_data.get('total_items'),
                vehicle_data.get('actual_volume'),
                vehicle_data.get('actual_weight'),
                vehicle_data.get('route_distance'),
                vehicle_data.get('route_duration')
            ))
            conn.commit()

    def add_performance_metric(self, experiment_id: str, metric_name: str,
                              metric_value: float, metric_unit: str = None,
                              category: str = 'overall'):
        """添加性能指标"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO performance_metrics (
                    experiment_id, metric_name, metric_value, metric_unit, category
                ) VALUES (?, ?, ?, ?, ?)
            """, (experiment_id, metric_name, metric_value, metric_unit, category))
            conn.commit()

    def get_experiments(self, limit: int = 50, offset: int = 0,
                       created_by: str = None) -> List[Dict]:
        """获取实验列表"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            query = """
                SELECT e.*, COUNT(v.id) as vehicle_count,
                       COUNT(pm.id) as metrics_count
                FROM experiments e
                LEFT JOIN vehicles v ON e.experiment_id = v.experiment_id
                LEFT JOIN performance_metrics pm ON e.experiment_id = pm.experiment_id
            """
            params = []

            if created_by:
                query += " WHERE e.created_by = ?"
                params.append(created_by)

            query += """
                GROUP BY e.id
                ORDER BY e.created_at DESC
                LIMIT ? OFFSET ?
            """
            params.extend([limit, offset])

            cursor.execute(query, params)
            rows = cursor.fetchall()

            experiments = []
            for row in rows:
                exp = dict(row)
                if exp['parameters']:
                    exp['parameters'] = json.loads(exp['parameters'])
                experiments.append(exp)

            return experiments

    def get_experiment_detail(self, experiment_id: str) -> Optional[Dict]:
        """获取实验详细信息"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # 基本信息
            cursor.execute("SELECT * FROM experiments WHERE experiment_id = ?", (experiment_id,))
            exp_row = cursor.fetchone()

            if not exp_row:
                return None

            experiment = dict(exp_row)
            if experiment['parameters']:
                experiment['parameters'] = json.loads(experiment['parameters'])

            # 车辆信息
            cursor.execute("SELECT * FROM vehicles WHERE experiment_id = ?", (experiment_id,))
            experiment['vehicles'] = [dict(row) for row in cursor.fetchall()]

            # 性能指标
            cursor.execute("SELECT * FROM performance_metrics WHERE experiment_id = ?", (experiment_id,))
            experiment['metrics'] = [dict(row) for row in cursor.fetchall()]

            # 运行记录
            cursor.execute("SELECT * FROM optimization_runs WHERE experiment_id = ?", (experiment_id,))
            experiment['runs'] = [dict(row) for row in cursor.fetchall()]

            return experiment

    def get_performance_trends(self, metric_name: str, category: str = None,
                              days: int = 30) -> List[Dict]:
        """获取性能趋势数据"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            query = """
                SELECT e.experiment_id, e.name, e.created_at,
                       pm.metric_value, pm.metric_unit
                FROM performance_metrics pm
                JOIN experiments e ON pm.experiment_id = e.experiment_id
                WHERE pm.metric_name = ?
                AND e.created_at >= datetime('now', '-{} days')
            """.format(days)

            params = [metric_name]

            if category:
                query += " AND pm.category = ?"
                params.append(category)

            query += " ORDER BY e.created_at"

            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    def compare_experiments(self, experiment_ids: List[str]) -> Dict:
        """对比多个实验"""
        comparison_data = {}

        for exp_id in experiment_ids:
            exp_detail = self.get_experiment_detail(exp_id)
            if exp_detail:
                comparison_data[exp_id] = {
                    'name': exp_detail['name'],
                    'algorithm': exp_detail['algorithm'],
                    'created_at': exp_detail['created_at'],
                    'status': exp_detail['status'],
                    'vehicle_count': len(exp_detail['vehicles']),
                    'metrics': {m['metric_name']: m['metric_value']
                              for m in exp_detail['metrics']}
                }

        return comparison_data

    def delete_experiment(self, experiment_id: str) -> bool:
        """删除实验（谨慎使用）"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # 删除相关数据
            cursor.execute("DELETE FROM optimization_runs WHERE experiment_id = ?", (experiment_id,))
            cursor.execute("DELETE FROM performance_metrics WHERE experiment_id = ?", (experiment_id,))
            cursor.execute("DELETE FROM vehicles WHERE experiment_id = ?", (experiment_id,))
            cursor.execute("DELETE FROM experiments WHERE experiment_id = ?", (experiment_id,))

            conn.commit()
            return cursor.rowcount > 0

    def get_statistics(self) -> Dict:
        """获取总体统计信息"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            stats = {}

            # 实验统计
            cursor.execute("SELECT COUNT(*) as count FROM experiments")
            stats['total_experiments'] = cursor.fetchone()['count']

            cursor.execute("SELECT COUNT(*) as count FROM experiments WHERE status = 'completed'")
            stats['completed_experiments'] = cursor.fetchone()['count']

            # 车辆统计
            cursor.execute("SELECT COUNT(*) as count FROM vehicles")
            stats['total_vehicles'] = cursor.fetchone()['count']

            cursor.execute("SELECT AVG(loading_efficiency) as avg FROM vehicles WHERE loading_efficiency IS NOT NULL")
            result = cursor.fetchone()
            stats['avg_loading_efficiency'] = result['avg'] if result['avg'] else 0

            # 最近7天的实验数
            cursor.execute("SELECT COUNT(*) as count FROM experiments WHERE created_at >= datetime('now', '-7 days')")
            stats['recent_experiments'] = cursor.fetchone()['count']

            return stats

# 全局数据库管理器实例
db_manager = DatabaseManager()