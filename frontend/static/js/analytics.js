/**
 * 分析仪表板 JavaScript
 * Analytics Dashboard JavaScript Functions
 */

// 全局变量
let currentPage = 1;
let pageSize = 10;
let currentFilters = {};
let charts = {};

// 页面初始化
document.addEventListener('DOMContentLoaded', function() {
    initializeAnalytics();
    setupNavigation();
    setupModalHandlers();
    setupTabHandlers();
});

/**
 * 初始化分析功能
 */
function initializeAnalytics() {
    loadDashboardOverview();
    loadExperiments();
    loadReportsList();

    // 设置定时刷新
    setInterval(loadDashboardOverview, 30000); // 每30秒刷新概览
}

/**
 * 设置导航功能
 */
function setupNavigation() {
    const navLinks = document.querySelectorAll('.nav-link');
    const sections = document.querySelectorAll('.section');

    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();

            // 更新导航状态
            navLinks.forEach(l => l.classList.remove('active'));
            this.classList.add('active');

            // 显示对应部分
            const targetId = this.getAttribute('href').substring(1);
            sections.forEach(section => {
                section.classList.remove('active');
                if (section.id === targetId) {
                    section.classList.add('active');
                }
            });

            // 加载对应数据
            loadSectionData(targetId);
        });
    });
}

/**
 * 设置模态框处理器
 */
function setupModalHandlers() {
    const modal = document.getElementById('createExperimentModal');
    const span = document.querySelector('.close');

    span.onclick = function() {
        closeCreateExperiment();
    }

    window.onclick = function(event) {
        if (event.target == modal) {
            closeCreateExperiment();
        }
    }

    // 表单提交处理
    document.getElementById('createExperimentForm').addEventListener('submit', function(e) {
        e.preventDefault();
        createExperiment();
    });
}

/**
 * 设置选项卡处理器
 */
function setupTabHandlers() {
    const tabButtons = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');

    tabButtons.forEach(button => {
        button.addEventListener('click', function() {
            const targetTab = this.getAttribute('data-tab');

            // 更新按钮状态
            tabButtons.forEach(btn => btn.classList.remove('active'));
            this.classList.add('active');

            // 显示对应内容
            tabContents.forEach(content => {
                content.classList.remove('active');
                if (content.id === targetTab) {
                    content.classList.add('active');
                }
            });

            // 加载选项卡数据
            loadTabData(targetTab);
        });
    });
}

/**
 * 加载仪表板概览数据
 */
async function loadDashboardOverview() {
    try {
        const response = await fetch('/api/analytics/dashboard/overview');
        const result = await response.json();

        if (result.success) {
            updateOverviewStats(result.data);
            updateTrendsCharts(result.data.recent_trends);
            updateInsights(result.data);
        } else {
            console.error('Failed to load dashboard overview:', result.error);
            showNotification('加载仪表板概览失败', 'error');
        }
    } catch (error) {
        console.error('Error loading dashboard overview:', error);
        showNotification('网络错误：无法加载仪表板数据', 'error');
    }
}

/**
 * 更新概览统计数据
 */
function updateOverviewStats(data) {
    const stats = data.statistics;

    // 更新统计卡片
    document.getElementById('total-experiments').textContent = stats.total_experiments || 0;
    document.getElementById('success-rate').textContent = `${((stats.completed_experiments / stats.total_experiments) * 100).toFixed(1)}%` || '0%';
    document.getElementById('avg-efficiency').textContent = `${stats.avg_loading_efficiency?.toFixed(1)}%` || '0%';
    document.getElementById('total-vehicles').textContent = stats.total_vehicles || 0;

    // 更新趋势指示器（模拟数据）
    document.getElementById('experiments-trend').textContent = '+5%';
    document.getElementById('success-trend').textContent = '+2%';
    document.getElementById('efficiency-trend').textContent = '+8%';
    document.getElementById('vehicles-trend').textContent = '0%';
}

/**
 * 更新趋势图表
 */
function updateTrendsCharts(trendsData) {
    // 装载效率趋势图
    updateEfficiencyTrendChart(trendsData.loading_efficiency);

    // 算法对比图
    updateAlgorithmComparisonChart();
}

/**
 * 更新装载效率趋势图
 */
