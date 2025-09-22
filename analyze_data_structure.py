"""
数据结构分析脚本
分析真实数据文件的结构，为可视化提供数据接口
"""
import pickle
import json
import pandas as pd
from pathlib import Path

def analyze_pickle_file(file_path):
    """分析pickle文件结构"""
    print(f"\n=== 分析文件: {file_path} ===")
    try:
        with open(file_path, 'rb') as f:
            data = pickle.load(f)

        print(f"数据类型: {type(data)}")

        if isinstance(data, dict):
            print(f"字典键: {list(data.keys())}")
            for key, value in data.items():
                print(f"  {key}: {type(value)}")
                if isinstance(value, list) and len(value) > 0:
                    print(f"    列表长度: {len(value)}")
                    if isinstance(value[0], dict):
                        print(f"    第一个元素的键: {list(value[0].keys())}")
                        # 打印第一个元素的完整结构
                        print(f"    第一个元素示例:")
                        for k, v in value[0].items():
                            print(f"      {k}: {v} ({type(v)})")
                elif isinstance(value, dict):
                    print(f"    嵌套字典键: {list(value.keys())[:5]}...")
        elif isinstance(data, list):
            print(f"列表长度: {len(data)}")
            if len(data) > 0:
                print(f"第一个元素类型: {type(data[0])}")
                if isinstance(data[0], dict):
                    print(f"第一个元素的键: {list(data[0].keys())}")

        return data
    except Exception as e:
        print(f"错误: {e}")
        return None

def analyze_json_file(file_path):
    """分析JSON文件结构"""
    print(f"\n=== 分析JSON文件: {file_path} ===")
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        print(f"数据类型: {type(data)}")
        if isinstance(data, dict):
            print(f"主要键: {list(data.keys())}")

        return data
    except Exception as e:
        print(f"错误: {e}")
        return None

def main():
    """主分析函数"""
    base_path = Path("a:/MYpython/物流/output")

    print("="*60)
    print("真实数据结构分析")
    print("="*60)

    # 1. 分析Gurobi解决方案
    gurobi_file = base_path / "intermediate" / "gurobi_solution.pkl"
    if gurobi_file.exists():
        gurobi_data = analyze_pickle_file(gurobi_file)

    # 2. 分析LTL候选项
    ltl_file = base_path / "intermediate" / "ltl_candidate_items.pkl"
    if ltl_file.exists():
        ltl_data = analyze_pickle_file(ltl_file)

    # 3. 分析处理后的货物数据
    processed_file = base_path / "intermediate" / "processed_items.pkl"
    if processed_file.exists():
        processed_data = analyze_pickle_file(processed_file)

    # 4. 分析调度计划
    dispatch_file = base_path / "intermediate" / "full_dispatch_plan.json"
    if dispatch_file.exists():
        dispatch_data = analyze_json_file(dispatch_file)

    # 5. 分析路径计划
    route_files = list((base_path / "reports").glob("*_route_plan.json"))
    if route_files:
        route_data = analyze_json_file(route_files[0])

    print("\n" + "="*60)
    print("数据分析完成")
    print("="*60)

if __name__ == "__main__":
    main()