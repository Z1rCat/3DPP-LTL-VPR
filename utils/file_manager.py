"""
文件管理工具模块
File Management Utilities for LTL Logistics Optimization
"""

import pandas as pd
import pickle
import json
import logging
from typing import Dict, List, Tuple, Optional, Any
from pathlib import Path
import shutil
from datetime import datetime
import openpyxl
from openpyxl.styles import Font, PatternFill, Border, Side, Alignment

# 导入配置
import sys
sys.path.append(str(Path(__file__).parent.parent))
from config import (REPORTS_DIR, VISUALIZATIONS_DIR, INTERMEDIATE_DIR, LOGS_DIR,
                   REPORT_CONFIG, TRUCK_SPECS)


class FileManager:
    """文件管理器类"""

    def __init__(self):
        """初始化文件管理器"""
        self.logger = self._setup_logger()
        self.report_config = REPORT_CONFIG

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

    def manage_output_directories(self):
        """管理输出目录结构"""
        directories = [REPORTS_DIR, VISUALIZATIONS_DIR, INTERMEDIATE_DIR, LOGS_DIR]

        for directory in directories:
            try:
                directory.mkdir(parents=True, exist_ok=True)
                self.logger.debug(f"确保目录存在: {directory}")
            except Exception as e:
                self.logger.error(f"创建目录失败 {directory}: {str(e)}")
                raise

        self.logger.info("输出目录结构管理完成")

    def save_excel_report(self, solution: Dict, output_file: Optional[str] = None) -> str:
        """
        生成并保存完整的Excel报告

        Args:
            solution: 完整求解结果
            output_file: 输出文件路径

        Returns:
            str: 保存的文件路径
        """
        if output_file is None:
            output_file = REPORTS_DIR / self.report_config['excel_file_name']

        self.logger.info(f"生成Excel报告: {output_file}")

        try:
            with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
                # 1. 装载方案摘要
                self._write_summary_sheet(writer, solution)

                # 2. 车辆分配详情
                self._write_trucks_sheet(writer, solution)

                # 3. 货物装载详情
                self._write_packages_sheet(writer, solution)

                # 4. 未装载货物
                self._write_unloaded_sheet(writer, solution)

            # 格式化Excel文件
            self._format_excel_file(output_file)

            self.logger.info(f"Excel报告已保存到: {output_file}")
            return str(output_file)

        except Exception as e:
            self.logger.error(f"生成Excel报告失败: {str(e)}")
            raise

    def _write_summary_sheet(self, writer: pd.ExcelWriter, solution: Dict):
        """写入装载方案摘要工作表"""
        # 基本统计信息
        total_items = len(solution['loaded_items']) + len(solution['unloaded_items'])
        loaded_items = len(solution['loaded_items'])
        unloaded_items = len(solution['unloaded_items'])
        trucks_used = solution['trucks_used']
        total_volume = solution['total_loaded_volume']
        loading_efficiency = solution['loading_efficiency']

        # 准备摘要数据
        summary_data = {
            '指标': [
                '总货物数量',
                '成功装载',
                '未装载',
                '装载成功率',
                '使用货车数量',
                '总装载体积(m³)',
                '平均装载效率',
                '总车辆容量(m³)',
                '车队利用率',
                '系统运行时间',
                '报告生成时间'
            ],
            '数值': [
                total_items,
                loaded_items,
                unloaded_items,
                f"{loaded_items/total_items*100:.1f}%" if total_items > 0 else "0%",
                trucks_used,
                f"{total_volume:.6f}",
                f"{loading_efficiency:.1%}",
                f"{trucks_used * TRUCK_SPECS['volume']:.3f}",
                f"{total_volume/(trucks_used * TRUCK_SPECS['volume'])*100:.1f}%" if trucks_used > 0 else "0%",
                "完成",  # 可以传入实际运行时间
                datetime.now().strftime(self.report_config['date_format'])
            ]
        }

        summary_df = pd.DataFrame(summary_data)
        summary_df.to_excel(writer, sheet_name=self.report_config['summary_sheet'],
                          index=False, startrow=1)

        # 添加标题行
        worksheet = writer.sheets[self.report_config['summary_sheet']]
        worksheet['A1'] = '零担物流3D装箱优化 - 结果摘要'

    def _write_trucks_sheet(self, writer: pd.ExcelWriter, solution: Dict):
        """写入车辆分配详情工作表"""
        truck_data = []

        for truck_id, items in solution['truck_assignments'].items():
            total_volume = sum(item['volume'] for item in items)
            total_weight = sum(item['weight'] for item in items)
            item_count = len(items)
            loading_efficiency = total_volume / TRUCK_SPECS['volume'] * 100

            # 货物类型统计
            type_counts = {}
            for item in items:
                item_type = item['item_type']
                type_counts[item_type] = type_counts.get(item_type, 0) + 1

            type_summary = '; '.join([f"{t}×{c}" for t, c in type_counts.items()])

            truck_data.append({
                '货车ID': truck_id,
                '装载货物数量': item_count,
                '装载体积(m³)': f"{total_volume:.6f}",
                '装载重量(kg)': f"{total_weight:.2f}",
                '装载效率': f"{loading_efficiency:.1f}%",
                '货物类型分布': type_summary,
                '平均单件体积(m³)': f"{total_volume/item_count:.6f}" if item_count > 0 else "0",
                '体积利用状态': '良好' if loading_efficiency > 60 else '一般' if loading_efficiency > 30 else '较低'
            })

        trucks_df = pd.DataFrame(truck_data)
        trucks_df.to_excel(writer, sheet_name=self.report_config['trucks_sheet'],
                         index=False)

    def _write_packages_sheet(self, writer: pd.ExcelWriter, solution: Dict):
        """写入货物装载详情工作表"""
        package_data = []

        for item in solution['loaded_items']:
            x, y, z = item['position']
            L, W, H = item['dimensions']

            package_data.append({
                '货物ID': item['item_id'],
                '货车ID': item['truck_id'],
                '货物类型': item['item_type'],
                '体积(m³)': f"{item['volume']:.6f}",
                '重量(kg)': f"{item['weight']:.2f}",
                '位置X(m)': f"{x:.4f}",
                '位置Y(m)': f"{y:.4f}",
                '位置Z(m)': f"{z:.4f}",
                '长度(m)': f"{L:.4f}",
                '宽度(m)': f"{W:.4f}",
                '高度(m)': f"{H:.4f}",
                '方向编号': item['orientation'],
                '装载时间': datetime.now().strftime(self.report_config['date_format'])
            })

        packages_df = pd.DataFrame(package_data)
        packages_df.to_excel(writer, sheet_name=self.report_config['packages_sheet'],
                           index=False)

    def _write_unloaded_sheet(self, writer: pd.ExcelWriter, solution: Dict):
        """写入未装载货物工作表"""
        unloaded_data = []

        for item in solution['unloaded_items']:
            unloaded_data.append({
                '货物ID': item['item_id'],
                '货物类型': item['item_type'],
                '体积(m³)': f"{item['volume']:.6f}",
                '重量(kg)': f"{item['weight']:.2f}",
                '未装载原因': item['reason'],
                '建议处理方式': '增加车辆' if item['reason'] == '未分配' else '检查货物规格'
            })

        if unloaded_data:
            unloaded_df = pd.DataFrame(unloaded_data)
            unloaded_df.to_excel(writer, sheet_name=self.report_config['unloaded_sheet'],
                               index=False)
        else:
            # 创建空的未装载工作表
            empty_df = pd.DataFrame(columns=['货物ID', '货物类型', '体积(m³)', '重量(kg)', '未装载原因', '建议处理方式'])
            empty_df.to_excel(writer, sheet_name=self.report_config['unloaded_sheet'],
                            index=False)

    def _format_excel_file(self, file_path: Path):
        """格式化Excel文件样式"""
        try:
            workbook = openpyxl.load_workbook(file_path)

            # 定义样式
            header_font = Font(bold=True, color="FFFFFF")
            header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
            border = Border(
                left=Side(style='thin'),
                right=Side(style='thin'),
                top=Side(style='thin'),
                bottom=Side(style='thin')
            )
            center_alignment = Alignment(horizontal='center', vertical='center')

            # 格式化每个工作表
            for sheet_name in workbook.sheetnames:
                worksheet = workbook[sheet_name]

                # 获取数据范围
                max_row = worksheet.max_row
                max_col = worksheet.max_column

                # 格式化标题行 (如果存在数据)
                if max_row > 1:
                    for col in range(1, max_col + 1):
                        cell = worksheet.cell(row=2 if sheet_name == self.report_config['summary_sheet'] else 1, column=col)
                        cell.font = header_font
                        cell.fill = header_fill
                        cell.alignment = center_alignment
                        cell.border = border

                # 应用边框和居中对齐
                for row in range(1, max_row + 1):
                    for col in range(1, max_col + 1):
                        cell = worksheet.cell(row=row, column=col)
                        cell.border = border
                        if row > (2 if sheet_name == self.report_config['summary_sheet'] else 1):
                            cell.alignment = center_alignment

                # 自动调整列宽
                for column in worksheet.columns:
                    max_length = 0
                    column_letter = column[0].column_letter

                    for cell in column:
                        try:
                            if len(str(cell.value)) > max_length:
                                max_length = len(str(cell.value))
                        except:
                            pass

                    adjusted_width = min(max_length + 2, 50)  # 限制最大宽度
                    worksheet.column_dimensions[column_letter].width = adjusted_width

            workbook.save(file_path)
            self.logger.info("Excel文件格式化完成")

        except Exception as e:
            self.logger.warning(f"Excel格式化失败，但文件已保存: {str(e)}")

    def save_solution_data(self, solution: Dict, metadata: Optional[Dict] = None,
                          output_file: Optional[str] = None) -> str:
        """
        保存完整的求解结果数据

        Args:
            solution: 求解结果
            metadata: 元数据
            output_file: 输出文件路径

        Returns:
            str: 保存的文件路径
        """
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = INTERMEDIATE_DIR / f"final_solution_{timestamp}.pkl"

        solution_package = {
            'solution': solution,
            'metadata': metadata or {
                'save_timestamp': datetime.now().isoformat(),
                'system_version': '1.0.0'
            },
            'config_snapshot': {
                'truck_specs': TRUCK_SPECS,
                'report_config': REPORT_CONFIG
            }
        }

        with open(output_file, 'wb') as f:
            pickle.dump(solution_package, f)

        self.logger.info(f"完整求解结果已保存到: {output_file}")
        return str(output_file)

    def create_project_archive(self, archive_name: Optional[str] = None) -> str:
        """
        创建项目结果归档

        Args:
            archive_name: 归档文件名

        Returns:
            str: 归档文件路径
        """
        if archive_name is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            archive_name = f"logistics_optimization_results_{timestamp}"

        archive_dir = REPORTS_DIR / archive_name
        archive_dir.mkdir(exist_ok=True)

        try:
            # 复制报告文件
            if REPORTS_DIR.exists():
                reports_dest = archive_dir / "reports"
                reports_dest.mkdir(exist_ok=True)
                for file_path in REPORTS_DIR.glob("*.xlsx"):
                    if file_path != archive_dir:  # 避免复制自己
                        shutil.copy2(file_path, reports_dest)

            # 复制可视化文件
            if VISUALIZATIONS_DIR.exists():
                viz_dest = archive_dir / "visualizations"
                viz_dest.mkdir(exist_ok=True)
                for file_path in VISUALIZATIONS_DIR.glob("*.html"):
                    shutil.copy2(file_path, viz_dest)

            # 复制关键中间文件
            intermediate_dest = archive_dir / "intermediate"
            intermediate_dest.mkdir(exist_ok=True)
            key_files = ['processed_items.pkl', 'gurobi_solution.pkl', 'preprocessing_statistics.txt']
            for filename in key_files:
                source_file = INTERMEDIATE_DIR / filename
                if source_file.exists():
                    shutil.copy2(source_file, intermediate_dest)

            # 创建归档说明文件
            readme_path = archive_dir / "README.txt"
            self._create_archive_readme(readme_path)

            self.logger.info(f"项目归档已创建: {archive_dir}")
            return str(archive_dir)

        except Exception as e:
            self.logger.error(f"创建项目归档失败: {str(e)}")
            raise

    def _create_archive_readme(self, readme_path: Path):
        """创建归档说明文件"""
        readme_content = f"""
零担物流3D装箱优化系统 - 结果归档
========================================

生成时间: {datetime.now().strftime(self.report_config['date_format'])}
系统版本: 1.0.0

目录结构说明:
├── reports/          # Excel报告文件
│   └── Final_Loading_Plan.xlsx    # 完整装载方案报告
├── visualizations/   # 3D可视化HTML文件
│   ├── TRUCK_XXX_visualization.html  # 各货车装载可视化
│   ├── fleet_summary.html           # 车队摘要仪表板
│   └── cargo_type_analysis.html     # 货物类型分析
└── intermediate/     # 中间处理文件
    ├── processed_items.pkl          # 预处理货物数据
    ├── gurobi_solution.pkl          # Gurobi求解结果
    └── preprocessing_statistics.txt  # 数据预处理统计

使用说明:
1. 查看 Final_Loading_Plan.xlsx 了解详细的装载方案
2. 在浏览器中打开 visualizations/ 目录下的HTML文件查看3D可视化
3. intermediate/ 目录包含系统运行的中间数据，可用于进一步分析

技术参数:
- 标准货车规格: {TRUCK_SPECS['length']}m × {TRUCK_SPECS['width']}m × {TRUCK_SPECS['height']}m
- 货车容量: {TRUCK_SPECS['volume']}m³
- 优化引擎: Gurobi MILP求解器
- 可视化引擎: Plotly 3D

注意事项:
- HTML可视化文件需要在现代浏览器中打开
- 建议使用Chrome、Firefox或Edge浏览器获得最佳体验
- 大型装载方案的3D可视化可能需要较长加载时间

技术支持:
本系统基于Gurobi数学优化和Plotly可视化技术构建
如有技术问题，请检查系统日志或联系技术支持
"""

        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(readme_content)

    def clean_temporary_files(self, keep_final_results: bool = True):
        """
        清理临时文件

        Args:
            keep_final_results: 是否保留最终结果
        """
        try:
            if not keep_final_results:
                # 清理所有中间文件
                temp_patterns = ['*.tmp', '*.log', '*_temp.pkl']
                for pattern in temp_patterns:
                    for temp_file in INTERMEDIATE_DIR.glob(pattern):
                        temp_file.unlink()
                        self.logger.debug(f"删除临时文件: {temp_file}")

            self.logger.info("临时文件清理完成")

        except Exception as e:
            self.logger.warning(f"清理临时文件时出错: {str(e)}")


def main():
    """测试文件管理器"""
    file_manager = FileManager()

    try:
        # 管理目录
        file_manager.manage_output_directories()

        # 加载解决方案（如果存在）
        solution_file = INTERMEDIATE_DIR / "gurobi_solution.pkl"
        if solution_file.exists():
            with open(solution_file, 'rb') as f:
                solution = pickle.load(f)

            # 生成Excel报告
            excel_path = file_manager.save_excel_report(solution)
            print(f"Excel报告已生成: {excel_path}")

            # 保存解决方案数据
            solution_path = file_manager.save_solution_data(solution)
            print(f"求解结果已保存: {solution_path}")

            # 创建项目归档
            archive_path = file_manager.create_project_archive()
            print(f"项目归档已创建: {archive_path}")

        else:
            print("未找到求解结果文件，跳过报告生成")

        print("文件管理器测试完成!")

    except Exception as e:
        print(f"文件管理器测试失败: {str(e)}")


if __name__ == "__main__":
    main()