function updateEfficiencyTrendChart(trendData) {
    const ctx = document.getElementById('efficiencyTrendChart');

    if (charts.efficiencyTrend) {
        charts.efficiencyTrend.destroy();
    }

    // 模拟数据（实际应该从API获取）
    const data = {
        labels: ['1周前', '6天前', '5天前', '4天前', '3天前', '2天前', '昨天'],
        datasets: [{
            label: '装载效率 (%)',
            data: [75, 78, 72, 80, 85, 83, 87],
            borderColor: '#007bff',
            backgroundColor: 'rgba(0, 123, 255, 0.1)',
            tension: 0.4,
            fill: true
        }]
    };

    charts.efficiencyTrend = new Chart(ctx, {
        type: 'line',
        data: data,
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100
                }
            },
            plugins: {
                legend: {
                    display: false
                }
            }
        }
    });
}

/**
 * 更新算法对比图
 */
function updateAlgorithmComparisonChart() {
    const ctx = document.getElementById('algorithmComparisonChart');

    if (charts.algorithmComparison) {
        charts.algorithmComparison.destroy();
    }

    const data = {
        labels: ['集成优化', 'Gurobi 3D', 'LTL优化'],
        datasets: [{
            label: '平均效率 (%)',
            data: [85, 78, 72],
            backgroundColor: ['#28a745', '#007bff', '#ffc107'],
            borderColor: ['#1e7e34', '#0056b3', '#e0a800'],
            borderWidth: 2
        }]
    };

    charts.algorithmComparison = new Chart(ctx, {
        type: 'bar',
        data: data,
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100
                }
            },
            plugins: {
                legend: {
                    display: false
                }
            }
        }
    });
}

/**
 * 更新洞察信息
 */
function updateInsights(data) {
    const insightsList = document.getElementById('insights-list');

    // 清空现有内容
    insightsList.innerHTML = '';

    const insights = [
        { icon: 'fas fa-arrow-up', text: '装载效率本周提升8%，表现优异' },
        { icon: 'fas fa-lightbulb', text: '集成优化算法在当前数据集上表现最佳' },
        { icon: 'fas fa-exclamation-circle', text: `检测到${data.statistics?.total_experiments || 0}个实验记录` },
        { icon: 'fas fa-chart-line', text: '车辆利用率稳定在90%以上水平' }
    ];

    insights.forEach(insight => {
        const insightItem = document.createElement('div');
        insightItem.className = 'insight-item';
        insightItem.innerHTML = `
            <i class="${insight.icon}"></i>
            <span>${insight.text}</span>
        `;
        insightsList.appendChild(insightItem);
    });
}

/**
 * 加载实验列表
 */
async function loadExperiments() {
    try {
        const queryParams = new URLSearchParams({
            limit: pageSize,
            offset: (currentPage - 1) * pageSize,
            ...currentFilters
        });

        const response = await fetch(`/api/experiments/?${queryParams}`);
        const result = await response.json();

        if (result.success) {
            updateExperimentsTable(result.data);
            updatePagination(result.pagination);
        } else {
            console.error('Failed to load experiments:', result.error);
            showNotification('加载实验列表失败', 'error');
        }
    } catch (error) {
        console.error('Error loading experiments:', error);
        showNotification('网络错误：无法加载实验数据', 'error');

        // 显示错误状态
        document.getElementById('experimentsTableBody').innerHTML = `
            <tr><td colspan="7" class="loading-cell" style="color: #dc3545;">
                <i class="fas fa-exclamation-triangle"></i> 加载失败，请稍后重试
            </td></tr>
        `;
    }
}

/**
 * 更新实验表格
 */
function updateExperimentsTable(experiments) {
    const tbody = document.getElementById('experimentsTableBody');

    if (experiments.length === 0) {
        tbody.innerHTML = `
            <tr><td colspan="7" class="loading-cell">暂无实验数据</td></tr>
        `;
        return;
    }

    tbody.innerHTML = experiments.map(exp => `
        <tr>
            <td>${exp.name}</td>
            <td>${exp.algorithm}</td>
            <td><span class="status-badge ${exp.status}">${getStatusText(exp.status)}</span></td>
            <td>${formatDate(exp.created_at)}</td>
            <td>${exp.vehicle_count || 0}</td>
            <td>${exp.total_orders || 0}</td>
            <td>
                <button class="btn primary" onclick="viewExperiment('${exp.experiment_id}')" style="padding: 4px 8px; font-size: 12px;">
                    查看
                </button>
                ${exp.status === 'running' ?
                    `<button class="btn secondary" onclick="stopExperiment('${exp.experiment_id}')" style="padding: 4px 8px; font-size: 12px; margin-left: 4px;">
                        停止
                    </button>` : ''
                }
            </td>
        </tr>
    `).join('');
}

