"""
真实数据可视化测试脚本
Test script for real data visualizations
"""

import sys
from pathlib import Path
import logging
import time
from datetime import datetime

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent))

# 导入可视化模块
from visualization.enhanced_visualizer import EnhancedVisualizer
from visualization.advanced_route_visualizer import AdvancedRouteVisualizer
from visualization.real_data_loader import RealDataLoader

def setup_logger():
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

def test_enhanced_visualizer_with_real_data():
    """测试增强可视化器使用真实数据"""
    logger = setup_logger()
    logger.info("=== 测试增强可视化器使用真实数据 ===")

    try:
        # 初始化可视化器
        visualizer = EnhancedVisualizer()
        results = {}

        # 1. 测试单品类3DPP可视化
        logger.info("测试单品类3DPP可视化...")
        available_cargo_types = visualizer.real_data_loader.get_available_cargo_types()

        if available_cargo_types:
            logger.info(f"发现可用货物类型: {available_cargo_types}")
            for cargo_type in available_cargo_types:
                try:
                    fig = visualizer.create_single_category_3dpp_visualization({}, cargo_type)
                    files = visualizer.save_visualization(fig, f'single_category_3dpp_{cargo_type}')
                    results[f'single_{cargo_type}'] = files
                    logger.info(f"成功创建 {cargo_type} 单品类可视化: {len(files)} 个文件")
                except Exception as e:
                    logger.error(f"创建 {cargo_type} 单品类可视化失败: {e}")
        else:
            logger.warning("未找到可用货物类型，使用默认类型")
            for cargo_type in ['食品', '酒水', '农产品']:
                try:
                    fig = visualizer.create_single_category_3dpp_visualization({}, cargo_type)
                    files = visualizer.save_visualization(fig, f'single_category_3dpp_{cargo_type}')
                    results[f'single_{cargo_type}'] = files
                    logger.info(f"成功创建 {cargo_type} 单品类可视化: {len(files)} 个文件")
                except Exception as e:
                    logger.error(f"创建 {cargo_type} 单品类可视化失败: {e}")

        # 2. 测试多品类3DPP可视化
        logger.info("测试多品类3DPP可视化...")
        try:
            fig = visualizer.create_multi_category_3dpp_visualization({})
            files = visualizer.save_visualization(fig, 'multi_category_3dpp')
            results['multi_category'] = files
            logger.info(f"成功创建多品类可视化: {len(files)} 个文件")
        except Exception as e:
            logger.error(f"创建多品类可视化失败: {e}")
            results['multi_category'] = []

        # 3. 测试路径优化可视化（使用enhanced_visualizer的方法）
        logger.info("测试路径优化可视化...")
        try:
            fig = visualizer.create_route_optimization_visualization({})
            files = visualizer.save_visualization(fig, 'basic_route_optimization')
            results['basic_route'] = files
            logger.info(f"成功创建基础路径可视化: {len(files)} 个文件")
        except Exception as e:
            logger.error(f"创建基础路径可视化失败: {e}")
            results['basic_route'] = []

        return results

    except Exception as e:
        logger.error(f"增强可视化器测试失败: {e}")
        return {}

def test_advanced_route_visualizer_with_real_data():
    """测试高级路径可视化器使用真实数据"""
    logger = setup_logger()
    logger.info("=== 测试高级路径可视化器使用真实数据 ===")

    try:
        # 初始化高级路径可视化器
        route_visualizer = AdvancedRouteVisualizer()

        # 创建所有路径可视化
        generated_files = route_visualizer.create_all_route_visualizations()

        logger.info(f"高级路径可视化完成，生成 {len(generated_files)} 个文件")
        return generated_files

    except Exception as e:
        logger.error(f"高级路径可视化器测试失败: {e}")
        return []

def test_data_loader_directly():
    """直接测试数据加载器"""
    logger = setup_logger()
    logger.info("=== 直接测试数据加载器 ===")

    try:
        loader = RealDataLoader()

        # 测试获取统计信息
        stats = loader.get_system_statistics()
        logger.info(f"系统统计: {stats}")

        # 测试获取可用货物类型
        cargo_types = loader.get_available_cargo_types()
        logger.info(f"可用货物类型: {cargo_types}")

        # 测试加载单品类数据
        if cargo_types:
            for cargo_type in cargo_types[:2]:  # 只测试前两种
                data = loader.get_single_category_data(cargo_type)
                if data:
                    logger.info(f"{cargo_type} 单品类数据: {len(data)} 个货物")
                else:
                    logger.warning(f"{cargo_type} 无单品类数据")

        # 测试加载多品类数据
        multi_data = loader.get_multi_category_data()
        if multi_data:
            logger.info(f"多品类数据: {len(multi_data)} 个货物")
        else:
            logger.warning("无多品类数据")

        # 测试加载路径数据
        route_data = loader.get_route_optimization_data()
        if route_data and route_data.get('route_solutions'):
            logger.info(f"路径数据: {len(route_data['route_solutions'])} 个车辆路径")
        else:
            logger.warning("无路径数据")

        return True

    except Exception as e:
        logger.error(f"数据加载器测试失败: {e}")
        return False

