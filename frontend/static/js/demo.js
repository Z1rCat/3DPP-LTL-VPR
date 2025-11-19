/**
 * 演示页面JavaScript功能 - 集成真实API
 * Demo Dashboard JavaScript Functions - Integrated with Real API
 */

class DemoVisualization {
    constructor() {
        this.currentVehicle = 'LARGE_TRUCK_000';
        this.currentVizType = 'single';
        this.charts = {};
        this.realAPIConnector = window.realAPIConnector;
        this.useRealData = true; // 启用真实数据
        this.init();
    }

    /**
     * 初始化演示可视化
     */
    init() {
        this.setupEventListeners();
        this.initializeCharts();
        this.startRealTimeUpdates();

        // 如果有真实API连接器，加载真实数据
        if (this.realAPIConnector && this.useRealData) {
            this.loadRealDataOnStart();
        }
    }

    /**
     * 设置事件监听器
     */
    setupEventListeners() {
        // 页面导航
        document.querySelectorAll('.nav-link').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const sectionId = link.getAttribute('href').substring(1);
                this.switchSection(sectionId);
            });
        });
    }

    /**
     * 切换页面部分
     */
    switchSection(sectionId) {
        // 更新导航状态
        document.querySelectorAll('.nav-link').forEach(link => {
            link.classList.remove('active');
        });
        document.querySelector(`[href="#${sectionId}"]`).classList.add('active');

        // 切换内容区域
        document.querySelectorAll('.section').forEach(section => {
            section.classList.remove('active');
        });
        document.getElementById(sectionId).classList.add('active');

        // 根据当前部分初始化相应的可视化
        switch(sectionId) {
            case 'loading':
                this.initializeLoadingVisualization();
                break;
            case 'analytics':
                this.initializeAnalyticsCharts();
                break;
            case 'comparison':
                this.initializeComparisonCharts();
                break;
        }
    }

    /**
     * 初始化图表
     */
    initializeCharts() {
        this.createTrendChart();
        this.createClassificationChart();
        this.createLoadingTrendChart();
        this.createCostAnalysisChart();
        this.createIterationChart();
    }

    /**
     * 创建趋势图表
     */
    createTrendChart() {
        const ctx = document.getElementById('trendChart');
        if (!ctx) return;

        const hours = Array.from({length: 24}, (_, i) => `${i}:00`);
        const optimizationRates = hours.map(() => Math.random() * 30 + 70);
        const successRates = hours.map(() => Math.random() * 5 + 95);

        this.charts.trend = new Chart(ctx, {
            type: 'line',
            data: {
                labels: hours,
                datasets: [{
                    label: '优化率 (%)',
                    data: optimizationRates,
                    borderColor: '#3498db',
                    backgroundColor: 'rgba(52, 152, 219, 0.1)',
                    tension: 0.4,
                    fill: true
                }, {
                    label: '成功率 (%)',
                    data: successRates,
                    borderColor: '#27ae60',
                    backgroundColor: 'rgba(39, 174, 96, 0.1)',
                    tension: 0.4,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: true,
                        position: 'top',
                        labels: {
                            boxWidth: 12,
                            font: {
                                size: 10
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        display: false
                    },
                    y: {
                        beginAtZero: false,
                        min: 60,
                        max: 100,
                        ticks: {
                            font: {
                                size: 10
                            }
                        }
                    }
                }
            }
        });
    }

    /**
     * 创建分类图表
     */
    createClassificationChart() {
        const ctx = document.getElementById('classificationChart');
        if (!ctx) return;

        this.charts.classification = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['大货物', '中货物', '小货物'],
                datasets: [{
                    data: [15, 20, 10],
                    backgroundColor: ['#e74c3c', '#f39c12', '#3498db'],
                    borderWidth: 2,
                    borderColor: '#fff'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            boxWidth: 12,
                            font: {
                                size: 11
                            }
                        }
                    }
                }
            }
        });
    }

    /**
     * 创建装载率趋势图表
     */
    createLoadingTrendChart() {
        const ctx = document.getElementById('loadingTrendChart');
        if (!ctx) return;

        const days = ['周一', '周二', '周三', '周四', '周五', '周六', '周日'];
        const beforeOptimization = [62, 65, 61, 63, 64, 60, 62];
        const afterOptimization = [85, 87, 84, 86, 88, 83, 85];

        this.charts.loadingTrend = new Chart(ctx, {
            type: 'line',
            data: {
                labels: days,
                datasets: [{
                    label: '优化前',
                    data: beforeOptimization,
                    borderColor: '#e74c3c',
                    backgroundColor: 'rgba(231, 76, 60, 0.1)',
                    tension: 0.4
                }, {
                    label: '优化后',
                    data: afterOptimization,
                    borderColor: '#27ae60',
                    backgroundColor: 'rgba(39, 174, 96, 0.1)',
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: true,
                        position: 'top'
                    }
                },
                scales: {
                    y: {
                        beginAtZero: false,
                        min: 50,
                        max: 100,
                        ticks: {
                            callback: function(value) {
                                return value + '%';
                            }
                        }
                    }
                }
            }
        });
    }

    /**
     * 创建成本分析图表
     */
    createCostAnalysisChart() {
        const ctx = document.getElementById('costAnalysisChart');
        if (!ctx) return;

        this.charts.costAnalysis = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: ['燃油', '人工', '维护', '折旧', '其他'],
                datasets: [{
                    label: '优化前',
                    data: [180, 150, 80, 50, 25],
                    backgroundColor: '#e74c3c',
                    borderColor: '#c0392b',
                    borderWidth: 1
                }, {
                    label: '优化后',
                    data: [120, 110, 60, 30, 10],
                    backgroundColor: '#27ae60',
                    borderColor: '#229954',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: true,
                        position: 'top'
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: function(value) {
                                return '¥' + value;
                            }
                        }
                    }
                }
            }
        });
    }

    /**
     * 创建迭代优化图表
     */
    createIterationChart() {
        const ctx = document.getElementById('iterationChart');
        if (!ctx) return;

        const iterations = Array.from({length: 20}, (_, i) => i + 1);
        const loadingRates = iterations.map(i => {
            // 模拟迭代优化过程
            const baseRate = 62;
            const improvement = Math.min(35, i * 1.8);
            const noise = (Math.random() - 0.5) * 2;
            return Math.max(0, Math.min(100, baseRate + improvement + noise));
        });

        this.charts.iteration = new Chart(ctx, {
            type: 'line',
            data: {
                labels: iterations,
                datasets: [{
                    label: '装载率 (%)',
                    data: loadingRates,
                    borderColor: '#3498db',
                    backgroundColor: 'rgba(52, 152, 219, 0.1)',
                    tension: 0.4,
                    fill: true,
                    pointRadius: 4,
                    pointHoverRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: true,
                        position: 'top'
                    },
                    tooltip: {
                        callbacks: {
                            title: function(context) {
                                return '迭代 ' + context[0].label;
                            },
                            label: function(context) {
                                return '装载率: ' + context.parsed.y.toFixed(1) + '%';
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        title: {
                            display: true,
                            text: '迭代次数'
                        }
                    },
                    y: {
                        beginAtZero: false,
                        min: 50,
                        max: 100,
                        title: {
                            display: true,
                            text: '装载率 (%)'
                        }
                    }
                }
            }
        });
    }

    /**
     * 初始化装载可视化
     */
    initializeLoadingVisualization() {
        this.updateLoadingStats();
        this.loadVehicleVisualization();
    }

    /**
     * 更新装载统计 - 支持真实数据
     */
    async updateLoadingStats() {
        if (this.useRealData && this.realAPIConnector) {
            // 尝试加载真实数据
            try {
                const trucksData = await this.realAPIConnector.getTrucksData();
                if (trucksData && trucksData.length > 0) {
                    this.updateLoadingStatsWithRealData(trucksData);
                    return;
                }
            } catch (error) {
                console.warn('加载真实数据失败，使用模拟数据:', error);
            }
        }

        // 回退到模拟统计数据
        const stats = {
            cargoCount: Math.floor(Math.random() * 20) + 35,
            loadingRate: (Math.random() * 10 + 80).toFixed(1),
            volumeRate: (Math.random() * 8 + 84).toFixed(1),
            weightRate: (Math.random() * 12 + 70).toFixed(1)
        };

        document.getElementById('cargo-count').textContent = stats.cargoCount;
        document.getElementById('loading-rate').textContent = stats.loadingRate + '%';
        document.getElementById('volume-rate').textContent = stats.volumeRate + '%';
        document.getElementById('weight-rate').textContent = stats.weightRate + '%';
    }

    /**
     * 用真实数据更新装载统计
     */
    updateLoadingStatsWithRealData(trucksData) {
        // 计算真实统计
        const totalItems = trucksData.reduce((sum, truck) => sum + (truck.total_items || 0), 0);
        const avgLoadingRate = trucksData.reduce((sum, truck) => sum + (truck.loading_efficiency || 0), 0) / trucksData.length;
        const avgVolumeRate = trucksData.reduce((sum, truck) => sum + (truck.volume_utilization || 0), 0) / trucksData.length;
        const avgWeightRate = avgLoadingRate * 0.9; // 简化计算

        document.getElementById('cargo-count').textContent = totalItems;
        document.getElementById('loading-rate').textContent = avgLoadingRate.toFixed(1) + '%';
        document.getElementById('volume-rate').textContent = avgVolumeRate.toFixed(1) + '%';
        document.getElementById('weight-rate').textContent = avgWeightRate.toFixed(1) + '%';
    }

    /**
     * 加载车辆可视化
     */
    loadVehicleVisualization() {
        const vehicleSelect = document.getElementById('vehicle-select');
        const vizTypeSelect = document.getElementById('viz-type-select');

        if (!vehicleSelect || !vizTypeSelect) return;

        const vehicleId = vehicleSelect.value;
        const vizType = vizTypeSelect.value;

        const iframe = document.getElementById('loading-iframe');
        if (!iframe) return;

        // 根据可视化类型选择不同的文件
        let vizFile = '';
        switch (vizType) {
            case 'single':
                vizFile = `single_category_3dpp_${vehicleId}.html`;
                break;
            case 'multi':
                vizFile = `multi_category_3dpp_0_${vehicleId}.html`;
                break;
            case 'heatmap':
                vizFile = 'loading_efficiency_dashboard.html';
                break;
            case 'analysis':
                vizFile = '3d_efficiency_analysis_20250926_160859.html';
                break;
            default:
                vizFile = `single_category_3dpp_${vehicleId}.html`;
        }

        iframe.src = `/visualizations/${vizFile}`;
    }

    /**
     * 改变可视化类型
     */
    changeVisualizationType() {
        this.loadVehicleVisualization();
    }

    /**
     * 刷新可视化
     */
    refreshVisualization() {
        const container = document.getElementById('loading-viz-container');
        if (container) {
            container.innerHTML = '<div style="text-align: center; padding: 2rem;"><i class="fas fa-spinner fa-spin" style="font-size: 2rem; color: #3498db;"></i><p>刷新可视化中...</p></div>';

            setTimeout(() => {
                container.innerHTML = `
                    <iframe
                        src="/visualizations/single_category_3dpp_${this.currentVehicle}.html"
                        width="100%"
                        height="600px"
                        frameborder="0"
                        id="loading-iframe">
                    </iframe>
                `;
                this.loadVehicleVisualization();
            }, 1000);
        }
    }

    /**
     * 初始化分析图表
     */
    initializeAnalyticsCharts() {
        // 图表已在initializeCharts中创建
    }

    /**
     * 初始化对比图表
     */
    initializeComparisonCharts() {
        // 图表已在initializeCharts中创建
    }

    /**
     * 启动实时更新
     */
    startRealTimeUpdates() {
        // 更新任务统计
        setInterval(() => {
            this.updateTaskStats();
        }, 5000);

        // 更新性能指标
        setInterval(() => {
            this.updatePerformanceIndicators();
        }, 3000);

        // 更新趋势图表
        setInterval(() => {
            this.updateTrendChart();
        }, 10000);
    }

    /**
     * 更新任务统计
     */
    updateTaskStats() {
        const activeTasks = Math.floor(Math.random() * 5) + 1;
        const completedTasks = Math.floor(Math.random() * 50) + 100;
        const successRate = (Math.random() * 2 + 98).toFixed(1);

        document.getElementById('active-tasks').textContent = activeTasks;
        document.getElementById('completed-tasks').textContent = completedTasks;
        document.getElementById('success-rate').textContent = successRate + '%';
    }

    /**
     * 更新性能指标
     */
    updatePerformanceIndicators() {
        const indicators = document.querySelectorAll('.indicator-fill');
        indicators.forEach(indicator => {
            const currentValue = parseInt(indicator.style.width);
            const newValue = Math.max(10, Math.min(90, currentValue + (Math.random() - 0.5) * 10));
            indicator.style.width = newValue + '%';

            const valueElement = indicator.closest('.indicator').querySelector('.indicator-value');
            if (valueElement) {
                valueElement.textContent = Math.round(newValue) + '%';
            }
        });
    }

    /**
     * 更新趋势图表
     */
    updateTrendChart() {
        if (!this.charts.trend) return;

        // 添加新数据点并移除旧数据点
        const newDataPoint = Math.random() * 30 + 70;
        const newSuccessPoint = Math.random() * 5 + 95;

        this.charts.trend.data.datasets[0].data.shift();
        this.charts.trend.data.datasets[0].data.push(newDataPoint);

        this.charts.trend.data.datasets[1].data.shift();
        this.charts.trend.data.datasets[1].data.push(newSuccessPoint);

        this.charts.trend.update('none');
    }
}

/**
 * 全局函数
 */

function toggleFullscreen() {
    if (!document.fullscreenElement) {
        document.documentElement.requestFullscreen().catch(err => {
            console.error('无法进入全屏模式:', err);
        });
    } else {
        document.exitFullscreen();
    }
}

/**
 * 初始化演示功能
 */
document.addEventListener('DOMContentLoaded', () => {
    window.demoVisualization = new DemoVisualization();

    // 监听全屏变化
    document.addEventListener('fullscreenchange', () => {
        if (document.fullscreenElement) {
            document.body.classList.add('fullscreen-mode');
        } else {
            document.body.classList.remove('fullscreen-mode');
        }
    });

    // 添加键盘快捷键
    document.addEventListener('keydown', (e) => {
        // F11 切换全屏
        if (e.key === 'F11') {
            e.preventDefault();
            toggleFullscreen();
        }

        // ESC 退出全屏
        if (e.key === 'Escape' && document.fullscreenElement) {
            document.exitFullscreen();
        }
    });

    // 自动演示模式（可选）
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get('autoplay') === 'true') {
        startAutoDemo();
    }
});