/**
 * 获取状态文本
 */
function getStatusText(status) {
    const statusMap = {
        'running': '运行中',
        'completed': '已完成',
        'failed': '失败',
        'pending': '待处理'
    };
    return statusMap[status] || status;
}

/**
 * 格式化日期
 */
function formatDate(dateString) {
    if (!dateString) return '-';

    try {
        const date = new Date(dateString);
        return date.toLocaleString('zh-CN', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit'
        });
    } catch (error) {
        return dateString;
    }
}

/**
 * 更新分页信息
 */
function updatePagination(pagination) {
    const pageInfo = document.getElementById('pageInfo');
    const prevButton = document.getElementById('prevPage');
    const nextButton = document.getElementById('nextPage');

    const totalPages = Math.ceil((pagination.offset + pagination.limit) / pageSize);
    pageInfo.textContent = `页面 ${currentPage} / ${Math.max(totalPages, 1)}`;

    prevButton.disabled = currentPage <= 1;
    nextButton.disabled = !pagination.has_more;
}

/**
 * 切换页面
 */
function changePage(direction) {
    currentPage += direction;
    if (currentPage < 1) currentPage = 1;

    loadExperiments();
}

/**
 * 刷新实验列表
 */
function refreshExperiments() {
    currentPage = 1;
    loadExperiments();
}

/**
 * 显示创建实验模态框
 */
function showCreateExperiment() {
    document.getElementById('createExperimentModal').style.display = 'block';
}

/**
 * 关闭创建实验模态框
 */
function closeCreateExperiment() {
    document.getElementById('createExperimentModal').style.display = 'none';
    document.getElementById('createExperimentForm').reset();
}

/**
 * 创建实验
 */
async function createExperiment() {
    const formData = new FormData(document.getElementById('createExperimentForm'));

    const experimentData = {
        name: formData.get('experimentName') || document.getElementById('experimentName').value,
        description: formData.get('experimentDescription') || document.getElementById('experimentDescription').value,
        algorithm: formData.get('experimentAlgorithm') || document.getElementById('experimentAlgorithm').value,
        created_by: 'frontend_user'
    };

    try {
        const response = await fetch('/api/experiments/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(experimentData)
        });

        const result = await response.json();

        if (result.success) {
            showNotification(`实验 "${experimentData.name}" 创建成功`, 'success');
            closeCreateExperiment();
            refreshExperiments();
        } else {
            showNotification('创建实验失败：' + (result.detail || '未知错误'), 'error');
        }
    } catch (error) {
        console.error('Error creating experiment:', error);
        showNotification('网络错误：创建实验失败', 'error');
    }
}

/**
 * 查看实验详情
 */
async function viewExperiment(experimentId) {
    try {
        const response = await fetch(`/api/experiments/${experimentId}`);
        const result = await response.json();

        if (result.success) {
            // 这里可以显示实验详情模态框或跳转到详情页
            console.log('Experiment details:', result.data);
            showNotification(`实验 ${experimentId} 详情已加载`, 'info');
        } else {
            showNotification('获取实验详情失败', 'error');
        }
    } catch (error) {
        console.error('Error viewing experiment:', error);
        showNotification('网络错误：无法获取实验详情', 'error');
    }
}

/**
 * 分析趋势
 */
async function analyzeTrend() {
    const metricSelect = document.getElementById('metricSelect');
    const periodSelect = document.getElementById('periodSelect');

    const metric = metricSelect.value;
    const period = periodSelect.value;

    try {
        const response = await fetch(`/api/analytics/trends/metrics/${metric}?time_period=${period}`);
        const result = await response.json();

        if (result.success) {
            updateTrendChart(result.data);
            updateTrendSummary(result.data);

            // 检测异常
            detectTrendAnomalies(metric, period);
        } else {
            showNotification('趋势分析失败', 'error');
        }
    } catch (error) {
        console.error('Error analyzing trend:', error);
        showNotification('网络错误：趋势分析失败', 'error');
    }
}