def generate_test_report(enhanced_results, route_files, data_loader_success):
    """生成测试报告"""
    logger = setup_logger()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = Path(__file__).parent / "output" / "visualizations" / f"visualization_test_report_{timestamp}.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)

    # 统计文件数量
    total_enhanced_files = sum(len(files) for files in enhanced_results.values())
    total_route_files = len(route_files)
    total_files = total_enhanced_files + total_route_files

    # 生成报告内容
    report_content = f"""# 真实数据可视化测试报告

**测试时间**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**总生成文件数**: {total_files}

## 测试概览

### 📊 增强可视化器测试结果
- **总文件数**: {total_enhanced_files}
- **测试状态**: {'✅ 成功' if enhanced_results else '❌ 失败'}

#### 详细结果:
"""

    for category, files in enhanced_results.items():
        report_content += f"\n**{category}**:\n"
        if files:
            for file_path in files:
                file_name = Path(file_path).name
                report_content += f"- ✅ {file_name}\n"
        else:
            report_content += "- ❌ 未生成文件\n"

    report_content += f"""

### 🗺️ 高级路径可视化器测试结果
- **总文件数**: {total_route_files}
- **测试状态**: {'✅ 成功' if route_files else '❌ 失败'}

#### 详细结果:
"""

    if route_files:
        for file_path in route_files:
            file_name = Path(file_path).name
            report_content += f"- ✅ {file_name}\n"
    else:
        report_content += "- ❌ 未生成文件\n"

    report_content += f"""

### 📁 数据加载器测试结果
- **测试状态**: {'✅ 成功' if data_loader_success else '❌ 失败'}

## 文件位置

所有生成的可视化文件保存在: `output/visualizations/`

## 使用说明

1. 打开任意 `.html` 文件在浏览器中查看可视化效果
2. 可视化包含交互功能，可以缩放、旋转、悬停查看详细信息
3. 如需PNG格式，需要安装 kaleido 包: `pip install kaleido`

## 技术说明

- 优先使用真实数据，如果真实数据不可用则回退到示例数据
- 三种可视化类型全部实现：单品类3DPP、多品类3DPP、路径优化
- 支持专业色板和3D光照效果
- 包含详细的悬停信息和图例

---
*报告生成时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}*
"""

    # 保存报告
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report_content)

    logger.info(f"测试报告已保存: {report_path}")
    return str(report_path)

def main():
    """主测试函数"""
    print("=" * 60)
    print("真实数据可视化综合测试开始")
    print("=" * 60)

    start_time = time.time()

    # 1. 测试数据加载器
    print("\n[1/4] 测试数据加载器...")
    data_loader_success = test_data_loader_directly()

    # 2. 测试增强可视化器
    print("\n[2/4] 测试增强可视化器...")
    enhanced_results = test_enhanced_visualizer_with_real_data()

    # 3. 测试高级路径可视化器
    print("\n[3/4] 测试高级路径可视化器...")
    route_files = test_advanced_route_visualizer_with_real_data()

    # 4. 生成测试报告
    print("\n[4/4] 生成测试报告...")
    report_path = generate_test_report(enhanced_results, route_files, data_loader_success)

    # 显示测试结果
    end_time = time.time()
    duration = end_time - start_time

    total_enhanced_files = sum(len(files) for files in enhanced_results.values())
    total_route_files = len(route_files)
    total_files = total_enhanced_files + total_route_files

    print("\n" + "=" * 60)
    print("真实数据可视化测试完成!")
    print("=" * 60)
    print(f"测试耗时: {duration:.2f} 秒")
    print(f"增强可视化: {total_enhanced_files} 个文件")
    print(f"路径可视化: {total_route_files} 个文件")
    print(f"总计文件: {total_files} 个")
    print(f"测试报告: {report_path}")
    print("\n请在浏览器中打开 HTML 文件查看可视化效果!")

    # 列出所有生成的文件
    if enhanced_results or route_files:
        print("\n生成的文件列表:")

        for category, files in enhanced_results.items():
            if files:
                print(f"\n{category}:")
                for file_path in files:
                    print(f"  - {Path(file_path).name}")

        if route_files:
            print(f"\n路径可视化:")
            for file_path in route_files:
                print(f"  - {Path(file_path).name}")

if __name__ == "__main__":
    main()