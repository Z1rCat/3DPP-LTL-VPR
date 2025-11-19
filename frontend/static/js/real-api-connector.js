/**
 * 真实API连接器 - 连接前端到后端优化系统
 * Real API Connector - Connect Frontend to Backend Optimization System
 */

class RealAPIConnector {
    constructor() {
        this.baseURL = '';
        this.currentOptimizationTask = null;
        this.optimizationHistory = [];
        this.realDataCache = {};
        this.init();
    }

    /**
     * 初始化API连接器
     */
    init() {
        console.log('🔗 初始化真实API连接器');
        this.loadExistingData();
    }

    /**
     * 加载现有的数据和可视化文件
     */
    async loadExistingData() {
        try {
            // 获取可视化文件列表
            const vizResponse = await fetch('/api/visualizations/list');
            if (vizResponse.ok) {
                const vizResult = await vizResponse.json();
                if (vizResult.success) {
                    this.realDataCache.visualizations = vizResult.data;
                    console.log(`📊 发现 ${vizResult.data.length} 个可视化文件`);
                }
            }

            // 获取卡车数据
            const trucksResponse = await fetch('/api/data/trucks?limit=20');
            if (trucksResponse.ok) {
                const trucksResult = await trucksResponse.json();
                if (trucksResult.success) {
                    this.realDataCache.trucks = trucksResult.data;
                    console.log(`🚛 发现 ${trucksResult.data.length} 辆卡车数据`);
                }
            }

            // 获取路径数据
            const routesResponse = await fetch('/api/data/routes?limit=20');
            if (routesResponse.ok) {
                const routesResult = await routesResponse.json();
                if (routesResult.success) {
                    this.realDataCache.routes = routesResult.data;
                    console.log(`🗺️ 发现 ${routesResult.data.length} 条路径数据`);
                }
            }

            // 获取可用算法
            const algorithmsResponse = await fetch('/api/optimization/algorithms');
            if (algorithmsResponse.ok) {
                const algorithmsResult = await algorithmsResponse.json();
                if (algorithmsResult.success) {
                    this.realDataCache.algorithms = algorithmsResult.data;
                    console.log(`⚡ 发现 ${algorithmsResult.data.length} 个可用算法`);
                }
            }

        } catch (error) {
            console.error('❌ 加载现有数据失败:', error);
        }
    }

