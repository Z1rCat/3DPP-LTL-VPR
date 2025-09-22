"""
增强可视化测试脚本
Enhanced Visualization Test Script - 测试三种专业可视化功能
"""

import sys
from pathlib import Path
import logging
import time
from typing import Dict, List

# 添加项目路径
sys.path.append(str(Path(__file__).parent))

# 导入可视化模块
from visualization.enhanced_visualizer import EnhancedVisualizer
from visualization.advanced_route_visualizer import AdvancedRouteVisualizer

# 尝试导入配置，如果失败则使用默认配置
try:
    from config import VISUALIZATIONS_DIR
except ImportError:
    VISUALIZATIONS_DIR = Path(__file__).parent / "output" / "visualizations"

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class VisualizationTester:
    """可视化测试器"""

    def __init__(self):
        """初始化测试器"""
        self.enhanced_visualizer = EnhancedVisualizer()
        self.route_visualizer = AdvancedRouteVisualizer()
        self.results = {
            'single_category_3dpp': [],
            'multi_category_3dpp': [],
            'route_optimization': [],
            'additional_charts': []
        }

    def test_single_category_3dpp(self) -> List[str]:
        """测试单品类3DPP可视化"""
        logger.info("🔍 测试单品类3DPP可视化...")

        generated_files = []

        try:
            # 测试三种不同的货物类型
            cargo_types = ['食品', '酒水', '农产品']

            for cargo_type in cargo_types:
                logger.info(f"  创建 {cargo_type} 的单品类3DPP可视化")

                # 创建可视化
                fig = self.enhanced_visualizer.create_single_category_3dpp_visualization(
                    truck_data={}, cargo_type=cargo_type
                )

                # 保存文件
                files = self.enhanced_visualizer.save_visualization(
                    fig, f'single_category_3dpp_{cargo_type}',
                    save_formats=['html', 'png']
                )
                generated_files.extend(files)

                logger.info(f"    ✅ 已生成 {len(files)} 个文件")

            self.results['single_category_3dpp'] = generated_files
            logger.info(f"✅ 单品类3DPP可视化测试完成，共生成 {len(generated_files)} 个文件")

        except Exception as e:
            logger.error(f"❌ 单品类3DPP可视化测试失败: {e}")

        return generated_files

    def test_multi_category_3dpp(self) -> List[str]:
        """测试多品类3DPP可视化"""
        logger.info("🔍 测试多品类3DPP可视化...")

        generated_files = []

        try:
            # 创建多品类可视化
            fig = self.enhanced_visualizer.create_multi_category_3dpp_visualization(
                ltl_data={}
            )

            # 保存文件
            files = self.enhanced_visualizer.save_visualization(
                fig, 'multi_category_3dpp',
                save_formats=['html', 'png']
            )
            generated_files.extend(files)

            self.results['multi_category_3dpp'] = generated_files
            logger.info(f"✅ 多品类3DPP可视化测试完成，共生成 {len(generated_files)} 个文件")

        except Exception as e:
            logger.error(f"❌ 多品类3DPP可视化测试失败: {e}")

        return generated_files

    def test_route_optimization_visualization(self) -> List[str]:
        """测试路径优化可视化"""
        logger.info("🔍 测试路径优化可视化...")

        generated_files = []

        try:
            # 1. 测试基本路径优化可视化
            logger.info("  创建基本路径优化可视化")
            fig1 = self.enhanced_visualizer.create_route_optimization_visualization(
                route_data={}
            )
            files1 = self.enhanced_visualizer.save_visualization(
                fig1, 'basic_route_optimization',
                save_formats=['html']
            )
            generated_files.extend(files1)

            # 2. 测试专业VRP总览
            logger.info("  创建专业VRP总览")
            fig2 = self.route_visualizer.create_professional_vrp_visualization(
                route_solutions=None
            )
            file2 = self.route_visualizer.save_route_visualization(
                fig2, 'professional_vrp_overview'
            )
            generated_files.append(file2)

            # 3. 测试路径对比仪表板
            logger.info("  创建路径对比仪表板")
            fig3 = self.route_visualizer.create_route_comparison_dashboard(
                route_solutions=None
            )
            file3 = self.route_visualizer.save_route_visualization(
                fig3, 'route_comparison_dashboard'
            )
            generated_files.append(file3)

            # 4. 测试单车辆详细视图
            logger.info("  创建单车辆详细视图")
            fig4 = self.route_visualizer.create_single_vehicle_detailed_view(
                'SAMPLE_TRUCK', {'route_sequence': []}
            )
            file4 = self.route_visualizer.save_route_visualization(
                fig4, 'single_vehicle_detailed'
            )
            generated_files.append(file4)

            self.results['route_optimization'] = generated_files
            logger.info(f"✅ 路径优化可视化测试完成，共生成 {len(generated_files)} 个文件")

        except Exception as e:
            logger.error(f"❌ 路径优化可视化测试失败: {e}")

        return generated_files

    def test_additional_analysis_charts(self) -> List[str]:
        """测试附加分析图表"""
        logger.info("🔍 测试附加分析图表...")

        generated_files = []

        try:
            # 创建附加分析图表
            analysis_figs = self.enhanced_visualizer._create_comprehensive_analysis()

            for i, fig in enumerate(analysis_figs):
                files = self.enhanced_visualizer.save_visualization(
                    fig, f'analysis_chart_{i+1}',
                    save_formats=['html', 'png']
                )
                generated_files.extend(files)

            self.results['additional_charts'] = generated_files
            logger.info(f"✅ 附加分析图表测试完成，共生成 {len(generated_files)} 个文件")

        except Exception as e:
            logger.error(f"❌ 附加分析图表测试失败: {e}")

        return generated_files

    def run_comprehensive_test(self) -> Dict[str, List[str]]:
        """运行综合测试"""
        logger.info("🚀 开始综合可视化测试...")

        start_time = time.time()

        # 确保输出目录存在
        VISUALIZATIONS_DIR.mkdir(parents=True, exist_ok=True)

        try:
            # 1. 测试单品类3DPP可视化
            self.test_single_category_3dpp()

            # 2. 测试多品类3DPP可视化
            self.test_multi_category_3dpp()

            # 3. 测试路径优化可视化
            self.test_route_optimization_visualization()

            # 4. 测试附加分析图表
            self.test_additional_analysis_charts()

            # 计算总体统计
            total_files = sum(len(files) for files in self.results.values())
            elapsed_time = time.time() - start_time

            logger.info("="*60)
            logger.info("🎉 综合可视化测试完成!")
            logger.info(f"⏱️  总用时: {elapsed_time:.2f} 秒")
            logger.info(f"📁 总文件数: {total_files} 个")
            logger.info("="*60)

            # 详细结果报告
            logger.info("📊 详细结果报告:")
            for category, files in self.results.items():
                logger.info(f"  {category}: {len(files)} 个文件")
                for file_path in files:
                    logger.info(f"    📄 {file_path}")

            logger.info("="*60)
            logger.info("💡 使用说明:")
            logger.info("  1. 打开浏览器")
            logger.info(f"  2. 导航到输出目录: {VISUALIZATIONS_DIR}")
            logger.info("  3. 双击HTML文件查看交互式可视化")
            logger.info("  4. PNG文件可直接查看静态图片")
            logger.info("="*60)

        except Exception as e:
            logger.error(f"❌ 综合测试失败: {e}")

        return self.results

    def create_test_summary_report(self) -> str:
        """创建测试摘要报告"""
        logger.info("📋 创建测试摘要报告...")

        try:
            # 生成摘要报告
            total_files = sum(len(files) for files in self.results.values())
            timestamp = time.strftime("%Y%m%d_%H%M%S")

            report_content = f"""
# 增强可视化测试报告
## Enhanced Visualization Test Report

**生成时间**: {time.strftime("%Y-%m-%d %H:%M:%S")}
**测试版本**: Enhanced Visualization v2.0

## 📊 测试概览

- **总文件数**: {total_files} 个
- **测试类别**: {len(self.results)} 种
- **输出目录**: {VISUALIZATIONS_DIR}

## 🔍 详细结果

### 1. 单品类3DPP可视化 (Single-Item 3DPP)
- **功能**: 清晰展示同一种货物的高效密集堆叠
- **特色**: 专业色板、3D光照、悬停信息、空间利用率分析
- **文件数**: {len(self.results.get('single_category_3dpp', []))} 个
"""

            for file_path in self.results.get('single_category_3dpp', []):
                report_content += f"  - {Path(file_path).name}\n"

            report_content += f"""
### 2. 多品类3DPP可视化 (Multi-Item LTL 3DPP)
- **功能**: 直观区分和展示不同种类货物的混合摆放
- **特色**: 按类型颜色编码、图例交互、点击过滤、装载分析
- **文件数**: {len(self.results.get('multi_category_3dpp', []))} 个
"""

            for file_path in self.results.get('multi_category_3dpp', []):
                report_content += f"  - {Path(file_path).name}\n"

            report_content += f"""
### 3. 路径优化结果可视化 (VRP Result)
- **功能**: 在地图上清晰展示车辆最佳行驶路线和停靠点
- **特色**: 真实地图背景、图标区分、悬停信息、路径统计
- **文件数**: {len(self.results.get('route_optimization', []))} 个
"""

            for file_path in self.results.get('route_optimization', []):
                report_content += f"  - {Path(file_path).name}\n"

            report_content += f"""
### 4. 附加分析图表
- **功能**: 综合分析和统计图表
- **特色**: 3D效率分析、装载密度热力图
- **文件数**: {len(self.results.get('additional_charts', []))} 个
"""

            for file_path in self.results.get('additional_charts', []):
                report_content += f"  - {Path(file_path).name}\n"

            report_content += """
## ✨ 设计亮点

### 统一设计语言
- **专业色板**: 使用Plotly3、viridis、cividis等和谐色板
- **3D光照与材质**: 调整光照参数和物体材质，提升真实感
- **悬停信息**: 精心设计的鼠标悬停信息框
- **图例与标题**: 明确的标题和必要的图例说明
- **一致性**: 三种图表在颜色、字体、布局风格上保持一致

### 交互功能
- **3D旋转与缩放**: 用户可从任何角度审视装载方案
- **点击过滤**: 在多品类可视化中点击图例可隐藏/显示对应类型
- **详细信息**: 悬停显示货物详细信息和统计数据
- **地图导航**: 路径可视化支持地图缩放、平移等操作

## 🔧 技术特色

1. **高性能渲染**: 使用Plotly的高效3D渲染引擎
2. **响应式设计**: 支持不同屏幕尺寸和设备
3. **数据驱动**: 基于真实的物流优化数据结构
4. **可扩展性**: 模块化设计，易于扩展新功能

## 📝 使用建议

1. **浏览器兼容性**: 推荐使用Chrome、Firefox、Edge等现代浏览器
2. **性能优化**: 大数据量时建议使用简化显示模式
3. **交互操作**: 充分利用悬停、点击、缩放等交互功能
4. **数据准备**: 确保输入数据格式符合规范

---
*报告由增强可视化测试系统自动生成*
"""

            # 保存报告
            report_file = VISUALIZATIONS_DIR / f"visualization_test_report_{timestamp}.md"
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(report_content)

            logger.info(f"📋 测试摘要报告已保存: {report_file}")
            return str(report_file)

        except Exception as e:
            logger.error(f"❌ 创建测试报告失败: {e}")
            return ""


def main():
    """主测试函数"""
    print("="*60)
    print("Enhanced Visualization Test System")
    print("="*60)

    # 创建测试器
    tester = VisualizationTester()

    # 运行综合测试
    results = tester.run_comprehensive_test()

    # 创建测试报告
    report_file = tester.create_test_summary_report()

    print("\nTest completed!")
    print(f"Report: {report_file}")
    print(f"Output directory: {VISUALIZATIONS_DIR}")

    return results


if __name__ == "__main__":
    main()