/**
 * 更新趋势图表
 */
function updateTrendChart(trendData) {
    const ctx = document.getElementById('trendChart');

    if (charts.trend) {
        charts.trend.destroy();
    }

    if (!trendData.data_points || trendData.data_points.length === 0) {
        ctx.getContext('2d').clearRect(0, 0, ctx.width, ctx.height);
        return;
    }

    const labels = trendData.data_points.map(point => formatDate(point.timestamp));
    const values = trendData.data_points.map(point => point.value);

    const data = {
        labels: labels,
        datasets: [{
            label: trendData.metric_name,
            data: values,
            borderColor: '#007bff',
            backgroundColor: 'rgba(0, 123, 255, 0.1)',
            tension: 0.4,
            fill: true
        }]
    };

    charts.trend = new Chart(ctx, {
        type: 'line',
        data: data,
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
}

/**
 * 更新趋势摘要
 */
function updateTrendSummary(trendData) {
    const summaryDiv = document.getElementById('trendSummary');

    const trendText = getTrendText(trendData.trend_direction);
    const strengthText = getStrengthText(trendData.trend_strength);

    summaryDiv.innerHTML = `
        <div class="trend-info">
            <p><strong>趋势方向:</strong> ${trendText}</p>
            <p><strong>趋势强度:</strong> ${strengthText}</p>
            <p><strong>数据点:</strong> ${trendData.data_points?.length || 0} 个</p>
            <p><strong>分析摘要:</strong> ${trendData.analysis_summary || '暂无摘要'}</p>
        </div>
    `;
}

/**
 * 获取趋势文本
 */
function getTrendText(direction) {
    const directionMap = {
        'increasing': '上升',
        'decreasing': '下降',
        'stable': '稳定'
    };
    return directionMap[direction] || '未知';
}

/**
 * 获取强度文本
 */
function getStrengthText(strength) {
    if (strength > 0.7) return '强烈';
    if (strength > 0.4) return '中等';
    if (strength > 0.1) return '微弱';
    return '几乎无变化';
}

/**
 * 检测趋势异常
 */
async function detectTrendAnomalies(metric, period) {
    try {
        const response = await fetch(`/api/analytics/trends/anomalies/${metric}?time_period=${period}`);
        const result = await response.json();

        if (result.success) {
            updateAnomaliesList(result.data);
        }
    } catch (error) {
        console.error('Error detecting anomalies:', error);
    }
}

/**
 * 更新异常列表
 */
function updateAnomaliesList(anomalies) {
    const anomaliesList = document.getElementById('anomaliesList');

    if (anomalies.length === 0) {
        anomaliesList.innerHTML = '<p>未检测到异常数据</p>';
        return;
    }

    anomaliesList.innerHTML = anomalies.map(anomaly => `
        <div class="anomaly-item">
            <strong>实验:</strong> ${anomaly.name}<br>
            <strong>值:</strong> ${anomaly.value}<br>
            <strong>异常评分:</strong> ${anomaly.z_score.toFixed(2)}<br>
            <strong>时间:</strong> ${formatDate(anomaly.timestamp)}
        </div>
    `).join('');
}

/**
 * 对比算法性能
 */
async function compareAlgorithms() {
    const timeRange = document.getElementById('timeRangeSelect').value;

    try {
        const response = await fetch('/api/analytics/performance/algorithms', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                algorithms: null, // 对比所有算法
                time_period: parseInt(timeRange)
            })
        });

        const result = await response.json();

        if (result.success) {
            updateAlgorithmPerformanceChart(result.data);
            updateAlgorithmComparisonTable(result.data);
        } else {
            showNotification('算法对比失败', 'error');
        }
    } catch (error) {
        console.error('Error comparing algorithms:', error);
        showNotification('网络错误：算法对比失败', 'error');
    }
}

/**
 * 更新算法性能图表
 */
function updateAlgorithmPerformanceChart(comparisonData) {
    const ctx = document.getElementById('algorithmPerformanceChart');

    if (charts.algorithmPerformance) {
        charts.algorithmPerformance.destroy();
    }

    if (!comparisonData.comparison_data) {
        return;
    }

    const algorithms = Object.keys(comparisonData.comparison_data);
    const efficiencyData = algorithms.map(alg => {
        const data = comparisonData.comparison_data[alg];
        return data.performance_statistics?.loading_efficiency?.mean || 0;
    });

    const data = {
        labels: algorithms,
        datasets: [{
            label: '平均装载效率 (%)',
            data: efficiencyData,
            backgroundColor: ['#007bff', '#28a745', '#ffc107', '#dc3545'],
            borderWidth: 1
        }]
    };

    charts.algorithmPerformance = new Chart(ctx, {
        type: 'bar',
        data: data,
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100
                }
            }
        }
    });
}