    /**
     * 运行真实优化算法
     * @param {string} algorithm - 算法类型
     * @param {string} dataSource - 数据源
     * @returns {Promise<string>} 任务ID
     */
    async runOptimization(algorithm = 'integrated', dataSource = 'simulated_data.xlsx') {
        try {
            this.showLoading('正在启动优化算法...');

            const requestBody = {
                algorithm: algorithm,
                data_source: dataSource,
                parameters: {
                    max_trucks: 20,
                    optimization_time_limit: 300,
                    enable_visualization: true,
                    enable_route_optimization: true
                }
            };

            const response = await fetch('/api/optimization/run', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(requestBody)
            });

            const result = await response.json();

            if (result.success) {
                this.currentOptimizationTask = result.data.task_id;
                console.log(`✅ 优化任务已启动: ${this.currentOptimizationTask}`);

                // 开始监控任务进度
                this.monitorOptimizationProgress(this.currentOptimizationTask);

                return this.currentOptimizationTask;
            } else {
                throw new Error(result.message || '启动优化失败');
            }

        } catch (error) {
            console.error('❌ 运行优化失败:', error);
            this.showError('启动优化算法失败: ' + error.message);
            throw error;
        }
    }

    /**
     * 监控优化任务进度
     * @param {string} taskId - 任务ID
     */
    async monitorOptimizationProgress(taskId) {
        const checkProgress = async () => {
            try {
                const response = await fetch(`/api/optimization/status/${taskId}`);
                const result = await response.json();

                if (result.success) {
                    const { status, progress, message } = result.data;

                    this.updateProgress(status, progress, message);
                    console.log(`📊 任务进度: ${progress}% - ${message}`);

                    if (status === 'completed') {
                        // 任务完成，获取结果
                        await this.getOptimizationResult(taskId);
                        return;
                    } else if (status === 'failed') {
                        this.showError('优化任务失败: ' + message);
                        return;
                    }

                    // 继续监控
                    setTimeout(checkProgress, 2000);
                } else {
                    console.error('❌ 获取任务状态失败:', result.message);
                }

            } catch (error) {
                console.error('❌ 监控进度失败:', error);
            }
        };

        // 开始监控
        setTimeout(checkProgress, 1000);
    }

    /**
     * 获取优化结果
     * @param {string} taskId - 任务ID
     */
    async getOptimizationResult(taskId) {
        try {
            const response = await fetch(`/api/optimization/result/${taskId}`);
            const result = await response.json();

            if (result.success) {
                console.log('🎉 优化完成!', result.data);
                this.realDataCache.latestOptimizationResult = result.data;
                this.optimizationHistory.push(result.data);

                // 刷新可视化文件列表
                await this.loadExistingData();

                // 显示完成通知
                this.showSuccess('优化完成! 已生成新的可视化文件');

                // 触发UI更新
                this.onOptimizationComplete(result.data);

                return result.data;
            } else {
                throw new Error(result.message || '获取优化结果失败');
            }

        } catch (error) {
            console.error('❌ 获取优化结果失败:', error);
            this.showError('获取优化结果失败: ' + error.message);
        }
    }

    /**
     * 获取最新的可视化文件列表
     * @param {string} typeFilter - 类型过滤
     * @returns {Promise<Array>} 可视化文件列表
     */
    async getVisualizationFiles(typeFilter = null) {
        try {
            const url = typeFilter
                ? `/api/visualizations/list?type_filter=${typeFilter}&limit=50`
                : '/api/visualizations/list?limit=50';

            const response = await fetch(url);
            const result = await response.json();

            if (result.success) {
                this.realDataCache.visualizations = result.data;
                return result.data;
            } else {
                console.error('❌ 获取可视化文件失败:', result.message);
                return [];
            }

        } catch (error) {
            console.error('❌ 获取可视化文件失败:', error);
            return [];
        }
    }

    /**
     * 获取卡车数据
     * @param {string} truckType - 卡车类型过滤
     * @returns {Promise<Array>} 卡车数据列表
     */
    async getTrucksData(truckType = null) {
        try {
            const url = truckType
                ? `/api/data/trucks?truck_type=${truckType}&limit=50`
                : '/api/data/trucks?limit=50';

            const response = await fetch(url);
            const result = await response.json();

            if (result.success) {
                this.realDataCache.trucks = result.data;
                return result.data;
            } else {
                console.error('❌ 获取卡车数据失败:', result.message);
                return [];
            }

        } catch (error) {
            console.error('❌ 获取卡车数据失败:', error);
            return [];
        }
    }

    /**
     * 获取路径数据
     * @param {string} truckType - 卡车类型过滤
     * @returns {Promise<Array>} 路径数据列表
     */
    async getRoutesData(truckType = null) {
        try {
            const url = truckType
                ? `/api/data/routes?truck_type=${truckType}&limit=50`
                : '/api/data/routes?limit=50';

            const response = await fetch(url);
            const result = await response.json();

            if (result.success) {
                this.realDataCache.routes = result.data;
                return result.data;
            } else {
                console.error('❌ 获取路径数据失败:', result.message);
                return [];
            }

        } catch (error) {
            console.error('❌ 获取路径数据失败:', error);
            return [];
        }
    }

    /**
     * 获取特定车辆的详细数据
     * @param {string} vehicleId - 车辆ID
     * @returns {Promise<Object>} 车辆详细数据
     */
    async getVehicleDetail(vehicleId) {
        try {
            const response = await fetch(`/api/data/trucks/${vehicleId}`);
            const result = await response.json();

            if (result.success) {
                return result.data;
            } else {
                console.error('❌ 获取车辆详情失败:', result.message);
                return null;
            }

        } catch (error) {
            console.error('❌ 获取车辆详情失败:', error);
            return null;
        }
    }

    /**
     * 获取优化任务历史
     * @returns {Promise<Array>} 任务历史列表
     */
    async getOptimizationHistory() {
        try {
            const response = await fetch('/api/optimization/history?limit=20');
            const result = await response.json();

            if (result.success) {
                this.optimizationHistory = result.data;
                return result.data;
            } else {
                console.error('❌ 获取优化历史失败:', result.message);
                return [];
            }

        } catch (error) {
            console.error('❌ 获取优化历史失败:', error);
            return [];
        }
    }

    /**
     * 更新进度显示
     * @param {string} status - 状态
     * @param {number} progress - 进度百分比
     * @param {string} message - 消息
     */
    updateProgress(status, progress, message) {
        // 更新进度条
        const progressBar = document.querySelector('.real-progress-fill');
        if (progressBar) {
            progressBar.style.width = `${progress}%`;
        }

        // 更新进度文本
        const progressText = document.querySelector('.real-progress-text');
        if (progressText) {
            progressText.textContent = `${message} (${progress}%)`;
        }

        // 更新状态指示器
        const statusIndicator = document.querySelector('.real-status-indicator');
        if (statusIndicator) {
            statusIndicator.className = `real-status-indicator status-${status}`;
            statusIndicator.textContent = this.getStatusText(status);
        }
    }

    /**
     * 获取状态文本
     * @param {string} status - 状态
     * @returns {string} 状态文本
     */
    getStatusText(status) {
        const statusMap = {
            'started': '已启动',
            'running': '运行中',
            'completed': '已完成',
            'failed': '失败'
        };
        return statusMap[status] || status;
    }

    /**
     * 显示加载状态
     * @param {string} message - 加载消息
     */
    showLoading(message) {
        console.log('⏳', message);
        // 可以在这里添加UI加载提示
    }

    /**
     * 显示成功消息
     * @param {string} message - 成功消息
     */
    showSuccess(message) {
        console.log('✅', message);
        // 可以在这里添加UI成功提示
        this.showNotification(message, 'success');
    }

    /**
     * 显示错误消息
     * @param {string} message - 错误消息
     */
    showError(message) {
        console.error('❌', message);
        // 可以在这里添加UI错误提示
        this.showNotification(message, 'error');
    }

    /**
     * 显示通知
     * @param {string} message - 消息内容
     * @param {string} type - 通知类型 (success, error, info)
     */
    showNotification(message, type = 'info') {
        // 创建通知元素
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <div class="notification-content">
                <span class="notification-icon">
                    ${type === 'success' ? '✅' : type === 'error' ? '❌' : 'ℹ️'}
                </span>
                <span class="notification-message">${message}</span>
                <button class="notification-close" onclick="this.parentElement.parentElement.remove()">×</button>
            </div>
        `;

        // 添加到页面
        document.body.appendChild(notification);

        // 自动移除
        setTimeout(() => {
            if (notification.parentElement) {
                notification.remove();
            }
        }, 5000);
    }

    /**
     * 优化完成回调
     * @param {Object} result - 优化结果
     */
    onOptimizationComplete(result) {
        // 刷新可视化列表
        if (window.demoVisualization) {
            window.demoVisualization.refreshVisualization();
        }

        // 更新统计图表
        this.updateStatisticsWithRealData(result);

        // 触发自定义事件
        window.dispatchEvent(new CustomEvent('optimizationComplete', {
            detail: result
        }));
    }

    /**
     * 用真实数据更新统计图表
     * @param {Object} result - 优化结果
     */
    updateStatisticsWithRealData(result) {
        // 如果有demo可视化实例，更新其数据
        if (window.demoVisualization && window.demoVisualization.charts) {
            // 更新任务统计
            const activeTasksElement = document.getElementById('active-tasks');
            if (activeTasksElement) {
                activeTasksElement.textContent = '0'; // 任务完成后无活跃任务
            }

            const completedTasksElement = document.getElementById('completed-tasks');
            if (completedTasksElement) {
                const currentCount = parseInt(completedTasksElement.textContent) || 0;
                completedTasksElement.textContent = currentCount + 1;
            }

            // 用真实数据更新图表
            this.updateChartsWithRealData(result);
        }
    }

    /**
     * 用真实数据更新图表
     * @param {Object} result - 优化结果
     */
    updateChartsWithRealData(result) {
        try {
            // 更新分类图表
            if (result.cargo_classification) {
                this.updateClassificationChart(result.cargo_classification);
            }

            // 更新装载率图表
            if (result.loading_efficiency) {
                this.updateLoadingEfficiencyChart(result.loading_efficiency);
            }

            // 更新成本分析图表
            if (result.cost_analysis) {
                this.updateCostAnalysisChart(result.cost_analysis);
            }

        } catch (error) {
            console.error('❌ 更新图表失败:', error);
        }
    }

    /**
     * 更新分类图表
     * @param {Object} classification - 分类数据
     */
    updateClassificationChart(classification) {
        if (!window.demoVisualization || !window.demoVisualization.charts.classification) return;

        const chart = window.demoVisualization.charts.classification;
        const data = [
            classification.large_cargo_count || 0,
            classification.medium_cargo_count || 0,
            classification.small_cargo_count || 0
        ];

        chart.data.datasets[0].data = data;
        chart.update();
    }

    /**
     * 更新装载效率图表
     * @param {Object} efficiency - 效率数据
     */
    updateLoadingEfficiencyChart(efficiency) {
        if (!window.demoVisualization || !window.demoVisualization.charts.loadingTrend) return;

        const chart = window.demoVisualization.charts.loadingTrend;
        if (efficiency.average_efficiency !== undefined) {
            // 添加新的数据点
            const newValue = efficiency.average_efficiency;
            chart.data.datasets[1].data.push(newValue);

            // 保持数据长度
            if (chart.data.datasets[1].data.length > 7) {
                chart.data.datasets[1].data.shift();
            }

            chart.update();
        }
    }

    /**
     * 更新成本分析图表
     * @param {Object} costAnalysis - 成本数据
     */
    updateCostAnalysisChart(costAnalysis) {
        if (!window.demoVisualization || !window.demoVisualization.charts.costAnalysis) return;

        const chart = window.demoVisualization.charts.costAnalysis;
        const data = [
            costAnalysis.fuel_cost || 0,
            costAnalysis.labor_cost || 0,
            costAnalysis.maintenance_cost || 0,
            costAnalysis.depreciation_cost || 0,
            costAnalysis.other_cost || 0
        ];

        chart.data.datasets[1].data = data;
        chart.update();
    }

    /**
     * 获取可用的可视化文件类型
     * @returns {Array} 可视化类型列表
     */
    getAvailableVisualizationTypes() {
        const vizFiles = this.realDataCache.visualizations || [];
        const types = [...new Set(vizFiles.map(file => file.type))];
        return types.filter(type => type !== 'unknown');
    }

    /**
     * 获取特定类型的可视化文件
     * @param {string} type - 可视化类型
     * @returns {Array} 匹配的文件列表
     */
    getVisualizationFilesByType(type) {
        const vizFiles = this.realDataCache.visualizations || [];
        return vizFiles.filter(file => file.type === type);
    }

    /**
     * 获取最新的可视化文件
     * @param {string} type - 可视化类型（可选）
     * @returns {Object|null} 最新的文件
     */
    getLatestVisualizationFile(type = null) {
        const files = type ? this.getVisualizationFilesByType(type) : (this.realDataCache.visualizations || []);

        if (files.length === 0) return null;

        return files.reduce((latest, file) => {
            return new Date(file.modified_at) > new Date(latest.modified_at) ? file : latest;
        });
    }
}

// 创建全局实例
window.realAPIConnector = new RealAPIConnector();

// 添加全局函数
window.runRealOptimization = async function(algorithm = 'integrated') {
    return await window.realAPIConnector.runOptimization(algorithm);
};

window.getRealVisualizationFiles = async function(typeFilter = null) {
    return await window.realAPIConnector.getVisualizationFiles(typeFilter);
};

window.getRealTrucksData = async function(truckType = null) {
    return await window.realAPIConnector.getTrucksData(truckType);
};

window.getRealRoutesData = async function(truckType = null) {
    return await window.realAPIConnector.getRoutesData(truckType);
};

console.log('🎉 真实API连接器已加载! 可以通过 window.realAPIConnector 访问');