/**
 * 自动演示模式
 */
function startAutoDemo() {
    const sections = ['overview', 'loading', 'routes', 'analytics', 'comparison'];
    let currentSectionIndex = 0;

    function showNextSection() {
        const sectionId = sections[currentSectionIndex];
        const link = document.querySelector(`[href="#${sectionId}"]`);
        if (link) {
            link.click();
        }

        currentSectionIndex = (currentSectionIndex + 1) % sections.length;
    }

    // 每30秒切换一个部分
    setInterval(showNextSection, 30000);

    // 从第一个部分开始
    showNextSection();
}

// ===== 新增：真实数据集成方法 =====

/**
 * 启动时加载真实数据
 */
DemoVisualization.prototype.loadRealDataOnStart = async function() {
    console.log('🔄 正在加载真实数据...');

    try {
        // 等待API连接器加载完数据
        await new Promise(resolve => setTimeout(resolve, 1000));

        // 更新车辆选择器
        await this.updateVehicleSelector();

        // 更新可视化文件列表
        await this.updateVisualizationFileList();

        console.log('✅ 真实数据加载完成');
    } catch (error) {
        console.error('❌ 加载真实数据失败:', error);
    }
};

/**
 * 更新车辆选择器 - 使用真实车辆数据
 */
DemoVisualization.prototype.updateVehicleSelector = async function() {
    const vehicleSelect = document.getElementById('vehicle-select');
    if (!vehicleSelect) return;

    try {
        const trucksData = await this.realAPIConnector.getTrucksData();
        if (trucksData && trucksData.length > 0) {
            // 清空现有选项
            vehicleSelect.innerHTML = '';

            // 添加真实车辆选项
            trucksData.forEach(truck => {
                const option = document.createElement('option');
                option.value = truck.vehicle_id;
                option.textContent = `${truck.vehicle_id} (${truck.loading_efficiency?.toFixed(1) || 0}% 装载率)`;
                vehicleSelect.appendChild(option);
            });

            // 设置默认选中第一个车辆
            if (trucksData.length > 0) {
                this.currentVehicle = trucksData[0].vehicle_id;
                vehicleSelect.value = this.currentVehicle;
            }

            console.log(`🚛 已更新车辆选择器: ${trucksData.length} 辆车`);
        }
    } catch (error) {
        console.warn('更新车辆选择器失败:', error);
    }
};

