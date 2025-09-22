#!/usr/bin/env python3
"""
数据结构诊断脚本
检查当前数据文件的列名和内容，诊断缺失order_type列的问题
"""

import pandas as pd
import json
import logging
from pathlib import Path

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_data_files():
    """检查所有相关数据文件的结构"""
    
    print("=== 数据文件结构诊断 ===\n")
    
    # 1. 检查原始Excel文件
    excel_file = "表2-1 A网点某年某月某日需完成的取送货订单需求.xlsx"
    if Path(excel_file).exists():
        print(f"1. 检查原始Excel文件: {excel_file}")
        try:
            df_excel = pd.read_excel(excel_file)
            print(f"   行数: {len(df_excel)}")
            print(f"   列数: {len(df_excel.columns)}")
            print(f"   列名: {df_excel.columns.tolist()}")
            
            # 检查是否有订单类型相关的列
            type_related_cols = [col for col in df_excel.columns if any(keyword in str(col).lower() 
                               for keyword in ['type', '类型', 'pickup', 'delivery', '取货', '送货', '配送'])]
            print(f"   类型相关列: {type_related_cols}")
            
            if type_related_cols:
                for col in type_related_cols:
                    unique_values = df_excel[col].unique()
                    print(f"   {col} 的唯一值: {unique_values}")
            
            print()
        except Exception as e:
            print(f"   读取Excel文件失败: {e}\n")
    
    # 2. 检查处理后的CSV文件
    csv_file = "output/intermediate/processed_items.csv"
    if Path(csv_file).exists():
        print(f"2. 检查处理后的CSV文件: {csv_file}")
        try:
            df_csv = pd.read_csv(csv_file)
            print(f"   行数: {len(df_csv)}")
            print(f"   列数: {len(df_csv.columns)}")
            print(f"   列名: {df_csv.columns.tolist()}")
            
            # 检查是否有订单类型相关的列
            type_related_cols = [col for col in df_csv.columns if any(keyword in str(col).lower() 
                               for keyword in ['type', '类型', 'pickup', 'delivery', '取货', '送货', '配送'])]
            print(f"   类型相关列: {type_related_cols}")
            
            if type_related_cols:
                for col in type_related_cols:
                    unique_values = df_csv[col].unique()
                    print(f"   {col} 的唯一值: {unique_values}")
            
            # 检查前几行数据
            print(f"   前3行数据:")
            print(df_csv.head(3).to_string())
            print()
        except Exception as e:
            print(f"   读取CSV文件失败: {e}\n")
    
    # 3. 检查调度计划JSON文件
    json_file = "output/intermediate/full_dispatch_plan.json"
    if Path(json_file).exists():
        print(f"3. 检查调度计划JSON文件: {json_file}")
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                dispatch_plan = json.load(f)
            
            print(f"   主要键: {list(dispatch_plan.keys())}")
            
            if 'dispatch_plan' in dispatch_plan:
                vehicles = list(dispatch_plan['dispatch_plan'].keys())
                print(f"   车辆数量: {len(vehicles)}")
                print(f"   车辆列表: {vehicles[:5]}...")  # 显示前5个
                
                # 检查第一个车辆的结构
                if vehicles:
                    first_vehicle = vehicles[0]
                    vehicle_data = dispatch_plan['dispatch_plan'][first_vehicle]
                    print(f"   第一个车辆 ({first_vehicle}) 的数据结构:")
                    print(f"     类型: {vehicle_data.get('type', 'N/A')}")
                    print(f"     主要键: {list(vehicle_data.keys())}")
                    
                    if 'loaded_items' in vehicle_data:
                        print(f"     装载物品数量: {len(vehicle_data['loaded_items'])}")
                        if vehicle_data['loaded_items']:
                            print(f"     第一个物品结构: {list(vehicle_data['loaded_items'][0].keys())}")
            print()
        except Exception as e:
            print(f"   读取JSON文件失败: {e}\n")
    
    # 4. 检查ID映射文件
    mapping_file = "output/intermediate/id_to_orders_mapping.json"
    if Path(mapping_file).exists():
        print(f"4. 检查ID映射文件: {mapping_file}")
        try:
            with open(mapping_file, 'r', encoding='utf-8') as f:
                mapping = json.load(f)
            
            print(f"   映射条目数量: {len(mapping)}")
            
            # 显示前几个映射关系
            sample_keys = list(mapping.keys())[:3]
            for key in sample_keys:
                print(f"   {key} -> {mapping[key]}")
            print()
        except Exception as e:
            print(f"   读取映射文件失败: {e}\n")

