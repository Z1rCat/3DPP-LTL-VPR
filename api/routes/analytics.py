"""
分析报告路由
Analytics and Reporting Routes
"""

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
import tempfile
import json
from pathlib import Path

from analytics.trend_analyzer import trend_analyzer
from analytics.performance_analyzer import performance_analyzer
from analytics.report_generator import report_generator

router = APIRouter()

class TrendAnalysisRequest(BaseModel):
    metric_name: str
    time_period: str = "30days"
    category: Optional[str] = None

class PerformanceAnalysisRequest(BaseModel):
    experiment_id: str

class AlgorithmComparisonRequest(BaseModel):
    algorithms: Optional[List[str]] = None
    time_period: int = 30

class CustomReportConfig(BaseModel):
    type: str = "custom"
    experiment_filter: Dict[str, Any] = {}
    metrics_filter: List[str] = []
    analysis_modules: List[str] = ["performance", "trends"]
    time_range: str = "30days"

@router.get("/trends/metrics/{metric_name}", summary="分析指定指标趋势")
async def analyze_metric_trend(
    metric_name: str,
    time_period: str = Query("30days", description="时间段: 7days, 30days, 90days"),
    category: Optional[str] = Query(None, description="指标类别筛选")
):
    """
    分析指定指标的趋势

    - **metric_name**: 指标名称
    - **time_period**: 分析时间段
    - **category**: 指标类别（可选）
    """
    try:
        analysis = trend_analyzer.analyze_metric_trend(
            metric_name=metric_name,
            time_period=time_period,
            category=category
        )

        return {
            "success": True,
            "data": analysis.to_dict()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"趋势分析失败: {str(e)}")

@router.get("/trends/all", summary="分析所有指标趋势")
async def analyze_all_trends(
    time_period: str = Query("30days", description="时间段: 7days, 30days, 90days")
):
    """
    分析所有标准指标的趋势

    - **time_period**: 分析时间段
    """
    try:
        analyses = trend_analyzer.analyze_all_metrics_trends(time_period)

        # 转换为字典格式
        result = {}
        for metric, analysis in analyses.items():
            result[metric] = analysis.to_dict()

        return {
            "success": True,
            "data": result,
            "metrics_count": len(result)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"全量趋势分析失败: {str(e)}")

@router.get("/trends/compare/{metric_name}", summary="对比指标不同时间段趋势")
async def compare_metric_periods(
    metric_name: str,
    periods: Optional[str] = Query("7days,30days,90days", description="时间段列表，逗号分隔")
):
    """
    对比指定指标在不同时间段的趋势

    - **metric_name**: 指标名称
    - **periods**: 时间段列表，逗号分隔
    """
    try:
        period_list = periods.split(",") if periods else None
        comparisons = trend_analyzer.compare_metric_periods(metric_name, period_list)

        # 转换为字典格式
        result = {}
        for period, analysis in comparisons.items():
            result[period] = analysis.to_dict()

        return {
            "success": True,
            "data": result,
            "periods_compared": len(result)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"趋势对比失败: {str(e)}")

@router.get("/trends/anomalies/{metric_name}", summary="检测指标异常值")
async def detect_anomalies(
    metric_name: str,
    time_period: str = Query("30days", description="时间段"),
    threshold_factor: float = Query(2.0, description="异常检测阈值因子")
):
    """
    检测指定指标的异常值

    - **metric_name**: 指标名称
    - **time_period**: 分析时间段
    - **threshold_factor**: 异常检测阈值因子
    """
    try:
        anomalies = trend_analyzer.detect_anomalies(
            metric_name=metric_name,
            time_period=time_period,
            threshold_factor=threshold_factor
        )

        return {
            "success": True,
            "data": anomalies,
            "anomalies_count": len(anomalies)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"异常检测失败: {str(e)}")

@router.get("/trends/improvement/{metric_name}", summary="计算指标改进率")
async def calculate_improvement_rate(
    metric_name: str,
    time_period: str = Query("30days", description="时间段")
):
    """
    计算指定指标的改进率

    - **metric_name**: 指标名称
    - **time_period**: 分析时间段
    """
    try:
        improvement = trend_analyzer.calculate_improvement_rate(
            metric_name=metric_name,
            time_period=time_period
        )

        return {
            "success": True,
            "data": improvement
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"改进率计算失败: {str(e)}")

