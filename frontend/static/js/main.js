/**
 * 主应用程序逻辑
 * Main Application Logic
 */

class LogisticsApp {
    constructor() {
        this.currentSection = 'dashboard';
        this.optimizationTasks = new Map();
        this.init();
    }

    /**
     * 初始化应用程序
     */
    init() {
        this.setupNavigation();
        this.setupOptimizationForm();
        this.loadDashboardData();
        this.setupAutoRefresh();

        // 页面加载完成后显示仪表盘
        this.showSection('dashboard');
    }

    /**
     * 设置导航功能
     */
    setupNavigation() {
        const navLinks = document.querySelectorAll('.nav-link');

        navLinks.forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const sectionId = link.getAttribute('href').substring(1);
                this.showSection(sectionId);

                // 更新导航状态
                navLinks.forEach(l => l.classList.remove('active'));
                link.classList.add('active');
            });
        });
    }

    /**
     * 显示指定部分
     */
    showSection(sectionId) {
        // 隐藏所有部分
        document.querySelectorAll('.section').forEach(section => {
            section.classList.remove('active');
        });

        // 显示目标部分
        const targetSection = document.getElementById(sectionId);
        if (targetSection) {
            targetSection.classList.add('active');
            this.currentSection = sectionId;

            // 根据部分执行特定的加载逻辑
            this.onSectionChange(sectionId);
        }
    }

    /**
     * 部分切换时的处理
     */
    onSectionChange(sectionId) {
        switch (sectionId) {
            case 'dashboard':
                this.loadDashboardData();
                break;
            case 'visualizations':
                // 可视化管理器会自动处理
                break;
            case 'optimization':
                this.loadOptimizationHistory();
                this.loadAvailableAlgorithms();
                break;
            case 'api':
                // API文档是静态的
                break;
        }
    }

    /**
     * 加载仪表盘数据
     */
    async loadDashboardData() {
        try {
            // 加载数据摘要
            await this.loadDataSummary();

            // 检查系统状态
            await this.checkSystemStatus();

        } catch (error) {
            console.error('加载仪表盘数据失败:', error);
        }
    }

    /**
     * 加载数据摘要
     */
    async loadDataSummary() {
        try {
            const response = await logisticsAPI.getDataSummary();

            if (response.success) {
                const data = response.data;

                this.updateElement('total-trucks', data.total_trucks || 0);
                this.updateElement('total-items', this.formatNumber(data.total_items || 0));
                this.updateElement('avg-efficiency', `${(data.average_loading_efficiency || 0).toFixed(1)}%`);
                this.updateElement('total-distance', `${(data.total_distance_km || 0).toFixed(1)} km`);
            }

        } catch (error) {
            console.error('加载数据摘要失败:', error);
            this.updateElement('total-trucks', 'N/A');
            this.updateElement('total-items', 'N/A');
            this.updateElement('avg-efficiency', 'N/A');
            this.updateElement('total-distance', 'N/A');
        }
    }

    /**
     * 检查系统状态
     */
    async checkSystemStatus() {
        try {
            // 检查API状态
            const health = await logisticsAPI.healthCheck();
            this.updateStatus('api-status', health.status === 'healthy' ? 'online' : 'offline');

            // 检查可视化系统
            const vizStats = await logisticsAPI.getVisualizationStats();
            this.updateStatus('viz-status', vizStats.success ? 'online' : 'offline');

            // 模拟检查优化引擎状态
            this.updateStatus('engine-status', 'online');

        } catch (error) {
            console.error('检查系统状态失败:', error);
            this.updateStatus('api-status', 'offline');
            this.updateStatus('viz-status', 'offline');
            this.updateStatus('engine-status', 'offline');
        }
    }

    /**
     * 更新状态标识
     */
    updateStatus(elementId, status) {
        const element = document.getElementById(elementId);
        if (!element) return;

        const statusText = {
            'online': '在线',
            'offline': '离线',
            'checking': '检查中...'
        };

        element.textContent = statusText[status] || status;
        element.className = `status-badge ${status}`;
    }

    /**
     * 设置优化表单
     */
    setupOptimizationForm() {
        const form = document.getElementById('optimization-form');
        if (!form) return;

        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            await this.submitOptimizationTask();
        });
    }

    /**
     * 提交优化任务
     */
    async submitOptimizationTask() {
        const algorithm = document.getElementById('algorithm').value;
        const dataSource = document.getElementById('data-source').value;
        const generateViz = document.getElementById('generate-viz').checked;
        const submitBtn = document.querySelector('.submit-btn');

        if (!algorithm || !dataSource) {
            alert('请填写所有必填字段');
            return;
        }

        try {
            // 更新按钮状态
            const originalHTML = submitBtn.innerHTML;
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 启动中...';
            submitBtn.disabled = true;

            const request = {
                algorithm: algorithm,
                data_source: dataSource,
                generate_visualizations: generateViz,
                parameters: {}
            };

            const response = await logisticsAPI.runOptimization(request);

            if (response.success) {
                const taskId = response.data.task_id;

                alert(`优化任务已启动！\n任务ID: ${taskId}\n预估时间: ${response.data.estimated_duration_minutes} 分钟`);

                // 开始监控任务进度
                this.monitorOptimizationTask(taskId);

                // 重置表单
                document.getElementById('optimization-form').reset();

                // 刷新历史列表
                this.loadOptimizationHistory();
            }

        } catch (error) {
            console.error('启动优化任务失败:', error);
            alert(`启动优化任务失败: ${error.message}`);

        } finally {
            submitBtn.innerHTML = originalHTML;
            submitBtn.disabled = false;
        }
    }

    /**
     * 监控优化任务进度
     */
    async monitorOptimizationTask(taskId) {
        try {
            await logisticsAPI.pollTaskStatus(
                taskId,
                (statusData) => {
                    console.log(`任务 ${taskId} 状态更新:`, statusData);

                    // 更新历史列表中的任务状态
                    this.updateTaskInHistory(taskId, statusData);
                },
                60, // 最多轮询60次
                5000 // 每5秒轮询一次
            );

        } catch (error) {
            console.error(`任务 ${taskId} 监控失败:`, error);
        }
    }

    /**
     * 更新历史列表中的任务
     */
    updateTaskInHistory(taskId, statusData) {
        const taskElement = document.querySelector(`[data-task-id="${taskId}"]`);
        if (!taskElement) return;

        const statusElement = taskElement.querySelector('.task-status');
        const messageElement = taskElement.querySelector('.task-message');

        if (statusElement) {
            statusElement.textContent = logisticsAPI.getTaskStatusName(statusData.status);
            statusElement.className = `task-status ${logisticsAPI.getTaskStatusClass(statusData.status)}`;
        }

        if (messageElement) {
            messageElement.textContent = statusData.message;
        }

        // 如果任务完成，添加查看结果按钮
        if (statusData.status === 'completed') {
            this.addResultButton(taskElement, taskId);
        }
    }

    /**
     * 添加查看结果按钮
     */
    addResultButton(taskElement, taskId) {
        const existingBtn = taskElement.querySelector('.result-btn');
        if (existingBtn) return;

        const button = document.createElement('button');
        button.className = 'result-btn';
        button.innerHTML = '<i class="fas fa-eye"></i> 查看结果';
        button.onclick = () => this.showOptimizationResult(taskId);

        const taskActions = taskElement.querySelector('.task-actions');
        if (taskActions) {
            taskActions.appendChild(button);
        } else {
            taskElement.appendChild(button);
        }
    }

    /**
     * 显示优化结果
     */
    async showOptimizationResult(taskId) {
        try {
            const response = await logisticsAPI.getOptimizationResult(taskId);

            if (response.success) {
                const result = response.data;

                // 创建结果显示模态框
                this.showResultModal(result);
            }

        } catch (error) {
            console.error('获取优化结果失败:', error);
            alert(`获取优化结果失败: ${error.message}`);
        }
    }

    /**
     * 显示结果模态框
     */
    showResultModal(result) {
        const modal = document.createElement('div');
        modal.className = 'modal';
        modal.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <h3>优化结果</h3>
                    <button class="modal-close" onclick="this.closest('.modal').remove()">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                <div class="modal-body">
                    <div class="result-grid">
                        <div class="result-item">
                            <strong>算法:</strong> ${result.algorithm_used}
                        </div>
                        <div class="result-item">
                            <strong>处理卡车:</strong> ${result.total_trucks} 辆
                        </div>
                        <div class="result-item">
                            <strong>处理货物:</strong> ${this.formatNumber(result.total_items_processed)} 件
                        </div>
                        <div class="result-item">
                            <strong>平均装载率:</strong> ${result.average_loading_efficiency.toFixed(1)}%
                        </div>
                        <div class="result-item">
                            <strong>总距离:</strong> ${result.total_distance_km.toFixed(1)} km
                        </div>
                        <div class="result-item">
                            <strong>优化耗时:</strong> ${result.optimization_time_seconds.toFixed(1)} 秒
                        </div>
                    </div>

                    <h4>生成的文件:</h4>
                    <div class="file-list">
                        ${result.visualization_files.map(file =>
                            `<div class="file-item">
                                <i class="fas fa-chart-line"></i>
                                <a href="/visualizations/${file}" target="_blank">${file}</a>
                            </div>`
                        ).join('')}
                        ${result.data_files.map(file =>
                            `<div class="file-item">
                                <i class="fas fa-file-alt"></i>
                                <span>${file}</span>
                            </div>`
                        ).join('')}
                    </div>
                </div>
                <div class="modal-footer">
                    <button class="btn btn-secondary" onclick="this.closest('.modal').remove()">
                        关闭
                    </button>
                </div>
            </div>
        `;

        document.body.appendChild(modal);

        // 点击背景关闭
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.remove();
            }
        });
    }

    /**
     * 加载优化历史
     */
    async loadOptimizationHistory() {
        const historyContainer = document.getElementById('history-list');
        if (!historyContainer) return;

        try {
            historyContainer.innerHTML = `
                <div class="loading-placeholder">
                    <i class="fas fa-spinner fa-spin"></i>
                    <p>加载任务历史中...</p>
                </div>
            `;

            const response = await logisticsAPI.getOptimizationHistory({ limit: 20 });

            if (response.success && response.data.length > 0) {
                const historyHTML = response.data.map(task => this.createTaskHistoryItem(task)).join('');
                historyContainer.innerHTML = historyHTML;
            } else {
                historyContainer.innerHTML = `
                    <div class="loading-placeholder">
                        <i class="fas fa-history"></i>
                        <p>暂无任务历史</p>
                    </div>
                `;
            }

        } catch (error) {
            console.error('加载优化历史失败:', error);
            historyContainer.innerHTML = `
                <div class="loading-placeholder">
                    <i class="fas fa-exclamation-triangle" style="color: #dc3545;"></i>
                    <p>加载失败</p>
                </div>
            `;
        }
    }

    /**
     * 创建任务历史项
     */
    createTaskHistoryItem(task) {
        const statusClass = logisticsAPI.getTaskStatusClass(task.status);
        const statusName = logisticsAPI.getTaskStatusName(task.status);
        const createdTime = logisticsAPI.formatDateTime(task.created_at);

        return `
            <div class="task-item ${statusClass}" data-task-id="${task.task_id}">
                <div class="task-header">
                    <span class="task-id">${task.task_id}</span>
                    <span class="task-status ${statusClass}">${statusName}</span>
                </div>
                <div class="task-meta">
                    <div class="task-message">${task.message}</div>
                    <div>创建时间: ${createdTime}</div>
                </div>
                <div class="task-actions">
                    ${task.has_result ? `<button class="result-btn" onclick="app.showOptimizationResult('${task.task_id}')">
                        <i class="fas fa-eye"></i> 查看结果
                    </button>` : ''}
                </div>
            </div>
        `;
    }

    /**
     * 加载可用算法
     */
    async loadAvailableAlgorithms() {
        const algorithmSelect = document.getElementById('algorithm');
        if (!algorithmSelect) return;

        try {
            const response = await logisticsAPI.getAvailableAlgorithms();

            if (response.success) {
                const options = response.data.map(alg =>
                    `<option value="${alg.id}">${alg.name} - ${alg.description}</option>`
                ).join('');

                algorithmSelect.innerHTML = '<option value="">请选择算法...</option>' + options;
            }

        } catch (error) {
            console.error('加载算法列表失败:', error);
        }
    }

    /**
     * 设置自动刷新
     */
    setupAutoRefresh() {
        // 每30秒自动刷新仪表盘数据
        setInterval(() => {
            if (this.currentSection === 'dashboard') {
                this.loadDashboardData();
            }
        }, 30000);
    }

    /**
     * 更新元素内容
     */
    updateElement(id, content) {
        const element = document.getElementById(id);
        if (element) {
            element.textContent = content;
        }
    }

    /**
     * 格式化数字
     */
    formatNumber(num) {
        return new Intl.NumberFormat('zh-CN').format(num);
    }
}

// 页面加载完成后初始化应用
document.addEventListener('DOMContentLoaded', () => {
    window.app = new LogisticsApp();
});

// 全局函数供HTML调用
function refreshVisualizations() {
    if (window.vizManager) {
        window.vizManager.refreshVisualizations();
    }
}