def test_column_mapping():
    """测试列名映射功能"""
    print("=== 测试列名映射功能 ===\n")
    
    csv_file = "output/intermediate/processed_items.csv"
    if not Path(csv_file).exists():
        print("processed_items.csv 文件不存在，无法测试")
        return
    
    try:
        df = pd.read_csv(csv_file)
        print(f"原始列名: {df.columns.tolist()}")
        
        # 定义列名映射关系（与routing_solver.py中相同）
        column_mapping = {
            'longitude': ['longitude', '经度'],
            'latitude': ['latitude', '纬度'],
            'weight_kg': ['weight_kg', '重量 (kg)', '重量', 'weight'],
            'order_type': ['订单类型', 'order_type', '类型', 'pickup_delivery']
        }
        
        # 执行列名映射
        mapped_columns = []
        for target_col, possible_cols in column_mapping.items():
            if target_col not in df.columns:
                for col in possible_cols:
                    if col in df.columns:
                        df[target_col] = df[col]
                        mapped_columns.append(f"{col} -> {target_col}")
                        break
        
        print(f"执行的映射: {mapped_columns}")
        print(f"映射后列名: {df.columns.tolist()}")
        
        # 检查必需的列
        required_columns = ['order_id', 'longitude', 'latitude', 'weight_kg', 'order_type']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            print(f"❌ 仍然缺失的列: {missing_columns}")
        else:
            print("✅ 所有必需列都已存在")
            
        # 如果order_type列存在，检查其值
        if 'order_type' in df.columns:
            unique_values = df['order_type'].unique()
            print(f"order_type 的唯一值: {unique_values}")
            value_counts = df['order_type'].value_counts()
            print(f"order_type 值分布:")
            for value, count in value_counts.items():
                print(f"  {value}: {count}")
        
    except Exception as e:
        print(f"测试失败: {e}")

def check_specific_vehicle_data():
    """检查特定车辆的数据"""
    print("=== 检查特定车辆数据 ===\n")
    
    # 加载必要文件
    try:
        # 1. 加载调度计划
        with open("output/intermediate/full_dispatch_plan.json", 'r', encoding='utf-8') as f:
            dispatch_plan = json.load(f)
        
        # 2. 加载映射关系
        with open("output/intermediate/id_to_orders_mapping.json", 'r', encoding='utf-8') as f:
            mapping = json.load(f)
        
        # 3. 加载订单数据
        orders_df = pd.read_csv("output/intermediate/processed_items.csv")
        
        # 检查第一个失败的车辆：LARGE_TRUCK_00
        truck_id = "LARGE_TRUCK_00"
        print(f"检查车辆: {truck_id}")
        
        if truck_id in dispatch_plan['dispatch_plan']:
            truck_data = dispatch_plan['dispatch_plan'][truck_id]
            print(f"车辆类型: {truck_data.get('type', 'N/A')}")
            print(f"车辆数据键: {list(truck_data.keys())}")
            
            # 提取装载的物品
            if truck_data['type'] == 'FULL_TRUCK':
                loaded_items = [truck_data['source_order']]
                print(f"装载的订单: {loaded_items}")
            elif truck_data['type'] == 'LTL_TRUCK':
                loaded_items = [item['item_id'] for item in truck_data['loaded_items']]
                print(f"装载的物品: {loaded_items}")
            
            # 通过映射找到原始订单ID
            order_ids = []
            for item_id in loaded_items:
                if item_id in mapping:
                    mapped_orders = mapping[item_id]
                    if isinstance(mapped_orders, list):
                        order_ids.extend(mapped_orders)
                    else:
                        order_ids.append(mapped_orders)
                else:
                    order_ids.append(item_id)
            
            order_ids = list(set(order_ids))
            print(f"映射后的订单ID: {order_ids}")
            
            # 从订单数据中查找
            relevant_orders = orders_df[orders_df['order_id'].isin(order_ids)]
            print(f"找到的相关订单数量: {len(relevant_orders)}")
            
            if not relevant_orders.empty:
                print(f"相关订单的列名: {relevant_orders.columns.tolist()}")
                print("前几行数据:")
                print(relevant_orders.head().to_string())
            else:
                print("❌ 未找到相关订单数据")
        
    except Exception as e:
        print(f"检查失败: {e}")

if __name__ == "__main__":
    check_data_files()
    test_column_mapping()
    check_specific_vehicle_data()