/**
 * 更新可视化文件列表
 */
DemoVisualization.prototype.updateVisualizationFileList = async function() {
    try {
        const vizFiles = await this.realAPIConnector.getVisualizationFiles();
        if (vizFiles && vizFiles.length > 0) {
            console.log(`📊 发现 ${vizFiles.length} 个可视化文件`);

            // 更新可视化类型选择器
            this.updateVisualizationTypeSelector(vizFiles);
        }
    } catch (error) {
        console.warn('更新可视化文件列表失败:', error);
    }
};

/**
 * 更新可视化类型选择器
 */
DemoVisualization.prototype.updateVisualizationTypeSelector = function(vizFiles) {
    const vizTypeSelect = document.getElementById('viz-type-select');
    if (!vizTypeSelect) return;

    // 分析可用的可视化类型
    const availableTypes = new Set();
    vizFiles.forEach(file => {
        if (file.type !== 'unknown') {
            availableTypes.add(file.type);
        }
    });

    // 为每种类型找到最新文件
    const latestFiles = {};
    availableTypes.forEach(type => {
        const filesOfType = vizFiles.filter(file => file.type === type);
        if (filesOfType.length > 0) {
            latestFiles[type] = filesOfType.reduce((latest, file) =>
                new Date(file.modified_at) > new Date(latest.modified_at) ? file : latest
            );
        }
    });

    // 更新选择器选项
    vizTypeSelect.innerHTML = '';

    // 添加3DPP类型
    if (latestFiles['3dpp']) {
        const option = document.createElement('option');
        option.value = 'single';
        option.textContent = '单品类3D装载可视化';
        vizTypeSelect.appendChild(option);
    }

    // 添加多品类类型
    if (latestFiles['multi_3dpp']) {
        const option = document.createElement('option');
        option.value = 'multi';
        option.textContent = '多品类混合装载可视化';
        vizTypeSelect.appendChild(option);
    }

    // 添加热力图类型
    if (latestFiles['heatmap']) {
        const option = document.createElement('option');
        option.value = 'heatmap';
        option.textContent = '装载密度热力图';
        vizTypeSelect.appendChild(option);
    }

    // 添加效率分析类型
    if (latestFiles['efficiency']) {
        const option = document.createElement('option');
        option.value = 'analysis';
        option.textContent = '装载效率分析';
        vizTypeSelect.appendChild(option);
    }

    // 添加路径地图类型
    if (latestFiles['route']) {
        const option = document.createElement('option');
        option.value = 'route';
        option.textContent = '路径优化地图';
        vizTypeSelect.appendChild(option);
    }
};

