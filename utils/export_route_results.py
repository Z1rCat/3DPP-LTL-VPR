"""
导出所有车辆路径优化结果到Excel表
"""

import json
import pandas as pd
from pathlib import Path
import logging
from datetime import datetime

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def standardize_vehicle_id(vehicle_id: str) -> str:
    """标准化vehicle_id为3位数格式"""
    if 'LARGE_TRUCK_' in vehicle_id:
        # 提取数字部分：LARGE_TRUCK_00 -> 00 -> 000
        number = vehicle_id.split('_')[-1]
        return f"LARGE_TRUCK_{int(number):03d}"
    elif 'LTL_TRUCK_' in vehicle_id:
        # 提取数字部分：LTL_TRUCK_00 -> 00 -> 000
        number = vehicle_id.split('_')[-1]
        return f"LTL_TRUCK_{int(number):03d}"
    else:
        return vehicle_id

def load_route_plan(file_path):
    """加载路径规划JSON文件"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.warning(f"文件不存在: {file_path}")
        return None
    except Exception as e:
        logger.error(f"加载文件失败 {file_path}: {e}")
        return None

def export_route_summary_to_excel():
    """导出路径优化汇总结果到Excel"""
    
    # 输出目录
    output_dir = Path("output/reports")
    
    # 所有车辆ID列表
    all_vehicles = [
        'LARGE_TRUCK_00', 'LARGE_TRUCK_01', 'LARGE_TRUCK_02', 'LARGE_TRUCK_03',
        'LARGE_TRUCK_04', 'LARGE_TRUCK_05', 'LARGE_TRUCK_06', 'LARGE_TRUCK_07',
        'LTL_TRUCK_00', 'LTL_TRUCK_01', 'LTL_TRUCK_02', 'LTL_TRUCK_03'
    ]
    
    # 汇总数据
    summary_data = []
    detailed_routes = []
    
    for vehicle_id in all_vehicles:
        standardized_vehicle_id = standardize_vehicle_id(vehicle_id)
        route_file = output_dir / f"{standardized_vehicle_id}_route_plan.json"
        route_data = load_route_plan(route_file)
        
        if route_data:
            # 有路径规划数据
            summary = route_data.get('summary', {})
            summary_data.append({
                '车辆ID': vehicle_id,
                '车辆类型': route_data.get('route_details', {}).get('vehicle_info', {}).get('type', '未知'),
                '优化状态': '成功',
                '总距离(km)': summary.get('total_distance_km', 0),
                '总时长(小时)': summary.get('total_duration_hours', 0),
                '燃油成本(元)': summary.get('fuel_cost_yuan', 0),
                '停靠点数': summary.get('total_stops', 0),
                '取货点数': summary.get('pickup_stops', 0),
                '送货点数': summary.get('delivery_stops', 0),
                '初始载重(kg)': summary.get('initial_load_kg', 0),
                '最终载重(kg)': summary.get('final_load_kg', 0),
                '载重效率(%)': summary.get('load_efficiency', 0),
                '优化算法': summary.get('optimization_algorithm', '未知'),
                '解状态': summary.get('solution_status', '未知'),
                '开始时间': summary.get('start_time', ''),
                '完成时间': summary.get('completion_time', ''),
                '工作时长(小时)': summary.get('working_hours', 0)
            })
            
            # 详细路径数据
            for stop in route_data.get('itinerary', []):
                detailed_routes.append({
                    '车辆ID': vehicle_id,
                    '步骤': stop.get('step', 0),
                    '操作': stop.get('action', ''),
                    '订单ID': stop.get('order_id', ''),
                    '纬度': stop.get('coordinates', [0, 0])[0],
                    '经度': stop.get('coordinates', [0, 0])[1],
                    '重量变化(kg)': stop.get('weight_change_kg', 0),
                    '累计载重(kg)': stop.get('cumulative_load_kg', 0),
                    '距离(km)': stop.get('distance_from_previous_km', 0),
                    '预计到达': stop.get('estimated_arrival', ''),
                    '服务时间(分钟)': stop.get('service_time_minutes', 0),
                    '离开时间': stop.get('departure_time', ''),
                    '地址': stop.get('address', '')
                })
        else:
            # 无路径规划数据
            summary_data.append({
                '车辆ID': vehicle_id,
                '车辆类型': '大型货车' if 'LARGE' in vehicle_id else 'LTL货车',
                '优化状态': '失败',
                '总距离(km)': 0,
                '总时长(小时)': 0,
                '燃油成本(元)': 0,
                '停靠点数': 0,
                '取货点数': 0,
                '送货点数': 0,
                '初始载重(kg)': 0,
                '最终载重(kg)': 0,
                '载重效率(%)': 0,
                '优化算法': '无解',
                '解状态': '无有效路径解',
                '开始时间': '',
                '完成时间': '',
                '工作时长(小时)': 0
            })
    
    # 创建DataFrame
    summary_df = pd.DataFrame(summary_data)
    detailed_df = pd.DataFrame(detailed_routes)
    
    # 导出到Excel
    excel_file = output_dir / "车辆路径优化汇总报告.xlsx"
    
    with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
        # 汇总表
        summary_df.to_excel(writer, sheet_name='车辆汇总', index=False)
        
        # 详细路径表
        if not detailed_df.empty:
            detailed_df.to_excel(writer, sheet_name='详细路径', index=False)
        
        # 统计分析表
        stats_data = []
        
        # 总体统计
        total_vehicles = len(all_vehicles)
        successful_vehicles = len(summary_df[summary_df['优化状态'] == '成功'])
        failed_vehicles = total_vehicles - successful_vehicles
        
        stats_data.append(['总车辆数', total_vehicles])
        stats_data.append(['成功优化车辆数', successful_vehicles])
        stats_data.append(['失败车辆数', failed_vehicles])
        stats_data.append(['成功率(%)', round(successful_vehicles / total_vehicles * 100, 2)])
        
        # 成功车辆的统计
        successful_df = summary_df[summary_df['优化状态'] == '成功']
        if not successful_df.empty:
            stats_data.append(['', ''])
            stats_data.append(['=== 成功车辆统计 ===', ''])
            stats_data.append(['总距离(km)', successful_df['总距离(km)'].sum()])
            stats_data.append(['平均距离(km)', round(successful_df['总距离(km)'].mean(), 2)])
            stats_data.append(['总燃油成本(元)', round(successful_df['燃油成本(元)'].sum(), 2)])
            stats_data.append(['平均燃油成本(元)', round(successful_df['燃油成本(元)'].mean(), 2)])
            stats_data.append(['总停靠点数', successful_df['停靠点数'].sum()])
            stats_data.append(['平均停靠点数', round(successful_df['停靠点数'].mean(), 2)])
            stats_data.append(['总工作时长(小时)', round(successful_df['工作时长(小时)'].sum(), 2)])
            stats_data.append(['平均工作时长(小时)', round(successful_df['工作时长(小时)'].mean(), 2)])
        
        # 失败原因分析
        failed_df = summary_df[summary_df['优化状态'] == '失败']
        if not failed_df.empty:
            stats_data.append(['', ''])
            stats_data.append(['=== 失败车辆分析 ===', ''])
            large_truck_failed = len(failed_df[failed_df['车辆ID'].str.contains('LARGE')])
            ltl_truck_failed = len(failed_df[failed_df['车辆ID'].str.contains('LTL')])
            stats_data.append(['大型货车失败数', large_truck_failed])
            stats_data.append(['LTL货车失败数', ltl_truck_failed])
        
        stats_df = pd.DataFrame(stats_data, columns=['统计项目', '数值'])
        stats_df.to_excel(writer, sheet_name='统计分析', index=False)
    
    logger.info(f"路径优化汇总报告已保存到: {excel_file}")
    
    # 打印汇总信息
    print("\n=== 车辆路径优化汇总 ===")
    print(f"总车辆数: {total_vehicles}")
    print(f"成功优化: {successful_vehicles} 辆")
    print(f"优化失败: {failed_vehicles} 辆")
    print(f"成功率: {successful_vehicles / total_vehicles * 100:.1f}%")
    
    if successful_vehicles > 0:
        print(f"\n成功车辆统计:")
        print(f"  总距离: {successful_df['总距离(km)'].sum():.1f} km")
        print(f"  总燃油成本: {successful_df['燃油成本(元)'].sum():.2f} 元")
        print(f"  总停靠点: {successful_df['停靠点数'].sum()} 个")
        print(f"  总工作时长: {successful_df['工作时长(小时)'].sum():.1f} 小时")
    
    print(f"\n详细报告已保存到: {excel_file}")
    
    return excel_file

def analyze_failed_vehicles():
    """分析失败车辆的原因"""
    
    print("\n=== 失败车辆原因分析 ===")
    
    # 加载调度计划
    try:
        with open('output/intermediate/full_dispatch_plan.json', 'r', encoding='utf-8') as f:
            dispatch_plan = json.load(f)
    except Exception as e:
        print(f"无法加载调度计划: {e}")
        return
    
    failed_vehicles = []
    for vehicle_id in ['LARGE_TRUCK_00', 'LARGE_TRUCK_01', 'LARGE_TRUCK_02', 'LARGE_TRUCK_03',
                      'LARGE_TRUCK_04', 'LARGE_TRUCK_05', 'LARGE_TRUCK_06', 'LARGE_TRUCK_07',
                      'LTL_TRUCK_00']:
        standardized_vehicle_id = standardize_vehicle_id(vehicle_id)
        route_file = Path(f"output/reports/{standardized_vehicle_id}_route_plan.json")
        if not route_file.exists():
            failed_vehicles.append(vehicle_id)
    
    print(f"失败车辆: {failed_vehicles}")
    
    for vehicle_id in failed_vehicles:
        truck_data = dispatch_plan['dispatch_plan'].get(vehicle_id)
        if truck_data:
            print(f"\n{vehicle_id}:")
            print(f"  类型: {truck_data.get('type', '未知')}")
            if truck_data['type'] == 'FULL_TRUCK':
                print(f"  订单: {truck_data.get('source_order', '无')}")
                print(f"  货物类型: {truck_data.get('item_type', '无')}")
                print(f"  数量: {truck_data.get('quantity_per_truck', 0)}")
                print(f"  总重量: {truck_data.get('total_weight_kg', 0)} kg")
            elif truck_data['type'] == 'LTL_TRUCK':
                loaded_items = truck_data.get('loaded_items', [])
                print(f"  装载物品数: {len(loaded_items)}")
                if loaded_items:
                    total_weight = sum(item.get('weight_kg', 0) for item in loaded_items)
                    print(f"  总重量: {total_weight} kg")
        else:
            print(f"\n{vehicle_id}: 无调度数据")

if __name__ == "__main__":
    # 导出Excel报告
    excel_file = export_route_summary_to_excel()
    
    # 分析失败原因
    analyze_failed_vehicles()
