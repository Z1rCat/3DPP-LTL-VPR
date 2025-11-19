/**
 * 管理员优化控制器
 * Admin Optimization Controller
 *
 * 负责管理优化任务的启动、监控、结果展示等功能
 */

class AdminOptimizationController {
    constructor() {
        this.currentTaskId = null;
        this.websocket = null;
        this.optimizationHistory = [];
        this.currentResult = null;

        // DOM 元素
        this.elements = {
            // 控制面板
            optimizationMode: document.getElementById('optimizationMode'),
            orderCount: document.getElementById('orderCount'),
            dataSource: document.getElementById('dataSource'),
            loadDataBtn: document.getElementById('loadDataBtn'),
            startOptimizationBtn: document.getElementById('startOptimizationBtn'),

            // 数据预览
            dataPreview: document.getElementById('dataPreview'),

            // 进度显示
            progressSection: document.getElementById('progressSection'),
            stepIndicator: document.getElementById('stepIndicator'),
            mainProgressBar: document.getElementById('mainProgressBar'),
            currentStatusMessage: document.getElementById('currentStatusMessage'),
            currentStepInfo: document.getElementById('currentStepInfo'),

            // 结果展示
            resultsSection: document.getElementById('resultsSection'),
            totalLoadingRate: document.getElementById('totalLoadingRate'),
            vehiclesUsed: document.getElementById('vehiclesUsed'),
            optimizationTime: document.getElementById('optimizationTime'),
            efficiencyScore: document.getElementById('efficiencyScore'),
            loadingPlansTableBody: document.getElementById('loadingPlansTableBody'),

            // 操作按钮
            exportResultsBtn: document.getElementById('exportResultsBtn'),
            viewDetailsBtn: document.getElementById('viewDetailsBtn'),
            newOptimizationBtn: document.getElementById('newOptimizationBtn')
        };

        this.init();
    }

    /**
     * 初始化控制器
     */
    init() {
        this.bindEvents();
        this.loadStatistics();
        console.log('[控制器] 管理员优化控制器已初始化');
    }

    /**
     * 绑定事件处理器
     */
    bindEvents() {
        // 数据加载
        this.elements.loadDataBtn.addEventListener('click', () => this.loadDemoData());

        // 优化启动
        this.elements.startOptimizationBtn.addEventListener('click', () => this.startOptimization());

        // 结果操作
        this.elements.exportResultsBtn.addEventListener('click', () => this.exportResults());
        this.elements.viewDetailsBtn.addEventListener('click', () => this.viewDetails());
        this.elements.newOptimizationBtn.addEventListener('click', () => this.resetForNewOptimization());

        // 配置变化监听
        this.elements.optimizationMode.addEventListener('change', () => this.updateConfigInfo());
        this.elements.orderCount.addEventListener('change', () => this.updateConfigInfo());

        // 页面标签切换监听
        document.querySelectorAll('#mainTabs button').forEach(tab => {
            tab.addEventListener('shown.bs.tab', (event) => this.handleTabSwitch(event));
        });
    }

    /**
     * 加载演示数据
     */
    async loadDemoData() {
        try {
            this.elements.loadDataBtn.disabled = true;
            this.elements.loadDataBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>加载中...';

            const orderCount = parseInt(this.elements.orderCount.value);

            const response = await fetch(`/api/optimization-task/demo-data?count=${orderCount}`);
            const result = await response.json();

            if (result.success) {
                this.displayDataPreview(result.data);
                this.showSuccess('数据加载成功', `已加载 ${result.count} 个订单数据`);
            } else {
                throw new Error(result.message || '数据加载失败');
            }
        } catch (error) {
            console.error('[错误] 加载数据失败:', error);
            this.showError('数据加载失败', error.message);
        } finally {
            this.elements.loadDataBtn.disabled = false;
            this.elements.loadDataBtn.innerHTML = '<i class="fas fa-download me-2"></i>加载数据预览';
        }
    }