/**
 * 运行真实优化算法
 */
DemoVisualization.prototype.runRealOptimization = async function(algorithm = 'integrated') {
    if (!this.realAPIConnector) {
        this.showError('API连接器未初始化');
        return;
    }

    try {
        // 显示优化开始提示
        this.showOptimizationStart();

        // 运行优化
        const taskId = await this.realAPIConnector.runOptimization(algorithm);

        console.log(`🚀 优化任务已启动: ${taskId}`);
    } catch (error) {
        this.showError('启动优化失败: ' + error.message);
    }
};

/**
 * 显示优化开始提示
 */
DemoVisualization.prototype.showOptimizationStart = function() {
    // 创建优化进度显示
    const progressContainer = document.createElement('div');
    progressContainer.className = 'optimization-progress-overlay';
    progressContainer.innerHTML = `
        <div class="optimization-progress-modal">
            <h3>🚀 正在运行优化算法</h3>
            <div class="progress-bar-container">
                <div class="real-progress-fill" style="width: 0%"></div>
            </div>
            <div class="real-progress-text">正在初始化...</div>
            <div class="real-status-indicator status-started">已启动</div>
            <div class="optimization-details">
                <p>算法类型: 集成优化</p>
                <p>数据源: 模拟订单数据</p>
                <p>目标: 最大化装载效率 + 最小化运输成本</p>
            </div>
        </div>
    `;

    document.body.appendChild(progressContainer);

    // 监听优化完成事件
    window.addEventListener('optimizationComplete', (event) => {
        this.hideOptimizationProgress();
        this.showOptimizationComplete(event.detail);
    }, { once: true });
};