/**
 * 更新算法对比表格
 */
function updateAlgorithmComparisonTable(comparisonData) {
    const tbody = document.getElementById('algorithmComparisonBody');

    if (!comparisonData.comparison_data) {
        tbody.innerHTML = '<tr><td colspan="5">暂无对比数据</td></tr>';
        return;
    }

    tbody.innerHTML = Object.entries(comparisonData.comparison_data).map(([algorithm, data]) => {
        const efficiency = data.performance_statistics?.loading_efficiency?.mean?.toFixed(1) || '0';
        const successRate = (data.success_rate * 100).toFixed(1);
        const score = ((parseFloat(efficiency) + parseFloat(successRate)) / 2).toFixed(1);

        return `
            <tr>
                <td>${algorithm}</td>
                <td>${data.experiment_count}</td>
                <td>${successRate}%</td>
                <td>${efficiency}%</td>
                <td>${score}</td>
            </tr>
        `;
    }).join('');
}

/**
 * 加载报告列表
 */
async function loadReportsList() {
    try {
        const response = await fetch('/api/analytics/reports/list');
        const result = await response.json();

        if (result.success) {
            updateReportsTable(result.data);
        } else {
            showNotification('加载报告列表失败', 'error');
        }
    } catch (error) {
        console.error('Error loading reports list:', error);
        showNotification('网络错误：无法加载报告列表', 'error');
    }
}

/**
 * 更新报告表格
 */
function updateReportsTable(reports) {
    const tbody = document.getElementById('reportsTableBody');

    if (reports.length === 0) {
        tbody.innerHTML = `
            <tr><td colspan="5" class="loading-cell">暂无报告</td></tr>
        `;
        return;
    }

    tbody.innerHTML = reports.map(report => `
        <tr>
            <td>${report.report_id}</td>
            <td>${report.report_type}</td>
            <td>${formatDate(report.generated_at)}</td>
            <td>${formatFileSize(report.file_size)}</td>
            <td>
                <button class="btn primary" onclick="downloadReport('${report.report_id}')" style="padding: 4px 8px; font-size: 12px;">
                    下载
                </button>
                <button class="btn secondary" onclick="exportReportExcel('${report.report_id}')" style="padding: 4px 8px; font-size: 12px; margin-left: 4px;">
                    Excel
                </button>
            </td>
        </tr>
    `).join('');
}

/**
 * 格式化文件大小
 */