    /**
     * 显示数据预览
     */
    displayDataPreview(data) {
        if (!data || data.length === 0) {
            this.elements.dataPreview.innerHTML = '<i class="fas fa-exclamation-triangle me-2"></i>暂无数据';
            return;
        }

        // 统计信息
        const stats = {
            total: data.length,
            large: data.filter(item => item.cargo_type === 'large').length,
            medium: data.filter(item => item.cargo_type === 'medium').length,
            small: data.filter(item => item.cargo_type === 'small').length
        };

        // 生成预览HTML
        let previewHTML = `
            <div class="row">
                <div class="col-md-3">
                    <div class="text-center">
                        <h5 class="text-primary">${stats.total}</h5>
                        <small class="text-muted">总订单数</small>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="text-center">
                        <h5 class="success">${stats.large}</h5>
                        <small class="text-muted">大货物</small>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="text-center">
                        <h5 class="warning">${stats.medium}</h5>
                        <small class="text-muted">中货物</small>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="text-center">
                        <h5 class="info">${stats.small}</h5>
                        <small class="text-muted">小货物</small>
                    </div>
                </div>
            </div>
            <hr>
            <div class="table-responsive mt-3">
                <table class="table table-sm">
                    <thead>
                        <tr>
                            <th>订单ID</th>
                            <th>客户</th>
                            <th>类型</th>
                            <th>尺寸(长×宽×高)</th>
                            <th>重量(kg)</th>
                            <th>目的地</th>
                        </tr>
                    </thead>
                    <tbody>
        `;

        // 显示前5个订单
        data.slice(0, 5).forEach(order => {
            previewHTML += `
                <tr>
                    <td><code>${order.order_id}</code></td>
                    <td>${order.customer_name}</td>
                    <td><span class="badge bg-${this.getCargoTypeColor(order.cargo_type)}">${this.getCargoTypeName(order.cargo_type)}</span></td>
                    <td>${order.dimensions.length}×${order.dimensions.width}×${order.dimensions.height}</td>
                    <td>${order.weight}</td>
                    <td>${order.destination}</td>
                </tr>
            `;
        });

        if (data.length > 5) {
            previewHTML += `
                <tr>
                    <td colspan="6" class="text-center text-muted">
                        <i class="fas fa-ellipsis-h"></i> 还有 ${data.length - 5} 个订单...
                    </td>
                </tr>
            `;
        }

        previewHTML += '</tbody></table></div>';
        this.elements.dataPreview.innerHTML = previewHTML;
    }

