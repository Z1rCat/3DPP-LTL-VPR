# 装载方案JSON文件格式设计

## 文件命名规范
```
{TRUCK_ID}_loading_plan.json
例如: LTL_TRUCK_00_loading_plan.json, LARGE_TRUCK_00_loading_plan.json
```

## JSON结构设计（基于路径优化成功模式）

```json
{
  "summary": {
    "vehicle_id": "LTL_TRUCK_00",
    "total_items": 156,
    "total_weight_kg": 12553.96,
    "total_volume_m3": 24.43,
    "loading_efficiency": 88.2,
    "volume_utilization": 85.5,
    "optimization_algorithm": "Multi_Truck_3DPP_Gurobi",
    "solution_status": "OPTIMAL",
    "loading_time_minutes": 45,
    "cargo_types": ["酒水", "日用品", "建材"]
  },

  "vehicle_details": {
    "type": "LTL_TRUCK",
    "truck_specs": {
      "length_m": 9.6,
      "width_m": 2.4,
      "height_m": 2.4,
      "volume_m3": 55.296,
      "capacity_kg": 15000
    },
    "optimization_info": {
      "solver": "Gurobi_3DPP_Optimizer",
      "strategy": "多品类混合装载优化",
      "loading_type": "LTL_MIXED_LOADING"
    }
  },

  "loading_plan": [
    {
      "item_index": 1,
      "original_order_id": "ORDER_0036", // 真实订单号（反映射结果）
      "original_item_id": "ITEM_0036_001", // 真实货物ID
      "virtual_item_id": "LTL_00206", // 虚拟ID（用于追踪）
      "cargo_info": {
        "type": "酒水",
        "subtype": "白酒",
        "brand": "某品牌",
        "weight_kg": 23.72,
        "volume_m3": 0.07856
      },
      "dimensions": {
        "length_m": 0.4,
        "width_m": 0.3,
        "height_m": 0.65
      },
      "position_3d": {
        "x": 0.0,
        "y": 0.0,
        "z": 0.0,
        "rotation": 0
      },
      "loading_sequence": 1,
      "loading_zone": "zone_A",
      "stacking_info": {
        "can_stack": true,
        "stacked_on": null,
        "supports": ["item_2", "item_3"]
      }
    },
    {
      "item_index": 2,
      "original_order_id": "MERGED_ORDER_日用品_002",
      "merged_from": ["ORDER_0045", "ORDER_0046", "ORDER_0047"], // 如果是合并订单
      "virtual_item_id": "LTL_04959",
      "cargo_info": {
        "type": "日用品",
        "subtype": "洗护用品",
        "weight_kg": 3779.94,
        "volume_m3": 5.484
      },
      "dimensions": {
        "length_m": 1.2,
        "width_m": 1.0,
        "height_m": 0.8
      },
      "position_3d": {
        "x": 0.5,
        "y": 0.0,
        "z": 0.0,
        "rotation": 0
      },
      "loading_sequence": 2,
      "loading_zone": "zone_B",
      "stacking_info": {
        "can_stack": false,
        "stacked_on": null,
        "supports": []
      }
    }
  ],

  "loading_zones": {
    "zone_A": {
      "name": "轻货区",
      "items_count": 45,
      "cargo_types": ["酒水", "食品"]
    },
    "zone_B": {
      "name": "重货区",
      "items_count": 111,
      "cargo_types": ["日用品", "建材"]
    }
  },

  "statistics": {
    "by_cargo_type": {
      "酒水": {
        "count": 45,
        "weight_kg": 1067.4,
        "volume_m3": 3.535,
        "percentage": 28.8
      },
      "日用品": {
        "count": 1,
        "weight_kg": 3779.94,
        "volume_m3": 5.484,
        "percentage": 22.4
      }
    },
    "utilization": {
      "length_utilization": 85.2,
      "width_utilization": 92.1,
      "height_utilization": 78.9,
      "overall_utilization": 85.4
    }
  },

  "metadata": {
    "generated_time": "2025-09-22T10:25:17.000Z",
    "generated_by": "LTL_3DPP_Optimization_System_V3.0",
    "format_version": "1.0",
    "id_mapping_source": "id_to_orders_mapping.json"
  }
}
```

## 关键特性

1. **学习路径优化成功模式**：
   - 独立的JSON文件（每辆车一个）
   - 完整的结构化信息
   - 真实订单信息（反映射结果）

2. **包含完整的3D装载信息**：
   - 精确的3D位置坐标
   - 货物尺寸和旋转
   - 堆叠关系和装载顺序

3. **反映射真实货物信息**：
   - original_order_id: 真实订单号
   - original_item_id: 真实货物ID
   - 合并订单的原始订单列表

4. **丰富的统计和分析数据**：
   - 按货物类型的统计
   - 空间利用率分析
   - 装载效率指标

## 与路径优化JSON的对应关系

| 路径优化JSON | 装载方案JSON | 作用 |
|-------------|-------------|------|
| route_plan.json | loading_plan.json | 独立文件 |
| itinerary[] | loading_plan[] | 详细列表 |
| order_id | original_order_id | 真实订单 |
| coordinates | position_3d | 位置信息 |
| summary | summary | 汇总统计 |