@router.post("/performance/experiment", summary="分析实验性能")
async def analyze_experiment_performance(request: PerformanceAnalysisRequest):
    """
    全面分析单个实验的性能

    - **experiment_id**: 实验ID
    """
    try:
        analysis = performance_analyzer.analyze_experiment_performance(request.experiment_id)

        return {
            "success": True,
            "data": analysis
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"实验性能分析失败: {str(e)}")

@router.post("/performance/algorithms", summary="对比算法性能")
async def compare_algorithm_performance(request: AlgorithmComparisonRequest):
    """
    对比不同算法的性能表现

    - **algorithms**: 算法列表，None则对比所有算法
    - **time_period**: 分析时间段（天）
    """
    try:
        comparison = performance_analyzer.compare_algorithm_performance(
            algorithms=request.algorithms,
            time_period=request.time_period
        )

        return {
            "success": True,
            "data": comparison
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"算法性能对比失败: {str(e)}")

@router.get("/performance/efficiency", summary="分析效率模式")
async def analyze_efficiency_patterns(
    category: Optional[str] = Query(None, description="指标类别筛选")
):
    """
    分析效率模式和规律

    - **category**: 指标类别筛选（可选）
    """
    try:
        analysis = performance_analyzer.analyze_efficiency_patterns(category)

        return {
            "success": True,
            "data": analysis
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"效率模式分析失败: {str(e)}")

@router.post("/reports/comprehensive", summary="生成综合报告")
async def generate_comprehensive_report(
    experiment_ids: Optional[List[str]] = None,
    time_period: str = "30days",
    include_recommendations: bool = True
):
    """
    生成综合分析报告

    - **experiment_ids**: 指定实验ID列表，None则包含所有实验
    - **time_period**: 分析时间段
    - **include_recommendations**: 是否包含改进建议
    """
    try:
        report = report_generator.generate_comprehensive_report(
            experiment_ids=experiment_ids,
            time_period=time_period,
            include_recommendations=include_recommendations
        )

        return {
            "success": True,
            "data": report
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"综合报告生成失败: {str(e)}")

@router.post("/reports/trend", summary="生成趋势报告")
async def generate_trend_report(
    metrics: Optional[List[str]] = None,
    time_period: str = "30days"
):
    """
    生成趋势分析报告

    - **metrics**: 指定指标列表，None则分析所有标准指标
    - **time_period**: 分析时间段
    """
    try:
        report = report_generator.generate_trend_report(
            metrics=metrics,
            time_period=time_period
        )

        return {
            "success": True,
            "data": report
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"趋势报告生成失败: {str(e)}")

@router.post("/reports/benchmark", summary="生成性能基准报告")
async def generate_benchmark_report(
    algorithm: Optional[str] = Query(None, description="指定算法，None则对比所有算法")
):
    """
    生成性能基准报告

    - **algorithm**: 指定算法，None则对比所有算法
    """
    try:
        report = report_generator.generate_performance_benchmark_report(algorithm)

        return {
            "success": True,
            "data": report
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"基准报告生成失败: {str(e)}")

@router.post("/reports/custom", summary="生成自定义报告")
async def generate_custom_report(config: CustomReportConfig):
    """
    生成自定义报告

    - **config**: 自定义报告配置
    """
    try:
        report = report_generator.generate_custom_report(config.dict())

        return {
            "success": True,
            "data": report
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"自定义报告生成失败: {str(e)}")