    /**
     * 启动优化
     */
    async startOptimization() {
        try {
            // 验证配置
            const config = this.getOptimizationConfig();
            if (!this.validateConfig(config)) {
                return;
            }

            // 禁用启动按钮
            this.elements.startOptimizationBtn.disabled = true;
            this.elements.startOptimizationBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>启动中...';

            // 发送启动请求
            const response = await fetch('/api/optimization-task/start', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(config)
            });

            const result = await response.json();

            if (result.success) {
                this.currentTaskId = result.task_id;
                this.showSuccess('优化任务已启动', `任务ID: ${result.task_id}`);

                // 显示进度界面
                this.showProgressInterface();

                // 开始监控进度
                this.startProgressMonitoring(result.task_id);

                // 显示预计时间
                this.showInfo('预计时间', result.estimated_time);

            } else {
                throw new Error(result.message || '启动优化失败');
            }
        } catch (error) {
            console.error('[错误] 启动优化失败:', error);
            this.showError('启动优化失败', error.message);
        } finally {
            // 恢复按钮状态（如果任务未启动）
            if (!this.currentTaskId) {
                this.elements.startOptimizationBtn.disabled = false;
                this.elements.startOptimizationBtn.innerHTML = '<i class="fas fa-play me-2"></i>开始优化';
            }
        }
    }

    /**
     * 开始进度监控
     */
    startProgressMonitoring(taskId) {
        try {
            // 建立WebSocket连接
            const wsUrl = `ws://localhost:8000/api/optimization-task/progress/${taskId}`;
            this.websocket = new WebSocket(wsUrl);

            this.websocket.onopen = () => {
                console.log('[WebSocket] 连接已建立');
            };

            this.websocket.onmessage = (event) => {
                const progress = JSON.parse(event.data);
                this.updateProgress(progress);
            };

            this.websocket.onclose = () => {
                console.log('[WebSocket] 连接已关闭');
            };

            this.websocket.onerror = (error) => {
                console.error('[WebSocket] 连接错误:', error);
                this.showError('WebSocket连接失败', '无法实时监控优化进度，请刷新页面重试');
            };

            // 设置超时检查（5分钟）
            setTimeout(() => {
                if (this.websocket && this.websocket.readyState === WebSocket.OPEN) {
                    this.checkTaskStatus(taskId);
                }
            }, 5 * 60 * 1000);

        } catch (error) {
            console.error('[错误] WebSocket连接失败:', error);
            // 降级到HTTP轮询
            this.startHttpPolling(taskId);
        }
    }

    /**
     * HTTP轮询监控（WebSocket失败时的备选方案）
     */
    startHttpPolling(taskId) {
        console.log('[轮询] 启动HTTP轮询监控');

        const pollInterval = setInterval(async () => {
            try {
                const response = await fetch(`/api/optimization-task/status/${taskId}`);
                const result = await response.json();

                if (result.success) {
                    const task = result.task;
                    this.updateProgress({
                        status: task.status,
                        progress: task.progress,
                        current_step: task.current_step,
                        message: task.message
                    });

                    if (task.status === 'completed' || task.status === 'error') {
                        clearInterval(pollInterval);
                    }
                }
            } catch (error) {
                console.error('[轮询] 获取状态失败:', error);
            }
        }, 2000);
    }

    /**
     * 更新进度显示
     */
    updateProgress(progress) {
        console.log('[进度] 更新:', progress);

        // 更新进度条
        this.elements.mainProgressBar.style.width = `${progress.progress}%`;
        this.elements.mainProgressBar.textContent = `${Math.round(progress.progress)}%`;

        // 更新状态消息
        this.elements.currentStatusMessage.textContent = progress.message || '处理中...';

        // 更新步骤指示器
        this.updateStepIndicator(progress.step || 1, progress.total_steps || 7);

        // 处理完成状态
        if (progress.status === 'completed') {
            this.handleOptimizationCompleted();
        } else if (progress.status === 'error') {
            this.handleOptimizationError(progress.message);
        }
    }

    /**
     * 更新步骤指示器
     */
    updateStepIndicator(currentStep, totalSteps) {
        const steps = this.elements.stepIndicator.querySelectorAll('.step');

        steps.forEach((step, index) => {
            const stepNum = index + 1;
            step.classList.remove('active', 'completed');

            if (stepNum < currentStep) {
                step.classList.add('completed');
            } else if (stepNum === currentStep) {
                step.classList.add('active');
            }
        });
    }

    /**
     * 处理优化完成
     */
    async handleOptimizationCompleted() {
        console.log('[完成] 优化任务已完成');

        // 关闭WebSocket连接
        if (this.websocket) {
            this.websocket.close();
            this.websocket = null;
        }

        try {
            // 获取优化结果
            const response = await fetch(`/api/optimization-task/result/${this.currentTaskId}`);
            const result = await response.json();

            if (result.success) {
                this.currentResult = result.result;
                this.displayResults(result.result);
                this.showSuccess('优化完成', '优化任务已成功完成！');
            } else {
                throw new Error(result.message || '获取结果失败');
            }
        } catch (error) {
            console.error('[错误] 获取结果失败:', error);
            this.showError('获取结果失败', error.message);
        }
    }

    /**
     * 处理优化错误
     */
    handleOptimizationCompleted(errorMessage) {
        console.error('[错误] 优化任务失败:', errorMessage);

        // 关闭WebSocket连接
        if (this.websocket) {
            this.websocket.close();
            this.websocket = null;
        }

        this.showError('优化失败', errorMessage);
        this.resetForNewOptimization();
    }

    /**
     * 显示优化结果
     */
    displayResults(result) {
        console.log('[结果] 显示优化结果:', result);

        // 隐藏进度界面，显示结果界面
        this.elements.progressSection.style.display = 'none';
        this.elements.resultsSection.style.display = 'block';

        // 更新性能指标
        this.elements.totalLoadingRate.textContent = `${result.total_loading_rate || 0}%`;
        this.elements.vehiclesUsed.textContent = result.used_trucks || 0;
        this.elements.optimizationTime.textContent = `${result.optimization_time_seconds || 0}s`;

        // 计算效率评分
        const efficiencyScore = this.calculateEfficiencyScore(result);
        this.elements.efficiencyScore.textContent = efficiencyScore;

        // 显示装载计划表格
        this.displayLoadingPlans(result.loading_plans || []);

        // 添加动画效果
        this.elements.resultsSection.classList.add('fade-in-up');
    }

    /**
     * 显示装载计划表格
     */
    displayLoadingPlans(loadingPlans) {
        const tbody = this.elements.loadingPlansTableBody;
        tbody.innerHTML = '';

        if (!loadingPlans || loadingPlans.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="5" class="text-center text-muted">
                        <i class="fas fa-inbox"></i> 暂无装载计划
                    </td>
                </tr>
            `;
            return;
        }

        loadingPlans.forEach((plan, index) => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>
                    <strong>${plan.truck_id}</strong>
                    <span class="badge bg-success ms-2">${index + 1}</span>
                </td>
                <td>${plan.orders ? plan.orders.length : 0}</td>
                <td>
                    <div class="progress" style="height: 20px;">
                        <div class="progress-bar bg-primary" style="width: ${plan.volume_utilization || 0}%">
                            ${plan.volume_utilization || 0}%
                        </div>
                    </div>
                </td>
                <td>
                    <div class="progress" style="height: 20px;">
                        <div class="progress-bar bg-info" style="width: ${plan.weight_utilization || 0}%">
                            ${plan.weight_utilization || 0}%
                        </div>
                    </div>
                </td>
                <td>
                    <button class="btn btn-sm btn-outline-primary" onclick="adminController.showLoadingPlanDetails('${plan.truck_id}')">
                        <i class="fas fa-eye"></i> 详情
                    </button>
                </td>
            `;
            tbody.appendChild(row);
        });
    }

    /**
     * 导出结果
     */
    async exportResults() {
        if (!this.currentResult) {
            this.showError('无结果可导出', '请先运行优化任务');
            return;
        }

        try {
            const exportData = {
                task_id: this.currentTaskId,
                timestamp: new Date().toISOString(),
                result: this.currentResult,
                config: this.getOptimizationConfig()
            };

            // 创建下载链接
            const blob = new Blob([JSON.stringify(exportData, null, 2)], {
                type: 'application/json'
            });
            const url = URL.createObjectURL(blob);

            const a = document.createElement('a');
            a.href = url;
            a.download = `optimization_result_${this.currentTaskId}.json`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);

            this.showSuccess('导出成功', '结果文件已下载');

        } catch (error) {
            console.error('[错误] 导出失败:', error);
            this.showError('导出失败', error.message);
        }
    }

    /**
     * 查看详情
     */
    viewDetails() {
        if (!this.currentResult) {
            this.showError('无结果可查看', '请先运行优化任务');
            return;
        }

        // 创建详情模态框
        this.showResultDetailsModal(this.currentResult);
    }

    /**
     * 重置为新优化
     */
    resetForNewOptimization() {
        // 重置状态
        this.currentTaskId = null;
        this.currentResult = null;

        // 关闭WebSocket
        if (this.websocket) {
            this.websocket.close();
            this.websocket = null;
        }

        // 隐藏进度和结果界面
        this.elements.progressSection.style.display = 'none';
        this.elements.resultsSection.style.display = 'none';

        // 重置按钮
        this.elements.startOptimizationBtn.disabled = false;
        this.elements.startOptimizationBtn.innerHTML = '<i class="fas fa-play me-2"></i>开始优化';

        // 重置进度条
        this.elements.mainProgressBar.style.width = '0%';
        this.elements.mainProgressBar.textContent = '0%';

        // 重置步骤指示器
        const steps = this.elements.stepIndicator.querySelectorAll('.step');
        steps.forEach(step => step.classList.remove('active', 'completed'));

        this.showInfo('已重置', '可以开始新的优化任务');
    }

    /**
     * 加载统计信息
     */
    async loadStatistics() {
        try {
            const response = await fetch('/api/optimization-task/statistics');
            const result = await response.json();

            if (result.success) {
                console.log('[统计] 加载统计信息成功:', result);
                // 这里可以显示一些统计信息
            }
        } catch (error) {
            console.error('[错误] 加载统计信息失败:', error);
        }
    }

    /**
     * 处理标签切换
     */
    handleTabSwitch(event) {
        const targetTab = event.target.getAttribute('data-bs-target');

        switch (targetTab) {
            case '#monitoring':
                this.loadTaskMonitoring();
                break;
            case '#results':
                this.loadResultsAnalysis();
                break;
            case '#history':
                this.loadOptimizationHistory();
                break;
        }
    }

    /**
     * 辅助方法
     */
    getOptimizationConfig() {
        return {
            optimization_mode: this.elements.optimizationMode.value,
            order_count: parseInt(this.elements.orderCount.value),
            data_source: this.elements.dataSource.value,
            config: {}
        };
    }

    validateConfig(config) {
        if (!config.optimization_mode) {
            this.showError('配置错误', '请选择优化模式');
            return false;
        }
        return true;
    }

    updateConfigInfo() {
        // 可以在这里更新配置相关的UI
    }

    showProgressInterface() {
        this.elements.progressSection.style.display = 'block';
        this.elements.startOptimizationBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>优化中...';
    }

    getCargoTypeColor(type) {
        const colors = {
            'large': 'danger',
            'medium': 'warning',
            'small': 'info'
        };
        return colors[type] || 'secondary';
    }

    getCargoTypeName(type) {
        const names = {
            'large': '大货物',
            'medium': '中货物',
            'small': '小货物'
        };
        return names[type] || '未知';
    }

    calculateEfficiencyScore(result) {
        // 简单的效率评分计算
        const loadingRate = result.total_loading_rate || 0;
        const weightUtil = result.total_weight_utilization || 0;
        const score = (loadingRate * 0.7 + weightUtil * 0.3);
        return score.toFixed(1);
    }

    // 通知方法
    showSuccess(title, message) {
        this.showNotification(title, message, 'success');
    }

    showError(title, message) {
        this.showNotification(title, message, 'danger');
    }

    showInfo(title, message) {
        this.showNotification(title, message, 'info');
    }

    showNotification(title, message, type) {
        // 创建Bootstrap通知
        const alertHTML = `
            <div class="alert alert-${type} alert-dismissible fade show" role="alert">
                <strong>${title}:</strong> ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `;

        // 在页面顶部显示
        const container = document.querySelector('.container-fluid');
        container.insertAdjacentHTML('afterbegin', alertHTML);

        // 自动关闭
        setTimeout(() => {
            const alert = container.querySelector('.alert');
            if (alert) {
                const bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            }
        }, 5000);
    }

    async checkTaskStatus(taskId) {
        try {
            const response = await fetch(`/api/optimization-task/status/${taskId}`);
            const result = await response.json();

            if (result.success && result.task.status === 'completed') {
                this.handleOptimizationCompleted();
            }
        } catch (error) {
            console.error('[检查] 获取任务状态失败:', error);
        }
    }

    // 占位方法（后续实现）
    async loadTaskMonitoring() {
        console.log('[监控] 加载任务监控界面');
    }

    async loadResultsAnalysis() {
        console.log('[分析] 加载结果分析界面');
    }

    async loadOptimizationHistory() {
        console.log('[历史] 加载优化历史');
    }

    showLoadingPlanDetails(truckId) {
        console.log('[详情] 显示装载计划详情:', truckId);
        // TODO: 实现详情显示
    }

    showResultDetailsModal(result) {
        console.log('[详情] 显示结果详情:', result);
        // TODO: 实现详情模态框
    }
}

// 初始化控制器
let adminController;
document.addEventListener('DOMContentLoaded', () => {
    adminController = new AdminOptimizationController();
});