/**
 * 隐藏优化进度
 */
DemoVisualization.prototype.hideOptimizationProgress = function() {
    const progressOverlay = document.querySelector('.optimization-progress-overlay');
    if (progressOverlay) {
        progressOverlay.remove();
    }
};

/**
 * 显示优化完成
 */
DemoVisualization.prototype.showOptimizationComplete = function(result) {
    // 创建完成通知
    const completeNotification = document.createElement('div');
    completeNotification.className = 'optimization-complete-notification';
    completeNotification.innerHTML = `
        <div class="notification-content">
            <h3>🎉 优化完成!</h3>
            <div class="optimization-summary">
                <p>总车辆: ${result.total_trucks || 0} 辆</p>
                <p>装载货物: ${result.total_items_processed || 0} 件</p>
                <p>平均效率: ${result.average_loading_efficiency?.toFixed(1) || 0}%</p>
                <p>生成可视化: ${(result.visualization_files || []).length} 个</p>
            </div>
            <button class="btn btn-primary" onclick="this.parentElement.parentElement.remove()">
                查看结果
            </button>
        </div>
    `;

    document.body.appendChild(completeNotification);

    // 自动移除通知
    setTimeout(() => {
        if (completeNotification.parentElement) {
            completeNotification.remove();
        }
    }, 8000);

    // 刷新界面数据
    setTimeout(() => {
        this.updateLoadingStats();
        this.updateVehicleSelector();
        this.loadVehicleVisualization();
    }, 1000);
};

/**
 * 显示错误信息
 */
DemoVisualization.prototype.showError = function(message) {
    console.error('❌', message);

    const errorNotification = document.createElement('div');
    errorNotification.className = 'notification notification-error';
    errorNotification.innerHTML = `
        <div class="notification-content">
            <span class="notification-icon">❌</span>
            <span class="notification-message">${message}</span>
            <button class="notification-close" onclick="this.parentElement.parentElement.remove()">×</button>
        </div>
    `;

    document.body.appendChild(errorNotification);

    setTimeout(() => {
        if (errorNotification.parentElement) {
            errorNotification.remove();
        }
    }, 5000);
};

// 添加全局函数
window.runRealOptimization = function(algorithm = 'integrated') {
    if (window.demoVisualization) {
        return window.demoVisualization.runRealOptimization(algorithm);
    }
};

window.refreshRealData = async function() {
    if (window.demoVisualization) {
        await window.demoVisualization.loadRealDataOnStart();
        await window.demoVisualization.updateLoadingStats();
    }
};

console.log('🎯 Demo可视化已集成真实API支持!');