@router.get("/reports/list", summary="获取已生成报告列表")
async def list_generated_reports(
    limit: int = Query(50, ge=1, le=100, description="返回数量限制")
):
    """
    列出已生成的报告

    - **limit**: 返回数量限制
    """
    try:
        reports = report_generator.list_generated_reports(limit)

        return {
            "success": True,
            "data": reports,
            "count": len(reports)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取报告列表失败: {str(e)}")

@router.get("/reports/{report_id}/download", summary="下载报告文件")
async def download_report(report_id: str):
    """
    下载指定的报告文件

    - **report_id**: 报告ID
    """
    try:
        reports_dir = Path("output/analytics_reports")
        report_file = reports_dir / f"{report_id}.json"

        if not report_file.exists():
            raise HTTPException(status_code=404, detail=f"报告文件 {report_id} 不存在")

        return FileResponse(
            path=str(report_file),
            filename=f"{report_id}.json",
            media_type="application/json"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"下载报告失败: {str(e)}")

@router.post("/reports/{report_id}/export/excel", summary="导出报告为Excel")
async def export_report_to_excel(report_id: str):
    """
    将报告导出为Excel文件并下载

    - **report_id**: 报告ID
    """
    try:
        reports_dir = Path("output/analytics_reports")
        report_file = reports_dir / f"{report_id}.json"

        if not report_file.exists():
            raise HTTPException(status_code=404, detail=f"报告文件 {report_id} 不存在")

        # 读取报告数据
        with open(report_file, 'r', encoding='utf-8') as f:
            report_data = json.load(f)

        # 导出为Excel
        excel_path = report_generator.export_report_to_excel(report_data)

        return FileResponse(
            path=excel_path,
            filename=f"{report_id}.xlsx",
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Excel导出失败: {str(e)}")

@router.get("/dashboard/overview", summary="获取分析仪表板概览")
async def get_dashboard_overview():
    """
    获取分析仪表板概览数据
    """
    try:
        # 获取基础统计
        from database.db_manager import db_manager
        stats = db_manager.get_statistics()

        # 获取最新趋势（简化版）
        try:
            recent_trends = {}
            key_metrics = ['loading_efficiency', 'total_distance', 'vehicle_utilization']

            for metric in key_metrics:
                try:
                    trend = trend_analyzer.analyze_metric_trend(metric, '7days')
                    recent_trends[metric] = {
                        'direction': trend.trend_direction,
                        'strength': trend.trend_strength,
                        'data_points': len(trend.data_points)
                    }
                except:
                    recent_trends[metric] = {'direction': 'stable', 'strength': 0, 'data_points': 0}

        except Exception:
            recent_trends = {}

        # 获取算法性能对比（简化版）
        try:
            algorithm_comparison = performance_analyzer.compare_algorithm_performance()
            best_algorithm = algorithm_comparison.get('best_algorithm', 'N/A')
        except Exception:
            best_algorithm = 'N/A'

        overview = {
            'statistics': stats,
            'recent_trends': recent_trends,
            'best_algorithm': best_algorithm,
            'last_updated': str(datetime.now())
        }

        return {
            "success": True,
            "data": overview
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取仪表板概览失败: {str(e)}")

@router.get("/dashboard/charts/trends", summary="获取趋势图表数据")
async def get_trends_chart_data(
    metrics: str = Query("loading_efficiency,vehicle_utilization", description="指标列表，逗号分隔"),
    time_period: str = Query("30days", description="时间段")
):
    """
    获取趋势图表数据

    - **metrics**: 指标列表，逗号分隔
    - **time_period**: 时间段
    """
    try:
        metric_list = metrics.split(',')
        chart_data = {}

        for metric in metric_list:
            try:
                trend = trend_analyzer.analyze_metric_trend(metric.strip(), time_period)
                chart_data[metric] = {
                    'data_points': trend.data_points,
                    'trend_info': {
                        'direction': trend.trend_direction,
                        'strength': trend.trend_strength
                    }
                }
            except Exception as e:
                chart_data[metric] = {'error': str(e)}

        return {
            "success": True,
            "data": chart_data
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取趋势图表数据失败: {str(e)}")

@router.get("/dashboard/charts/performance", summary="获取性能分布图表数据")
async def get_performance_chart_data():
    """
    获取性能分布图表数据
    """
    try:
        # 获取效率模式分析
        efficiency_analysis = performance_analyzer.analyze_efficiency_patterns()

        # 提取图表所需数据
        chart_data = {
            'efficiency_distribution': efficiency_analysis.get('efficiency_distribution', {}),
            'vehicle_type_performance': efficiency_analysis.get('vehicle_type_performance', {}),
            'loading_patterns': efficiency_analysis.get('loading_patterns', {})
        }

        return {
            "success": True,
            "data": chart_data
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取性能图表数据失败: {str(e)}")

from datetime import datetime