function formatFileSize(bytes) {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

/**
 * 下载报告
 */
function downloadReport(reportId) {
    window.open(`/api/analytics/reports/${reportId}/download`, '_blank');
}

/**
 * 导出Excel报告
 */
function exportReportExcel(reportId) {
    window.open(`/api/analytics/reports/${reportId}/export/excel`, '_blank');
}

/**
 * 加载部分数据
 */
function loadSectionData(sectionId) {
    switch (sectionId) {
        case 'overview':
            loadDashboardOverview();
            break;
        case 'experiments':
            loadExperiments();
            break;
        case 'trends':
            // 趋势分析按需加载
            break;
        case 'performance':
            // 性能分析按需加载
            break;
        case 'reports':
            loadReportsList();
            break;
    }
}

/**
 * 加载选项卡数据
 */
function loadTabData(tabId) {
    switch (tabId) {
        case 'algorithm-comparison':
            // 算法对比按需加载
            break;
        case 'efficiency-analysis':
            loadEfficiencyAnalysis();
            break;
        case 'optimization-opportunities':
            loadOptimizationOpportunities();
            break;
    }
}

/**
 * 加载效率分析
 */
async function loadEfficiencyAnalysis() {
    try {
        const response = await fetch('/api/analytics/performance/efficiency');
        const result = await response.json();

        if (result.success) {
            updateEfficiencyAnalysis(result.data);
        } else {
            showNotification('效率分析加载失败', 'error');
        }
    } catch (error) {
        console.error('Error loading efficiency analysis:', error);
        showNotification('网络错误：效率分析失败', 'error');
    }
}

/**
 * 更新效率分析
 */
function updateEfficiencyAnalysis(data) {
    // 更新效率统计
    const statsDiv = document.getElementById('efficiencyStats');
    const distribution = data.efficiency_distribution;

    if (distribution && distribution.mean !== undefined) {
        statsDiv.innerHTML = `
            <p><strong>平均效率:</strong> ${distribution.mean.toFixed(1)}%</p>
            <p><strong>中位数:</strong> ${distribution.median.toFixed(1)}%</p>
            <p><strong>标准差:</strong> ${distribution.std.toFixed(1)}</p>
            <p><strong>第一四分位数:</strong> ${distribution.quartiles?.q1?.toFixed(1)}%</p>
            <p><strong>第三四分位数:</strong> ${distribution.quartiles?.q3?.toFixed(1)}%</p>
        `;
    } else {
        statsDiv.innerHTML = '<p>暂无效率统计数据</p>';
    }

    // 更新模式列表
    const patternsList = document.getElementById('patternsList');
    const patterns = data.loading_patterns;

    if (patterns) {
        patternsList.innerHTML = `
            <p><strong>高效率车辆 (>80%):</strong> ${patterns.high_efficiency_vehicles} 辆</p>
            <p><strong>中等效率车辆 (60-80%):</strong> ${patterns.medium_efficiency_vehicles} 辆</p>
            <p><strong>低效率车辆 (<60%):</strong> ${patterns.low_efficiency_vehicles} 辆</p>
            <p><strong>利用不足车辆:</strong> ${patterns.underutilized_vehicles} 辆</p>
        `;
    } else {
        patternsList.innerHTML = '<p>暂无模式数据</p>';
    }
}

/**
 * 加载优化机会
 */
async function loadOptimizationOpportunities() {
    try {
        const response = await fetch('/api/analytics/performance/efficiency');
        const result = await response.json();

        if (result.success) {
            updateOptimizationOpportunities(result.data);
        } else {
            showNotification('优化机会加载失败', 'error');
        }
    } catch (error) {
        console.error('Error loading optimization opportunities:', error);
        showNotification('网络错误：优化机会加载失败', 'error');
    }
}

/**
 * 更新优化机会
 */
function updateOptimizationOpportunities(data) {
    // 更新机会列表
    const opportunitiesList = document.getElementById('opportunitiesList');
    const opportunities = data.optimization_opportunities || [];

    if (opportunities.length > 0) {
        opportunitiesList.innerHTML = opportunities.map(opp => `
            <div class="opportunity-item">
                <i class="fas fa-lightbulb"></i>
                <span>${opp}</span>
            </div>
        `).join('');
    } else {
        opportunitiesList.innerHTML = '<p>当前运营效率良好，暂无明显优化机会</p>';
    }

    // 更新建议列表
    const recommendationsList = document.getElementById('recommendationsList');
    const recommendations = [
        '定期监控装载效率，及时调整装载策略',
        '优化路径规划算法，减少不必要的行驶距离',
        '建立车辆性能基准，识别异常表现',
        '实施动态调度，提高车辆利用率'
    ];

    recommendationsList.innerHTML = recommendations.map(rec => `
        <div class="recommendation-item">
            <i class="fas fa-check-circle"></i>
            <span>${rec}</span>
        </div>
    `).join('');
}

/**
 * 显示通知
 */
function showNotification(message, type = 'info') {
    // 创建通知元素
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.innerHTML = `
        <i class="fas ${getNotificationIcon(type)}"></i>
        <span>${message}</span>
        <button class="notification-close">&times;</button>
    `;

    // 添加到页面
    document.body.appendChild(notification);

    // 设置关闭按钮
    notification.querySelector('.notification-close').addEventListener('click', () => {
        notification.remove();
    });

    // 自动消失
    setTimeout(() => {
        if (notification.parentNode) {
            notification.remove();
        }
    }, 5000);
}

/**
 * 获取通知图标
 */
function getNotificationIcon(type) {
    const icons = {
        'success': 'fa-check-circle',
        'error': 'fa-exclamation-circle',
        'warning': 'fa-exclamation-triangle',
        'info': 'fa-info-circle'
    };
    return icons[type] || 'fa-info-circle';
}