/**
 * 巧满装载平台 - 管理员控制台JavaScript
 * Modern Admin Dashboard JavaScript
 */

class AdminDashboard {
    constructor() {
        this.currentPage = 'dashboard';
        this.sidebarCollapsed = false;
        this.notifications = [];
        this.refreshInterval = null;
        this.charts = {};

        this.init();
    }

    // 初始化方法
    init() {
        this.bindEvents();
        this.loadInitialData();
        this.initCharts();
        this.checkSystemHealth();
        this.startPeriodicRefresh();
        this.setupFormHandlers();
        this.setupFileUpload();

        // 页面加载完成后显示仪表盘
        document.getElementById('dashboard-page').classList.add('active');
    }

    // 绑定事件监听器
    bindEvents() {
        // 侧边栏切换
        const sidebarToggle = document.getElementById('sidebarToggle');
        if (sidebarToggle) {
            sidebarToggle.addEventListener('click', () => this.toggleSidebar());
        }

        // 导航链接
        document.querySelectorAll('.nav-link').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const page = link.getAttribute('data-page');
                this.navigateToPage(page);
            });
        });

        // 全局搜索
        const globalSearch = document.getElementById('globalSearch');
        if (globalSearch) {
            globalSearch.addEventListener('input', (e) => this.handleGlobalSearch(e.target.value));
        }

        // 通知面板
        const notificationBtn = document.getElementById('notificationBtn');
        const notificationPanel = document.getElementById('notificationPanel');
        const closeNotificationPanel = document.getElementById('closeNotificationPanel');

        if (notificationBtn) {
            notificationBtn.addEventListener('click', () => this.toggleNotificationPanel());
        }

        if (closeNotificationPanel) {
            closeNotificationPanel.addEventListener('click', () => this.closeNotificationPanel());
        }

        // 仪表盘刷新按钮
        const refreshDashboard = document.getElementById('refreshDashboard');
        if (refreshDashboard) {
            refreshDashboard.addEventListener('click', () => this.refreshDashboardData());
        }

        // 快速操作按钮
        document.querySelectorAll('.quick-action-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const action = btn.getAttribute('data-action');
                this.handleQuickAction(action);
            });
        });

        // 响应式处理
        window.addEventListener('resize', () => this.handleResize());

        // 键盘快捷键
        document.addEventListener('keydown', (e) => this.handleKeyboardShortcuts(e));
    }

    // 页面导航
    navigateToPage(pageName) {
        // 隐藏当前页面
        document.querySelectorAll('.page').forEach(page => {
            page.classList.remove('active');
        });

        // 更新导航状态
        document.querySelectorAll('.nav-link').forEach(link => {
            link.classList.remove('active');
        });

        // 显示目标页面
        const targetPage = document.getElementById(`${pageName}-page`);
        const targetNav = document.querySelector(`[data-page="${pageName}"]`);

        if (targetPage) {
            targetPage.classList.add('active');
            this.currentPage = pageName;
        }

        if (targetNav) {
            targetNav.classList.add('active');
        }

        // 加载页面特定数据
        this.loadPageData(pageName);

        // 移动端关闭侧边栏
        if (window.innerWidth <= 768) {
            this.closeSidebar();
        }
    }

    // 侧边栏控制
    toggleSidebar() {
        const sidebar = document.getElementById('sidebar');
        const mainContent = document.getElementById('mainContent');

        if (this.sidebarCollapsed) {
            sidebar.style.transform = 'translateX(0)';
            this.sidebarCollapsed = false;
        } else {
            if (window.innerWidth <= 768) {
                sidebar.classList.toggle('open');
            } else {
                sidebar.style.width = this.sidebarCollapsed ? '280px' : '80px';
                this.sidebarCollapsed = !this.sidebarCollapsed;
            }
        }
    }

    closeSidebar() {
        const sidebar = document.getElementById('sidebar');
        sidebar.classList.remove('open');
    }

    // 通知面板控制
    toggleNotificationPanel() {
        const panel = document.getElementById('notificationPanel');
        panel.classList.toggle('open');
    }

    closeNotificationPanel() {
        const panel = document.getElementById('notificationPanel');
        panel.classList.remove('open');
    }

    // 加载初始数据
    async loadInitialData() {
        this.showLoading(true);

        try {
            await Promise.all([
                this.loadDashboardMetrics(),
                this.loadSystemStatus(),
                this.loadRecentTasks()
            ]);
        } catch (error) {
            console.error('加载初始数据失败:', error);
            this.showNotification('加载数据失败', 'error');
        } finally {
            this.showLoading(false);
        }
    }

    // 加载仪表盘指标
    async loadDashboardMetrics() {
        try {
            const response = await fetch('/api/data/summary');
            const data = await response.json();

            if (data.success) {
                const summary = data.data;
                this.updateMetrics(summary);
            }
        } catch (error) {
            console.error('加载仪表盘指标失败:', error);
        }
    }

    // 更新指标显示
    updateMetrics(summary) {
        const elements = {
            totalTrucks: document.getElementById('totalTrucks'),
            totalItems: document.getElementById('totalItems'),
            avgEfficiency: document.getElementById('avgEfficiency'),
            totalDistance: document.getElementById('totalDistance')
        };

        if (elements.totalTrucks) {
            elements.totalTrucks.textContent = summary.total_trucks || 0;
        }

        if (elements.totalItems) {
            elements.totalItems.textContent = this.formatNumber(summary.total_items || 0);
        }

        if (elements.avgEfficiency) {
            elements.avgEfficiency.textContent = `${summary.average_loading_efficiency || 0}%`;
        }

        if (elements.totalDistance) {
            elements.totalDistance.textContent = `${summary.total_distance_km || 0}km`;
        }
    }

    // 加载系统状态
    async loadSystemStatus() {
        try {
            const response = await fetch('/health');
            const data = await response.json();

            this.updateSystemStatus(data);
        } catch (error) {
            console.error('加载系统状态失败:', error);
            this.updateSystemStatus({ status: 'error' });
        }
    }

    // 更新系统状态显示
    updateSystemStatus(healthData) {
        // 这里可以根据健康检查的结果更新状态指示器
        const statusItems = document.querySelectorAll('.status-item');
        statusItems.forEach(item => {
            const indicator = item.querySelector('.status-indicator');
            if (healthData.status === 'healthy') {
                indicator.className = 'status-indicator online';
            } else {
                indicator.className = 'status-indicator warning';
            }
        });
    }

    // 加载最近任务
    async loadRecentTasks() {
        try {
            const response = await fetch('/api/optimization/history?limit=5');
            const data = await response.json();

            if (data.success) {
                this.updateRecentTasks(data.data);
            }
        } catch (error) {
            console.error('加载最近任务失败:', error);
        }
    }

    // 更新最近任务显示
    updateRecentTasks(tasks) {
        const tasksList = document.getElementById('recentTasks');
        if (!tasksList || !tasks.length) return;

        tasksList.innerHTML = tasks.map(task => `
            <div class="task-item">
                <div class="task-status ${this.getTaskStatusClass(task.status)}"></div>
                <div class="task-info">
                    <h4 class="task-title">${this.getTaskTypeDisplay(task.task_id)}</h4>
                    <p class="task-meta">${task.task_id} • ${this.formatTime(task.created_at)}</p>
                </div>
                <div class="task-actions">
                    <button class="btn-small" onclick="adminDashboard.viewTaskDetail('${task.task_id}')">
                        ${task.status === 'running' ? '监控' : '查看'}
                    </button>
                </div>
            </div>
        `).join('');
    }

    // 获取任务状态CSS类
    getTaskStatusClass(status) {
        const statusMap = {
            'completed': 'success',
            'running': 'running',
            'failed': 'error',
            'pending': 'pending'
        };
        return statusMap[status] || 'pending';
    }

    // 获取任务类型显示名称
    getTaskTypeDisplay(taskId) {
        if (taskId.includes('integrated')) return '集成优化任务';
        if (taskId.includes('3dpp')) return '3DPP装载优化';
        if (taskId.includes('route')) return '路径优化';
        return '优化任务';
    }

    // 初始化图表
    initCharts() {
        this.initPerformanceChart();
    }

    // 初始化性能趋势图表
    initPerformanceChart() {
        const ctx = document.getElementById('performanceChart');
        if (!ctx) return;

        this.charts.performance = new Chart(ctx, {
            type: 'line',
            data: {
                labels: ['1月', '2月', '3月', '4月', '5月', '6月'],
                datasets: [{
                    label: '装载效率',
                    data: [85, 87, 88, 90, 89, 91],
                    borderColor: '#3498db',
                    backgroundColor: 'rgba(52, 152, 219, 0.1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4
                }, {
                    label: '任务成功率',
                    data: [92, 94, 93, 95, 96, 95],
                    borderColor: '#27ae60',
                    backgroundColor: 'rgba(39, 174, 96, 0.1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                },
                scales: {
                    y: {
                        beginAtZero: false,
                        min: 80,
                        max: 100
                    }
                }
            }
        });
    }

    // 处理快速操作
    handleQuickAction(action) {
        switch (action) {
            case 'import-data':
                this.navigateToPage('data-import');
                break;
            case 'start-optimization':
                this.navigateToPage('optimization-start');
                break;
            case 'view-reports':
                this.navigateToPage('loading-results');
                break;
            case 'system-health':
                this.showSystemHealthModal();
                break;
            default:
                console.log('未知的快速操作:', action);
        }
    }

    // 系统健康检查
    async checkSystemHealth() {
        try {
            const checks = await Promise.allSettled([
                fetch('/health'),
                fetch('/api/data/summary'),
                fetch('/api/visualizations/stats')
            ]);

            let healthScore = 0;
            checks.forEach(result => {
                if (result.status === 'fulfilled' && result.value.ok) {
                    healthScore += 1;
                }
            });

            const healthPercentage = (healthScore / checks.length) * 100;
            this.updateHealthIndicator(healthPercentage);

        } catch (error) {
            console.error('系统健康检查失败:', error);
            this.updateHealthIndicator(0);
        }
    }

    // 更新健康指示器
    updateHealthIndicator(percentage) {
        // 可以在界面上显示系统健康状态
        console.log(`系统健康状态: ${percentage}%`);
    }

    // 全局搜索处理
    handleGlobalSearch(query) {
        if (!query.trim()) return;

        // 这里可以实现搜索逻辑
        console.log('搜索:', query);

        // 模拟搜索结果
        this.showSearchResults(query);
    }

    // 显示搜索结果
    showSearchResults(query) {
        // 实现搜索结果显示逻辑
        console.log('显示搜索结果:', query);
    }

    // 查看任务详情
    async viewTaskDetail(taskId) {
        try {
            const response = await fetch(`/api/optimization/status/${taskId}`);
            const data = await response.json();

            if (data.success) {
                this.showTaskDetailModal(data.data);
            }
        } catch (error) {
            console.error('获取任务详情失败:', error);
            this.showNotification('获取任务详情失败', 'error');
        }
    }

    // 显示任务详情模态框
    showTaskDetailModal(taskData) {
        // 实现任务详情模态框
        console.log('任务详情:', taskData);
    }

    // 系统健康模态框
    showSystemHealthModal() {
        // 实现系统健康检查模态框
        console.log('显示系统健康检查');
    }

    // 加载页面特定数据
    async loadPageData(pageName) {
        switch (pageName) {
            case 'data-import':
                await this.loadDataImportPage();
                break;
            case 'task-monitor':
                await this.loadTaskMonitorPage();
                break;
            case 'loading-results':
                await this.loadLoadingResultsPage();
                break;
            case 'route-results':
                await this.loadRouteResultsPage();
                break;
            case 'visualization-manager':
                await this.loadVisualizationManagerPage();
                break;
            case 'optimization-start':
                await this.loadOptimizationStartPage();
                break;
            case 'algorithm-config':
                await this.loadAlgorithmConfigPage();
                break;
            case 'user-management':
                await this.loadUserManagementPage();
                break;
            case 'system-settings':
                await this.loadSystemSettingsPage();
                break;
            case 'ai-assistant':
                await this.loadAIAssistantPage();
                break;
            default:
                break;
        }
    }

    // 加载数据导入页面
    async loadDataImportPage() {
        // 动态生成数据导入页面内容
        const page = document.getElementById('data-import-page');
        if (!page) return;

        page.innerHTML = `
            <div class="page-header">
                <h2 class="page-title">
                    <i class="fas fa-upload"></i>
                    数据导入
                </h2>
            </div>

            <div class="upload-area">
                <div class="upload-zone" id="uploadZone">
                    <div class="upload-icon">
                        <i class="fas fa-cloud-upload-alt"></i>
                    </div>
                    <h3>拖拽Excel文件到此处</h3>
                    <p>或者 <button class="upload-btn">选择文件</button></p>
                    <div class="upload-info">
                        <small>支持.xlsx, .xls格式，最大文件大小50MB</small>
                    </div>
                </div>

                <input type="file" id="fileInput" accept=".xlsx,.xls" style="display: none;">

                <div class="upload-progress" id="uploadProgress" style="display: none;">
                    <div class="progress-bar">
                        <div class="progress-fill" id="progressFill"></div>
                    </div>
                    <div class="progress-text" id="progressText">上传中... 0%</div>
                </div>
            </div>

            <div class="data-preview" id="dataPreview" style="display: none;">
                <h3>数据预览</h3>
                <div class="preview-table" id="previewTable"></div>
                <div class="preview-actions">
                    <button class="btn btn-primary" id="confirmImport">确认导入</button>
                    <button class="btn btn-secondary" id="cancelImport">取消</button>
                </div>
            </div>
        `;

        this.initDataImportHandlers();
    }

    // 初始化数据导入处理器
    initDataImportHandlers() {
        const uploadZone = document.getElementById('uploadZone');
        const fileInput = document.getElementById('fileInput');
        const uploadBtn = document.querySelector('.upload-btn');

        if (uploadBtn) {
            uploadBtn.addEventListener('click', () => fileInput.click());
        }

        if (fileInput) {
            fileInput.addEventListener('change', (e) => this.handleFileSelect(e.target.files[0]));
        }

        if (uploadZone) {
            // 拖拽处理
            uploadZone.addEventListener('dragover', (e) => {
                e.preventDefault();
                uploadZone.classList.add('drag-over');
            });

            uploadZone.addEventListener('dragleave', () => {
                uploadZone.classList.remove('drag-over');
            });

            uploadZone.addEventListener('drop', (e) => {
                e.preventDefault();
                uploadZone.classList.remove('drag-over');
                const file = e.dataTransfer.files[0];
                this.handleFileSelect(file);
            });
        }
    }

    // 处理文件选择
    handleFileSelect(file) {
        if (!file) return;

        // 验证文件类型
        const validTypes = ['application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                           'application/vnd.ms-excel'];

        if (!validTypes.includes(file.type)) {
            this.showNotification('请选择Excel文件（.xlsx或.xls）', 'error');
            return;
        }

        // 验证文件大小（50MB）
        if (file.size > 50 * 1024 * 1024) {
            this.showNotification('文件大小不能超过50MB', 'error');
            return;
        }

        this.uploadFile(file);
    }

    // 上传文件
    async uploadFile(file) {
        const formData = new FormData();
        formData.append('file', file);

        const progressElement = document.getElementById('uploadProgress');
        const progressFill = document.getElementById('progressFill');
        const progressText = document.getElementById('progressText');

        progressElement.style.display = 'block';

        try {
            // 模拟上传进度
            let progress = 0;
            const progressInterval = setInterval(() => {
                progress += Math.random() * 30;
                if (progress > 90) progress = 90;

                progressFill.style.width = `${progress}%`;
                progressText.textContent = `上传中... ${Math.round(progress)}%`;
            }, 200);

            // 实际上传逻辑（需要后端支持）
            const response = await fetch('/api/data/upload', {
                method: 'POST',
                body: formData
            });

            clearInterval(progressInterval);
            progressFill.style.width = '100%';
            progressText.textContent = '上传完成 100%';

            if (response.ok) {
                const result = await response.json();
                this.showDataPreview(result.data);
                this.showNotification('文件上传成功', 'success');
            } else {
                throw new Error('上传失败');
            }

        } catch (error) {
            console.error('上传失败:', error);
            this.showNotification('文件上传失败', 'error');
        } finally {
            setTimeout(() => {
                progressElement.style.display = 'none';
            }, 2000);
        }
    }

    // 显示数据预览
    showDataPreview(data) {
        const previewContainer = document.getElementById('dataPreview');
        const previewTable = document.getElementById('previewTable');

        if (!previewContainer || !previewTable) return;

        // 生成预览表格
        const tableHTML = `
            <table class="preview-table">
                <thead>
                    <tr>
                        ${data.headers.map(header => `<th>${header}</th>`).join('')}
                    </tr>
                </thead>
                <tbody>
                    ${data.preview.map(row => `
                        <tr>
                            ${row.map(cell => `<td>${cell}</td>`).join('')}
                        </tr>
                    `).join('')}
                </tbody>
            </table>
            <div class="preview-info">
                <p>显示前10行数据，共${data.totalRows}行</p>
            </div>
        `;

        previewTable.innerHTML = tableHTML;
        previewContainer.style.display = 'block';

        // 绑定确认导入事件
        const confirmBtn = document.getElementById('confirmImport');
        if (confirmBtn) {
            confirmBtn.addEventListener('click', () => this.confirmDataImport(data));
        }
    }

    // 确认数据导入
    async confirmDataImport(data) {
        try {
            this.showLoading(true);

            const response = await fetch('/api/data/import/confirm', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data)
            });

            if (response.ok) {
                this.showNotification('数据导入成功', 'success');
                this.navigateToPage('dashboard');
                this.refreshDashboardData();
            } else {
                throw new Error('导入确认失败');
            }

        } catch (error) {
            console.error('数据导入失败:', error);
            this.showNotification('数据导入失败', 'error');
        } finally {
            this.showLoading(false);
        }
    }

    // 加载任务监控页面
    async loadTaskMonitorPage() {
        const page = document.getElementById('task-monitor-page');
        if (!page) return;

        page.innerHTML = `
            <div class="page-header">
                <h2 class="page-title">
                    <i class="fas fa-tasks"></i>
                    任务监控中心
                </h2>
                <div class="page-actions">
                    <button class="btn btn-primary" onclick="adminDashboard.refreshTaskList()">
                        <i class="fas fa-sync-alt"></i> 刷新任务
                    </button>
                </div>
            </div>

            <!-- 任务概览统计 -->
            <div class="task-stats">
                <div class="stat-card">
                    <div class="stat-icon running">
                        <i class="fas fa-play-circle"></i>
                    </div>
                    <div class="stat-content">
                        <h3 id="runningTasks">0</h3>
                        <p>正在运行</p>
                    </div>
                </div>
                <div class="stat-card">
                    <div class="stat-icon pending">
                        <i class="fas fa-clock"></i>
                    </div>
                    <div class="stat-content">
                        <h3 id="pendingTasks">0</h3>
                        <p>等待中</p>
                    </div>
                </div>
                <div class="stat-card">
                    <div class="stat-icon completed">
                        <i class="fas fa-check-circle"></i>
                    </div>
                    <div class="stat-content">
                        <h3 id="completedTasks">0</h3>
                        <p>已完成</p>
                    </div>
                </div>
                <div class="stat-card">
                    <div class="stat-icon failed">
                        <i class="fas fa-exclamation-circle"></i>
                    </div>
                    <div class="stat-content">
                        <h3 id="failedTasks">0</h3>
                        <p>失败</p>
                    </div>
                </div>
            </div>

            <!-- 活跃任务监控 -->
            <div class="monitoring-section">
                <h3>实时任务监控</h3>
                <div class="active-tasks" id="activeTasks">
                    <!-- 动态生成活跃任务 -->
                </div>
            </div>

            <!-- 任务历史列表 -->
            <div class="task-history-section">
                <div class="section-header">
                    <h3>任务历史</h3>
                    <div class="filter-controls">
                        <select id="statusFilter">
                            <option value="">所有状态</option>
                            <option value="running">运行中</option>
                            <option value="completed">已完成</option>
                            <option value="failed">失败</option>
                        </select>
                        <select id="algorithmFilter">
                            <option value="">所有算法</option>
                            <option value="integrated">集成优化</option>
                            <option value="gurobi_3dpp">Gurobi 3DPP</option>
                            <option value="ltl_optimizer">LTL优化</option>
                            <option value="vrp_basic">路径优化</option>
                        </select>
                    </div>
                </div>
                <div class="task-table-container">
                    <table class="task-table" id="taskTable">
                        <thead>
                            <tr>
                                <th>任务ID</th>
                                <th>算法类型</th>
                                <th>状态</th>
                                <th>进度</th>
                                <th>开始时间</th>
                                <th>耗时</th>
                                <th>操作</th>
                            </tr>
                        </thead>
                        <tbody id="taskTableBody">
                            <!-- 动态生成任务列表 -->
                        </tbody>
                    </table>
                </div>
            </div>
        `;

        // 绑定过滤器事件
        document.getElementById('statusFilter')?.addEventListener('change', () => this.filterTasks());
        document.getElementById('algorithmFilter')?.addEventListener('change', () => this.filterTasks());

        // 加载任务数据
        await this.loadTaskData();

        // 开始实时监控
        this.startTaskMonitoring();
    }

    // 加载装载结果页面
    async loadLoadingResultsPage() {
        const page = document.getElementById('loading-results-page');
        if (!page) return;

        page.innerHTML = `
            <div class="page-header">
                <h2 class="page-title">
                    <i class="fas fa-boxes"></i>
                    装载方案查询
                </h2>
                <div class="page-actions">
                    <button class="btn btn-primary" onclick="adminDashboard.refreshLoadingResults()">
                        <i class="fas fa-sync-alt"></i> 刷新数据
                    </button>
                    <button class="btn btn-secondary" onclick="adminDashboard.exportLoadingResults()">
                        <i class="fas fa-download"></i> 导出数据
                    </button>
                </div>
            </div>

            <!-- 搜索和过滤 -->
            <div class="search-filter-section">
                <div class="search-box-container">
                    <input type="text" id="loadingSearch" placeholder="搜索车辆ID、货物类型..." class="search-input">
                    <i class="fas fa-search search-icon"></i>
                </div>
                <div class="filter-controls">
                    <select id="truckTypeFilter">
                        <option value="">所有车型</option>
                        <option value="LARGE_TRUCK">大型卡车</option>
                        <option value="LTL_TRUCK">LTL卡车</option>
                    </select>
                    <select id="efficiencyFilter">
                        <option value="">装载效率</option>
                        <option value="high">高效率(>90%)</option>
                        <option value="medium">中等效率(70%-90%)</option>
                        <option value="low">低效率(<70%)</option>
                    </select>
                </div>
            </div>

            <!-- 装载结果概览 -->
            <div class="loading-overview">
                <div class="overview-card">
                    <div class="overview-icon">
                        <i class="fas fa-truck"></i>
                    </div>
                    <div class="overview-content">
                        <h3 id="totalVehicles">0</h3>
                        <p>总车辆数</p>
                    </div>
                </div>
                <div class="overview-card">
                    <div class="overview-icon">
                        <i class="fas fa-cubes"></i>
                    </div>
                    <div class="overview-content">
                        <h3 id="totalCargo">0</h3>
                        <p>总货物数</p>
                    </div>
                </div>
                <div class="overview-card">
                    <div class="overview-icon">
                        <i class="fas fa-percentage"></i>
                    </div>
                    <div class="overview-content">
                        <h3 id="avgEfficiency">0%</h3>
                        <p>平均装载率</p>
                    </div>
                </div>
                <div class="overview-card">
                    <div class="overview-icon">
                        <i class="fas fa-weight"></i>
                    </div>
                    <div class="overview-content">
                        <h3 id="totalWeight">0kg</h3>
                        <p>总重量</p>
                    </div>
                </div>
            </div>

            <!-- 装载结果表格 -->
            <div class="results-table-section">
                <div class="table-container">
                    <table class="results-table" id="loadingResultsTable">
                        <thead>
                            <tr>
                                <th>车辆ID</th>
                                <th>车型</th>
                                <th>货物数量</th>
                                <th>总重量(kg)</th>
                                <th>总体积(m³)</th>
                                <th>装载效率</th>
                                <th>体积利用率</th>
                                <th>状态</th>
                                <th>操作</th>
                            </tr>
                        </thead>
                        <tbody id="loadingResultsTableBody">
                            <!-- 动态生成装载结果 -->
                        </tbody>
                    </table>
                </div>

                <!-- 分页控件 -->
                <div class="pagination-controls" id="loadingPagination">
                    <!-- 动态生成分页 -->
                </div>
            </div>

            <!-- 详情模态框 -->
            <div class="modal" id="loadingDetailModal">
                <div class="modal-content large">
                    <div class="modal-header">
                        <h3>装载详情</h3>
                        <button class="modal-close" onclick="adminDashboard.closeLoadingDetailModal()">
                            <i class="fas fa-times"></i>
                        </button>
                    </div>
                    <div class="modal-body" id="loadingDetailContent">
                        <!-- 动态生成详情内容 -->
                    </div>
                </div>
            </div>
        `;

        // 绑定搜索和过滤事件
        document.getElementById('loadingSearch')?.addEventListener('input', () => this.filterLoadingResults());
        document.getElementById('truckTypeFilter')?.addEventListener('change', () => this.filterLoadingResults());
        document.getElementById('efficiencyFilter')?.addEventListener('change', () => this.filterLoadingResults());

        // 加载装载结果数据
        await this.loadLoadingResultsData();
    }

    // 加载路径结果页面
    async loadRouteResultsPage() {
        const page = document.getElementById('route-results-page');
        if (!page) return;

        page.innerHTML = `
            <div class="page-header">
                <h2 class="page-title">
                    <i class="fas fa-route"></i>
                    路径优化查询
                </h2>
                <div class="page-actions">
                    <button class="btn btn-primary" onclick="adminDashboard.refreshRouteResults()">
                        <i class="fas fa-sync-alt"></i> 刷新数据
                    </button>
                    <button class="btn btn-secondary" onclick="adminDashboard.exportRouteResults()">
                        <i class="fas fa-download"></i> 导出路径
                    </button>
                </div>
            </div>

            <!-- 地图和筛选区域 -->
            <div class="route-main-section">
                <!-- 左侧地图区域 -->
                <div class="map-section">
                    <div class="map-controls">
                        <button class="map-btn active" data-view="all">全部路径</button>
                        <button class="map-btn" data-view="selected">选中路径</button>
                        <select id="vehicleMapFilter">
                            <option value="">选择车辆</option>
                        </select>
                    </div>
                    <div class="map-container" id="routeMap">
                        <!-- 地图将在这里加载 -->
                        <div class="map-placeholder">
                            <div class="placeholder-content">
                                <i class="fas fa-map-marked-alt"></i>
                                <p>地图加载中...</p>
                                <small>正在初始化路径显示</small>
                            </div>
                        </div>
                    </div>
                    <div class="map-legend">
                        <div class="legend-item">
                            <div class="legend-color" style="background: #3498db;"></div>
                            <span>LARGE_TRUCK路径</span>
                        </div>
                        <div class="legend-item">
                            <div class="legend-color" style="background: #e74c3c;"></div>
                            <span>LTL_TRUCK路径</span>
                        </div>
                        <div class="legend-item">
                            <div class="legend-color" style="background: #27ae60;"></div>
                            <span>配送中心</span>
                        </div>
                    </div>
                </div>

                <!-- 右侧数据区域 -->
                <div class="route-data-section">
                    <!-- 搜索过滤 -->
                    <div class="route-search-section">
                        <input type="text" id="routeSearch" placeholder="搜索车辆ID..." class="search-input">
                        <select id="routeTypeFilter">
                            <option value="">所有车型</option>
                            <option value="LARGE_TRUCK">大型卡车</option>
                            <option value="LTL_TRUCK">LTL卡车</option>
                        </select>
                    </div>

                    <!-- 路径统计 -->
                    <div class="route-stats">
                        <div class="stat-item">
                            <span class="stat-value" id="totalRoutes">0</span>
                            <span class="stat-label">总路径数</span>
                        </div>
                        <div class="stat-item">
                            <span class="stat-value" id="totalDistance">0km</span>
                            <span class="stat-label">总距离</span>
                        </div>
                        <div class="stat-item">
                            <span class="stat-value" id="totalStops">0</span>
                            <span class="stat-label">总停靠点</span>
                        </div>
                        <div class="stat-item">
                            <span class="stat-value" id="avgDuration">0h</span>
                            <span class="stat-label">平均时长</span>
                        </div>
                    </div>

                    <!-- 路径列表 -->
                    <div class="route-list-container">
                        <div class="route-list" id="routeList">
                            <!-- 动态生成路径卡片 -->
                        </div>
                    </div>
                </div>
            </div>

            <!-- 路径详情模态框 -->
            <div class="modal" id="routeDetailModal">
                <div class="modal-content extra-large">
                    <div class="modal-header">
                        <h3>路径详情</h3>
                        <button class="modal-close" onclick="adminDashboard.closeRouteDetailModal()">
                            <i class="fas fa-times"></i>
                        </button>
                    </div>
                    <div class="modal-body" id="routeDetailContent">
                        <!-- 动态生成路径详情 -->
                    </div>
                </div>
            </div>
        `;

        // 绑定地图控制事件
        document.querySelectorAll('.map-btn').forEach(btn => {
            btn.addEventListener('click', (e) => this.switchMapView(e.target.dataset.view));
        });

        // 绑定搜索和过滤事件
        document.getElementById('routeSearch')?.addEventListener('input', () => this.filterRouteResults());
        document.getElementById('routeTypeFilter')?.addEventListener('change', () => this.filterRouteResults());
        document.getElementById('vehicleMapFilter')?.addEventListener('change', () => this.updateMapDisplay());

        // 加载路径结果数据
        await this.loadRouteResultsData();

        // 初始化地图
        this.initializeRouteMap();
    }

    // 加载可视化管理页面
    async loadVisualizationManagerPage() {
        const page = document.getElementById('visualization-manager-page');
        if (!page) return;

        page.innerHTML = `
            <div class="page-header">
                <h2 class="page-title">
                    <i class="fas fa-chart-pie"></i>
                    可视化管理
                </h2>
                <div class="page-actions">
                    <button class="btn btn-primary" onclick="adminDashboard.refreshVisualizations()">
                        <i class="fas fa-sync-alt"></i> 刷新列表
                    </button>
                    <button class="btn btn-success" onclick="adminDashboard.generateNewVisualization()">
                        <i class="fas fa-plus"></i> 生成新可视化
                    </button>
                </div>
            </div>

            <!-- 可视化统计概览 -->
            <div class="viz-stats-section">
                <div class="viz-stat-card">
                    <div class="stat-icon">
                        <i class="fas fa-file-image"></i>
                    </div>
                    <div class="stat-content">
                        <h3 id="totalVizFiles">0</h3>
                        <p>可视化文件</p>
                    </div>
                </div>
                <div class="viz-stat-card">
                    <div class="stat-icon">
                        <i class="fas fa-cube"></i>
                    </div>
                    <div class="stat-content">
                        <h3 id="total3DFiles">0</h3>
                        <p>3D装载图</p>
                    </div>
                </div>
                <div class="viz-stat-card">
                    <div class="stat-icon">
                        <i class="fas fa-map"></i>
                    </div>
                    <div class="stat-content">
                        <h3 id="totalRouteFiles">0</h3>
                        <p>路径地图</p>
                    </div>
                </div>
                <div class="viz-stat-card">
                    <div class="stat-icon">
                        <i class="fas fa-hdd"></i>
                    </div>
                    <div class="stat-content">
                        <h3 id="totalVizSize">0MB</h3>
                        <p>占用空间</p>
                    </div>
                </div>
            </div>

            <!-- 可视化类型筛选 -->
            <div class="viz-filter-section">
                <div class="filter-tabs">
                    <button class="filter-tab active" data-type="all">全部 (<span id="allCount">0</span>)</button>
                    <button class="filter-tab" data-type="3dpp">3D装载 (<span id="3dppCount">0</span>)</button>
                    <button class="filter-tab" data-type="route">路径地图 (<span id="routeCount">0</span>)</button>
                    <button class="filter-tab" data-type="heatmap">热力图 (<span id="heatmapCount">0</span>)</button>
                    <button class="filter-tab" data-type="efficiency">效率分析 (<span id="efficiencyCount">0</span>)</button>
                    <button class="filter-tab" data-type="3d_analysis">3D分析 (<span id="analysisCount">0</span>)</button>
                </div>
                <div class="view-controls">
                    <button class="view-btn active" data-view="grid">
                        <i class="fas fa-th"></i>
                    </button>
                    <button class="view-btn" data-view="list">
                        <i class="fas fa-list"></i>
                    </button>
                </div>
            </div>

            <!-- 可视化文件网格 -->
            <div class="viz-grid-container">
                <div class="viz-grid" id="visualizationGrid">
                    <!-- 动态生成可视化文件卡片 -->
                </div>
            </div>

            <!-- 批量操作栏 -->
            <div class="batch-actions" id="batchActions" style="display: none;">
                <div class="batch-info">
                    已选择 <span id="selectedCount">0</span> 项
                </div>
                <div class="batch-buttons">
                    <button class="btn btn-warning" onclick="adminDashboard.downloadSelectedFiles()">
                        <i class="fas fa-download"></i> 批量下载
                    </button>
                    <button class="btn btn-danger" onclick="adminDashboard.deleteSelectedFiles()">
                        <i class="fas fa-trash"></i> 批量删除
                    </button>
                    <button class="btn btn-secondary" onclick="adminDashboard.clearSelection()">
                        <i class="fas fa-times"></i> 取消选择
                    </button>
                </div>
            </div>

            <!-- 可视化预览模态框 -->
            <div class="modal" id="vizPreviewModal">
                <div class="modal-content fullscreen">
                    <div class="modal-header">
                        <h3 id="vizPreviewTitle">可视化预览</h3>
                        <div class="modal-actions">
                            <button class="btn btn-sm btn-primary" onclick="adminDashboard.openVizInNewTab()">
                                <i class="fas fa-external-link-alt"></i> 新窗口打开
                            </button>
                            <button class="btn btn-sm btn-secondary" onclick="adminDashboard.downloadCurrentViz()">
                                <i class="fas fa-download"></i> 下载
                            </button>
                            <button class="modal-close" onclick="adminDashboard.closeVizPreview()">
                                <i class="fas fa-times"></i>
                            </button>
                        </div>
                    </div>
                    <div class="modal-body">
                        <iframe id="vizPreviewFrame" src="" style="width: 100%; height: 80vh; border: none;"></iframe>
                    </div>
                </div>
            </div>

            <!-- 生成新可视化模态框 -->
            <div class="modal" id="generateVizModal">
                <div class="modal-content">
                    <div class="modal-header">
                        <h3>生成新可视化</h3>
                        <button class="modal-close" onclick="adminDashboard.closeGenerateVizModal()">
                            <i class="fas fa-times"></i>
                        </button>
                    </div>
                    <div class="modal-body">
                        <form id="generateVizForm">
                            <div class="form-group">
                                <label>可视化类型</label>
                                <select id="vizType" required>
                                    <option value="">请选择类型</option>
                                    <option value="3dpp">3D装载可视化</option>
                                    <option value="route">路径地图</option>
                                    <option value="heatmap">装载密度热力图</option>
                                    <option value="efficiency">装载效率分析</option>
                                    <option value="3d_analysis">3D效率分析</option>
                                </select>
                            </div>
                            <div class="form-group">
                                <label>选择车辆</label>
                                <select id="vizVehicleSelect" multiple>
                                    <!-- 动态填充车辆选项 -->
                                </select>
                                <small class="form-hint">可多选，留空则生成所有车辆</small>
                            </div>
                            <div class="form-group">
                                <label>
                                    <input type="checkbox" id="vizAutoOpen" checked>
                                    生成后自动打开预览
                                </label>
                            </div>
                            <div class="form-actions">
                                <button type="submit" class="btn btn-primary">
                                    <i class="fas fa-magic"></i> 开始生成
                                </button>
                                <button type="button" class="btn btn-secondary" onclick="adminDashboard.closeGenerateVizModal()">
                                    取消
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            </div>
        `;

        // 绑定筛选标签事件
        document.querySelectorAll('.filter-tab').forEach(tab => {
            tab.addEventListener('click', (e) => this.switchVizFilter(e.target.dataset.type));
        });

        // 绑定视图切换事件
        document.querySelectorAll('.view-btn').forEach(btn => {
            btn.addEventListener('click', (e) => this.switchVizView(e.target.dataset.view));
        });

        // 绑定生成表单事件
        document.getElementById('generateVizForm')?.addEventListener('submit', (e) => this.handleGenerateViz(e));

        // 加载可视化数据
        await this.loadVisualizationData();
    }

    // 刷新仪表盘数据
    async refreshDashboardData() {
        await this.loadDashboardMetrics();
        await this.loadSystemStatus();
        await this.loadRecentTasks();
        this.showNotification('数据已刷新', 'success');
    }

    // 开始定期刷新
    startPeriodicRefresh() {
        // 每30秒刷新一次数据
        this.refreshInterval = setInterval(() => {
            if (this.currentPage === 'dashboard') {
                this.loadDashboardMetrics();
                this.loadRecentTasks();
            }
        }, 30000);
    }

    // 停止定期刷新
    stopPeriodicRefresh() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
            this.refreshInterval = null;
        }
    }

    // 显示通知
    showNotification(message, type = 'info', duration = 3000) {
        // 创建通知元素
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <div class="notification-content">
                <i class="fas fa-${this.getNotificationIcon(type)}"></i>
                <span>${message}</span>
            </div>
            <button class="notification-close">
                <i class="fas fa-times"></i>
            </button>
        `;

        // 添加到页面
        const container = document.querySelector('.notifications-container') || this.createNotificationsContainer();
        container.appendChild(notification);

        // 关闭按钮事件
        notification.querySelector('.notification-close').addEventListener('click', () => {
            this.removeNotification(notification);
        });

        // 自动移除
        setTimeout(() => {
            this.removeNotification(notification);
        }, duration);
    }

    // 创建通知容器
    createNotificationsContainer() {
        const container = document.createElement('div');
        container.className = 'notifications-container';
        container.style.cssText = `
            position: fixed;
            top: 80px;
            right: 20px;
            z-index: 10000;
            display: flex;
            flex-direction: column;
            gap: 10px;
            pointer-events: none;
        `;
        document.body.appendChild(container);
        return container;
    }

    // 移除通知
    removeNotification(notification) {
        notification.style.animation = 'slideOutRight 0.3s ease';
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 300);
    }

    // 获取通知图标
    getNotificationIcon(type) {
        const icons = {
            success: 'check-circle',
            error: 'exclamation-circle',
            warning: 'exclamation-triangle',
            info: 'info-circle'
        };
        return icons[type] || 'info-circle';
    }

    // 显示/隐藏加载遮罩
    showLoading(show) {
        const overlay = document.getElementById('loadingOverlay');
        if (overlay) {
            overlay.classList.toggle('show', show);
        }
    }

    // 响应式处理
    handleResize() {
        if (window.innerWidth <= 768) {
            this.closeSidebar();
        }
    }

    // 键盘快捷键
    handleKeyboardShortcuts(e) {
        // Ctrl+/ 或 Cmd+/ 打开搜索
        if ((e.ctrlKey || e.metaKey) && e.key === '/') {
            e.preventDefault();
            document.getElementById('globalSearch').focus();
        }

        // ESC 关闭面板
        if (e.key === 'Escape') {
            this.closeNotificationPanel();
        }
    }

    // 工具方法：格式化数字
    formatNumber(num) {
        return new Intl.NumberFormat('zh-CN').format(num);
    }

    // 工具方法：格式化时间
    formatTime(dateString) {
        const date = new Date(dateString);
        const now = new Date();
        const diffMs = now - date;
        const diffMins = Math.floor(diffMs / 60000);

        if (diffMins < 1) return '刚刚';
        if (diffMins < 60) return `${diffMins}分钟前`;
        if (diffMins < 1440) return `${Math.floor(diffMins / 60)}小时前`;
        return `${Math.floor(diffMins / 1440)}天前`;
    }

    // ===== 新增页面函数 =====

    // 启动优化页面
    async loadOptimizationStartPage() {
        const page = document.getElementById('optimization-start-page');
        if (!page) return;

        page.innerHTML = `
            <div class="page-header">
                <h2 class="page-title">
                    <i class="fas fa-play-circle"></i>
                    启动优化任务
                </h2>
                <div class="page-actions">
                    <button class="btn btn-secondary" onclick="adminDashboard.loadOptimizationHistory()">
                        <i class="fas fa-history"></i> 查看历史
                    </button>
                </div>
            </div>

            <div class="optimization-wizard">
                <div class="wizard-steps">
                    <div class="step active" data-step="1">
                        <div class="step-number">1</div>
                        <div class="step-title">选择数据源</div>
                    </div>
                    <div class="step" data-step="2">
                        <div class="step-number">2</div>
                        <div class="step-title">配置算法</div>
                    </div>
                    <div class="step" data-step="3">
                        <div class="step-number">3</div>
                        <div class="step-title">启动优化</div>
                    </div>
                </div>

                <form class="optimization-form" id="optimizationForm">
                    <!-- 第一步：选择数据源 -->
                    <div class="wizard-content active" data-content="1">
                        <h3>选择数据源</h3>
                        <div class="data-source-options">
                            <div class="data-option">
                                <input type="radio" id="useExistingData" name="dataSource" value="existing" checked>
                                <label for="useExistingData">
                                    <div class="option-icon">
                                        <i class="fas fa-database"></i>
                                    </div>
                                    <div class="option-content">
                                        <h4>使用现有数据</h4>
                                        <p>使用最近导入的Excel数据</p>
                                    </div>
                                </label>
                            </div>
                            <div class="data-option">
                                <input type="radio" id="uploadNewData" name="dataSource" value="new">
                                <label for="uploadNewData">
                                    <div class="option-icon">
                                        <i class="fas fa-upload"></i>
                                    </div>
                                    <div class="option-content">
                                        <h4>上传新数据</h4>
                                        <p>上传新的Excel文件</p>
                                    </div>
                                </label>
                            </div>
                        </div>
                        <div class="upload-section" id="uploadSection" style="display: none;">
                            <div class="upload-zone">
                                <i class="fas fa-cloud-upload-alt"></i>
                                <p>拖拽Excel文件到此处或<button type="button" class="upload-btn">选择文件</button></p>
                            </div>
                        </div>
                    </div>

                    <!-- 第二步：配置算法 -->
                    <div class="wizard-content" data-content="2">
                        <h3>选择优化算法</h3>
                        <div class="algorithm-grid">
                            <div class="algorithm-card">
                                <input type="radio" id="integrated" name="algorithm" value="integrated" checked>
                                <label for="integrated">
                                    <div class="card-header">
                                        <i class="fas fa-magic"></i>
                                        <h4>集成优化</h4>
                                    </div>
                                    <div class="card-content">
                                        <p>同时进行装载和路径优化，获得最佳整体方案</p>
                                        <div class="features">
                                            <span>• 3DPP装载优化</span>
                                            <span>• 车辆路径规划</span>
                                            <span>• 全局最优解</span>
                                        </div>
                                    </div>
                                </label>
                            </div>
                            <div class="algorithm-card">
                                <input type="radio" id="gurobi3dpp" name="algorithm" value="gurobi_3dpp">
                                <label for="gurobi3dpp">
                                    <div class="card-header">
                                        <i class="fas fa-cube"></i>
                                        <h4>Gurobi 3DPP</h4>
                                    </div>
                                    <div class="card-content">
                                        <p>专注于3D装载优化，使用Gurobi求解器</p>
                                        <div class="features">
                                            <span>• 精确装载计算</span>
                                            <span>• 高装载效率</span>
                                            <span>• 支持复杂约束</span>
                                        </div>
                                    </div>
                                </label>
                            </div>
                            <div class="algorithm-card">
                                <input type="radio" id="ltlOptimizer" name="algorithm" value="ltl_optimizer">
                                <label for="ltlOptimizer">
                                    <div class="card-header">
                                        <i class="fas fa-truck"></i>
                                        <h4>LTL拼装优化</h4>
                                    </div>
                                    <div class="card-content">
                                        <p>零担货物拼装专用优化算法</p>
                                        <div class="features">
                                            <span>• LTL货物处理</span>
                                            <span>• 智能拼装</span>
                                            <span>• 成本最优</span>
                                        </div>
                                    </div>
                                </label>
                            </div>
                            <div class="algorithm-card">
                                <input type="radio" id="vrpBasic" name="algorithm" value="vrp_basic">
                                <label for="vrpBasic">
                                    <div class="card-header">
                                        <i class="fas fa-route"></i>
                                        <h4>路径优化</h4>
                                    </div>
                                    <div class="card-content">
                                        <p>专注于车辆路径规划优化</p>
                                        <div class="features">
                                            <span>• 最短路径计算</span>
                                            <span>• 时间窗口约束</span>
                                            <span>• 成本控制</span>
                                        </div>
                                    </div>
                                </label>
                            </div>
                        </div>
                    </div>

                    <!-- 第三步：启动优化 -->
                    <div class="wizard-content" data-content="3">
                        <h3>确认并启动优化</h3>
                        <div class="confirmation-section">
                            <div class="config-summary">
                                <h4>配置摘要</h4>
                                <div class="summary-item">
                                    <span class="label">数据源：</span>
                                    <span class="value" id="summaryDataSource">现有数据</span>
                                </div>
                                <div class="summary-item">
                                    <span class="label">优化算法：</span>
                                    <span class="value" id="summaryAlgorithm">集成优化</span>
                                </div>
                                <div class="summary-item">
                                    <span class="label">预计耗时：</span>
                                    <span class="value" id="summaryDuration">5-15分钟</span>
                                </div>
                            </div>
                            <div class="optimization-options">
                                <h4>附加选项</h4>
                                <label class="checkbox-option">
                                    <input type="checkbox" id="generateViz" checked>
                                    <span class="checkmark"></span>
                                    生成可视化图表
                                </label>
                                <label class="checkbox-option">
                                    <input type="checkbox" id="emailNotify">
                                    <span class="checkmark"></span>
                                    完成后发送邮件通知
                                </label>
                                <label class="checkbox-option">
                                    <input type="checkbox" id="autoArchive">
                                    <span class="checkmark"></span>
                                    自动归档结果文件
                                </label>
                            </div>
                        </div>
                    </div>

                    <!-- 导航按钮 -->
                    <div class="wizard-navigation">
                        <button type="button" class="btn btn-secondary" id="prevStep" style="display: none;">
                            <i class="fas fa-arrow-left"></i> 上一步
                        </button>
                        <div class="nav-spacer"></div>
                        <button type="button" class="btn btn-primary" id="nextStep">
                            下一步 <i class="fas fa-arrow-right"></i>
                        </button>
                        <button type="submit" class="btn btn-success" id="startOptimization" style="display: none;">
                            <i class="fas fa-rocket"></i> 启动优化
                        </button>
                    </div>
                </form>
            </div>
        `;

        // 绑定向导步骤事件
        this.initOptimizationWizard();
    }

    // 算法配置页面
    async loadAlgorithmConfigPage() {
        const page = document.getElementById('algorithm-config-page');
        if (!page) return;

        page.innerHTML = `
            <div class="page-header">
                <h2 class="page-title">
                    <i class="fas fa-cogs"></i>
                    算法配置
                </h2>
                <div class="page-actions">
                    <button class="btn btn-success" onclick="adminDashboard.saveAlgorithmConfig()">
                        <i class="fas fa-save"></i> 保存配置
                    </button>
                    <button class="btn btn-secondary" onclick="adminDashboard.resetToDefault()">
                        <i class="fas fa-undo"></i> 恢复默认
                    </button>
                </div>
            </div>

            <div class="config-sections">
                <!-- Gurobi配置 -->
                <div class="config-section">
                    <div class="section-header">
                        <h3><i class="fas fa-cube"></i> Gurobi 求解器配置</h3>
                        <p>配置Gurobi优化求解器的参数</p>
                    </div>
                    <div class="config-grid">
                        <div class="config-item">
                            <label>求解时间限制（秒）</label>
                            <input type="number" id="gurobiTimeLimit" value="3600" min="60" max="18000">
                            <small>设置单个优化任务的最大求解时间</small>
                        </div>
                        <div class="config-item">
                            <label>MIP间隙</label>
                            <input type="number" id="gurobiMipGap" value="0.01" step="0.001" min="0.001" max="0.1">
                            <small>设置整数规划的相对间隙容忍度</small>
                        </div>
                        <div class="config-item">
                            <label>线程数</label>
                            <input type="number" id="gurobiThreads" value="0" min="0" max="32">
                            <small>0表示自动使用所有可用线程</small>
                        </div>
                    </div>
                </div>

                <!-- LTL优化配置 -->
                <div class="config-section">
                    <div class="section-header">
                        <h3><i class="fas fa-truck"></i> LTL优化配置</h3>
                        <p>零担货物拼装优化参数</p>
                    </div>
                    <div class="config-grid">
                        <div class="config-item">
                            <label>最大装载率（%）</label>
                            <input type="number" id="ltlMaxLoadRate" value="95" min="70" max="100">
                            <small>LTL卡车的最大装载率限制</small>
                        </div>
                        <div class="config-item">
                            <label>最小装载率（%）</label>
                            <input type="number" id="ltlMinLoadRate" value="60" min="30" max="80">
                            <small>LTL卡车的最小装载率要求</small>
                        </div>
                        <div class="config-item">
                            <label>兼容性系数</label>
                            <input type="number" id="ltlCompatibility" value="0.8" step="0.1" min="0.1" max="1.0">
                            <small>不同货物类型的兼容性权重</small>
                        </div>
                    </div>
                </div>

                <!-- 路径优化配置 -->
                <div class="config-section">
                    <div class="section-header">
                        <h3><i class="fas fa-route"></i> 路径优化配置</h3>
                        <p>车辆路径规划算法参数</p>
                    </div>
                    <div class="config-grid">
                        <div class="config-item">
                            <label>最大路径长度（公里）</label>
                            <input type="number" id="maxRouteDistance" value="500" min="100" max="2000">
                            <small>单车最大行驶距离限制</small>
                        </div>
                        <div class="config-item">
                            <label>最大停靠点数</label>
                            <input type="number" id="maxStops" value="20" min="5" max="50">
                            <small>单车最大停靠点数量</small>
                        </div>
                        <div class="config-item">
                            <label>速度系数（km/h）</label>
                            <input type="number" id="avgSpeed" value="60" min="30" max="120">
                            <small>平均行驶速度，用于时间计算</small>
                        </div>
                    </div>
                </div>

                <!-- 可视化配置 -->
                <div class="config-section">
                    <div class="section-header">
                        <h3><i class="fas fa-chart-pie"></i> 可视化配置</h3>
                        <p>可视化生成和显示参数</p>
                    </div>
                    <div class="config-grid">
                        <div class="config-item">
                            <label>
                                <input type="checkbox" id="enableHeavyViz">
                                启用重型可视化
                            </label>
                            <small>启用后将生成更详细但更耗时的可视化</small>
                        </div>
                        <div class="config-item">
                            <label>采样比例</label>
                            <input type="number" id="samplingRatio" value="0.3" step="0.1" min="0.1" max="1.0">
                            <small>大数据集的可视化采样比例</small>
                        </div>
                        <div class="config-item">
                            <label>最大显示项目数</label>
                            <input type="number" id="maxVizItems" value="500" min="100" max="2000">
                            <small>单个可视化图表的最大显示项目数</small>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    // 用户管理页面
    async loadUserManagementPage() {
        const page = document.getElementById('user-management-page');
        if (!page) return;

        page.innerHTML = `
            <div class="page-header">
                <h2 class="page-title">
                    <i class="fas fa-users"></i>
                    用户管理
                </h2>
                <div class="page-actions">
                    <button class="btn btn-success" onclick="adminDashboard.showAddUserModal()">
                        <i class="fas fa-user-plus"></i> 添加用户
                    </button>
                    <button class="btn btn-primary" onclick="adminDashboard.refreshUserList()">
                        <i class="fas fa-sync-alt"></i> 刷新列表
                    </button>
                </div>
            </div>

            <!-- 用户统计 -->
            <div class="user-stats">
                <div class="stat-card">
                    <div class="stat-icon">
                        <i class="fas fa-users"></i>
                    </div>
                    <div class="stat-content">
                        <h3 id="totalUsers">0</h3>
                        <p>总用户数</p>
                    </div>
                </div>
                <div class="stat-card">
                    <div class="stat-icon">
                        <i class="fas fa-user-shield"></i>
                    </div>
                    <div class="stat-content">
                        <h3 id="adminUsers">0</h3>
                        <p>管理员</p>
                    </div>
                </div>
                <div class="stat-card">
                    <div class="stat-icon">
                        <i class="fas fa-user-check"></i>
                    </div>
                    <div class="stat-content">
                        <h3 id="activeUsers">0</h3>
                        <p>活跃用户</p>
                    </div>
                </div>
                <div class="stat-card">
                    <div class="stat-icon">
                        <i class="fas fa-user-clock"></i>
                    </div>
                    <div class="stat-content">
                        <h3 id="recentLogins">0</h3>
                        <p>最近登录</p>
                    </div>
                </div>
            </div>

            <!-- 搜索和过滤 -->
            <div class="user-filters">
                <input type="text" id="userSearch" placeholder="搜索用户名、邮箱..." class="search-input">
                <select id="roleFilter">
                    <option value="">所有角色</option>
                    <option value="admin">管理员</option>
                    <option value="operator">操作员</option>
                    <option value="viewer">查看者</option>
                </select>
                <select id="statusFilter">
                    <option value="">所有状态</option>
                    <option value="active">活跃</option>
                    <option value="inactive">非活跃</option>
                </select>
            </div>

            <!-- 用户表格 -->
            <div class="user-table-container">
                <table class="user-table">
                    <thead>
                        <tr>
                            <th>用户名</th>
                            <th>邮箱</th>
                            <th>角色</th>
                            <th>状态</th>
                            <th>创建时间</th>
                            <th>最后登录</th>
                            <th>操作</th>
                        </tr>
                    </thead>
                    <tbody id="userTableBody">
                        <!-- 动态生成用户列表 -->
                    </tbody>
                </table>
            </div>

            <!-- 添加/编辑用户模态框 -->
            <div class="modal" id="userModal">
                <div class="modal-content">
                    <div class="modal-header">
                        <h3 id="userModalTitle">添加用户</h3>
                        <button class="modal-close" onclick="adminDashboard.closeUserModal()">
                            <i class="fas fa-times"></i>
                        </button>
                    </div>
                    <div class="modal-body">
                        <form id="userForm">
                            <div class="form-group">
                                <label>用户名*</label>
                                <input type="text" id="userName" required>
                            </div>
                            <div class="form-group">
                                <label>邮箱*</label>
                                <input type="email" id="userEmail" required>
                            </div>
                            <div class="form-group">
                                <label>角色*</label>
                                <select id="userRole" required>
                                    <option value="">选择角色</option>
                                    <option value="admin">管理员</option>
                                    <option value="operator">操作员</option>
                                    <option value="viewer">查看者</option>
                                </select>
                            </div>
                            <div class="form-group" id="passwordGroup">
                                <label>密码*</label>
                                <input type="password" id="userPassword" required>
                            </div>
                            <div class="form-group">
                                <label>
                                    <input type="checkbox" id="userActive" checked>
                                    激活用户
                                </label>
                            </div>
                            <div class="form-actions">
                                <button type="submit" class="btn btn-primary">
                                    <i class="fas fa-save"></i> 保存
                                </button>
                                <button type="button" class="btn btn-secondary" onclick="adminDashboard.closeUserModal()">
                                    取消
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            </div>
        `;

        // 绑定搜索和过滤事件
        document.getElementById('userSearch')?.addEventListener('input', () => this.filterUsers());
        document.getElementById('roleFilter')?.addEventListener('change', () => this.filterUsers());
        document.getElementById('statusFilter')?.addEventListener('change', () => this.filterUsers());

        // 绑定表单事件
        document.getElementById('userForm')?.addEventListener('submit', (e) => this.handleUserForm(e));

        // 加载用户数据
        await this.loadUserData();
    }

    // 系统设置页面
    async loadSystemSettingsPage() {
        const page = document.getElementById('system-settings-page');
        if (!page) return;

        page.innerHTML = `
            <div class="page-header">
                <h2 class="page-title">
                    <i class="fas fa-sliders-h"></i>
                    系统设置
                </h2>
                <div class="page-actions">
                    <button class="btn btn-success" onclick="adminDashboard.saveSystemSettings()">
                        <i class="fas fa-save"></i> 保存设置
                    </button>
                    <button class="btn btn-danger" onclick="adminDashboard.resetSystemSettings()">
                        <i class="fas fa-undo"></i> 重置设置
                    </button>
                </div>
            </div>

            <div class="settings-container">
                <!-- 系统信息 -->
                <div class="settings-section">
                    <h3><i class="fas fa-info-circle"></i> 系统信息</h3>
                    <div class="system-info-grid">
                        <div class="info-item">
                            <span class="label">系统版本</span>
                            <span class="value">4.0.0</span>
                        </div>
                        <div class="info-item">
                            <span class="label">运行时间</span>
                            <span class="value" id="systemUptime">计算中...</span>
                        </div>
                        <div class="info-item">
                            <span class="label">内存使用</span>
                            <span class="value" id="memoryUsage">计算中...</span>
                        </div>
                        <div class="info-item">
                            <span class="label">磁盘使用</span>
                            <span class="value" id="diskUsage">计算中...</span>
                        </div>
                    </div>
                </div>

                <!-- 性能配置 -->
                <div class="settings-section">
                    <h3><i class="fas fa-tachometer-alt"></i> 性能配置</h3>
                    <div class="setting-item">
                        <label>最大并发任务数</label>
                        <input type="number" id="maxConcurrentTasks" value="3" min="1" max="10">
                        <small>同时运行的优化任务最大数量</small>
                    </div>
                    <div class="setting-item">
                        <label>任务超时时间（分钟）</label>
                        <input type="number" id="taskTimeout" value="60" min="5" max="300">
                        <small>单个优化任务的超时时间</small>
                    </div>
                    <div class="setting-item">
                        <label>
                            <input type="checkbox" id="enableCaching" checked>
                            启用结果缓存
                        </label>
                        <small>缓存优化结果以提高重复查询性能</small>
                    </div>
                </div>

                <!-- 数据配置 -->
                <div class="settings-section">
                    <h3><i class="fas fa-database"></i> 数据配置</h3>
                    <div class="setting-item">
                        <label>数据保留天数</label>
                        <input type="number" id="dataRetentionDays" value="90" min="7" max="365">
                        <small>自动清理超过指定天数的历史数据</small>
                    </div>
                    <div class="setting-item">
                        <label>最大上传文件大小（MB）</label>
                        <input type="number" id="maxUploadSize" value="100" min="10" max="1000">
                        <small>Excel文件上传的大小限制</small>
                    </div>
                    <div class="setting-item">
                        <label>
                            <input type="checkbox" id="autoBackup" checked>
                            启用自动备份
                        </label>
                        <small>定期自动备份用户数据和配置</small>
                    </div>
                </div>

                <!-- 通知配置 -->
                <div class="settings-section">
                    <h3><i class="fas fa-bell"></i> 通知配置</h3>
                    <div class="setting-item">
                        <label>SMTP服务器</label>
                        <input type="text" id="smtpServer" placeholder="smtp.example.com">
                        <small>用于发送邮件通知的SMTP服务器</small>
                    </div>
                    <div class="setting-item">
                        <label>发件人邮箱</label>
                        <input type="email" id="senderEmail" placeholder="noreply@example.com">
                        <small>系统发送通知邮件的邮箱地址</small>
                    </div>
                    <div class="setting-item">
                        <label>
                            <input type="checkbox" id="enableEmailNotify">
                            启用邮件通知
                        </label>
                        <small>任务完成后发送邮件通知</small>
                    </div>
                </div>

                <!-- 安全配置 -->
                <div class="settings-section">
                    <h3><i class="fas fa-shield-alt"></i> 安全配置</h3>
                    <div class="setting-item">
                        <label>会话过期时间（小时）</label>
                        <input type="number" id="sessionTimeout" value="8" min="1" max="24">
                        <small>用户会话的有效期限制</small>
                    </div>
                    <div class="setting-item">
                        <label>密码最小长度</label>
                        <input type="number" id="minPasswordLength" value="8" min="6" max="20">
                        <small>用户密码的最小长度要求</small>
                    </div>
                    <div class="setting-item">
                        <label>
                            <input type="checkbox" id="requireStrongPassword" checked>
                            要求强密码
                        </label>
                        <small>密码必须包含字母、数字和特殊字符</small>
                    </div>
                </div>

                <!-- 系统维护 -->
                <div class="settings-section">
                    <h3><i class="fas fa-tools"></i> 系统维护</h3>
                    <div class="maintenance-buttons">
                        <button class="btn btn-warning" onclick="adminDashboard.clearCache()">
                            <i class="fas fa-broom"></i> 清理缓存
                        </button>
                        <button class="btn btn-info" onclick="adminDashboard.runSystemCheck()">
                            <i class="fas fa-stethoscope"></i> 系统检查
                        </button>
                        <button class="btn btn-secondary" onclick="adminDashboard.exportLogs()">
                            <i class="fas fa-download"></i> 导出日志
                        </button>
                        <button class="btn btn-danger" onclick="adminDashboard.restartSystem()">
                            <i class="fas fa-restart"></i> 重启系统
                        </button>
                    </div>
                </div>
            </div>
        `;

        // 加载系统信息
        await this.loadSystemInfo();
    }

    // AI助手页面
    async loadAIAssistantPage() {
        const page = document.getElementById('ai-assistant-page');
        if (!page) return;

        page.innerHTML = `
            <div class="page-header">
                <h2 class="page-title">
                    <i class="fas fa-robot"></i>
                    AI助手
                    <span class="beta-badge">Beta</span>
                </h2>
                <div class="page-actions">
                    <button class="btn btn-primary" onclick="adminDashboard.clearAIChat()">
                        <i class="fas fa-broom"></i> 清空对话
                    </button>
                </div>
            </div>

            <div class="ai-container">
                <div class="ai-sidebar">
                    <h3>快捷指令</h3>
                    <div class="quick-commands">
                        <button class="quick-cmd" data-cmd="分析最新的优化结果">
                            <i class="fas fa-chart-line"></i>
                            分析最新优化结果
                        </button>
                        <button class="quick-cmd" data-cmd="推荐最佳装载方案">
                            <i class="fas fa-lightbulb"></i>
                            推荐最佳装载方案
                        </button>
                        <button class="quick-cmd" data-cmd="检查系统性能">
                            <i class="fas fa-tachometer-alt"></i>
                            检查系统性能
                        </button>
                        <button class="quick-cmd" data-cmd="生成效率报告">
                            <i class="fas fa-file-alt"></i>
                            生成效率报告
                        </button>
                    </div>

                    <h3>AI能力</h3>
                    <div class="ai-features">
                        <div class="feature-item">
                            <i class="fas fa-comments"></i>
                            <span>智能问答</span>
                        </div>
                        <div class="feature-item">
                            <i class="fas fa-chart-bar"></i>
                            <span>数据分析</span>
                        </div>
                        <div class="feature-item">
                            <i class="fas fa-magic"></i>
                            <span>优化建议</span>
                        </div>
                        <div class="feature-item">
                            <i class="fas fa-search"></i>
                            <span>智能搜索</span>
                        </div>
                    </div>
                </div>

                <div class="ai-main">
                    <div class="chat-container">
                        <div class="chat-messages" id="chatMessages">
                            <div class="message ai-message">
                                <div class="message-avatar">
                                    <i class="fas fa-robot"></i>
                                </div>
                                <div class="message-content">
                                    <div class="message-text">
                                        您好！我是巧满装载平台的AI助手。我可以帮助您：
                                        <br>• 分析优化结果和效率数据
                                        <br>• 推荐最佳装载和路径方案
                                        <br>• 回答系统使用相关问题
                                        <br>• 提供智能化的操作建议
                                        <br><br>请告诉我您需要什么帮助？
                                    </div>
                                    <div class="message-time">刚刚</div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div class="chat-input-container">
                        <div class="input-wrapper">
                            <textarea id="aiInput" placeholder="输入您的问题..." rows="2"></textarea>
                            <button class="send-btn" id="sendMessage">
                                <i class="fas fa-paper-plane"></i>
                            </button>
                        </div>
                        <div class="input-actions">
                            <button class="action-btn" title="语音输入">
                                <i class="fas fa-microphone"></i>
                            </button>
                            <button class="action-btn" title="上传文件">
                                <i class="fas fa-paperclip"></i>
                            </button>
                            <span class="input-counter">0/1000</span>
                        </div>
                    </div>
                </div>
            </div>

            <div class="ai-notice">
                <i class="fas fa-info-circle"></i>
                <span>AI助手功能正在开发中，目前仅提供基础问答功能。</span>
            </div>
        `;

        // 绑定AI助手事件
        this.initAIAssistant();
    }

    // 清理方法
    destroy() {
        this.stopPeriodicRefresh();

        // 清理图表
        Object.values(this.charts).forEach(chart => {
            if (chart && typeof chart.destroy === 'function') {
                chart.destroy();
            }
        });

        this.charts = {};
    }

    // 系统维护功能
    async clearCache() {
        this.showNotification('正在清理缓存...', 'info');

        try {
            const response = await fetch('/api/system/clear-cache', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`,
                    'Content-Type': 'application/json'
                }
            });

            if (response.ok) {
                this.showNotification('缓存清理完成', 'success');
                // 刷新页面数据
                await this.loadInitialData();
            } else {
                throw new Error('清理缓存失败');
            }
        } catch (error) {
            console.error('清理缓存出错:', error);
            this.showNotification('清理缓存失败', 'error');
        }
    }

    async runSystemCheck() {
        this.showNotification('正在进行系统检查...', 'info');

        try {
            const response = await fetch('/api/system/health-check', {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                }
            });

            const data = await response.json();

            if (data.success) {
                const report = data.data;
                let message = `系统检查完成\n`;
                message += `CPU: ${report.cpu_usage}%\n`;
                message += `内存: ${report.memory_usage}%\n`;
                message += `磁盘: ${report.disk_usage}%\n`;
                message += `数据库: ${report.database_status}\n`;
                message += `API服务: ${report.api_status}`;

                this.showNotification(message, report.overall_status === 'healthy' ? 'success' : 'warning');
            } else {
                throw new Error(data.message);
            }
        } catch (error) {
            console.error('系统检查出错:', error);
            this.showNotification('系统检查失败', 'error');
        }
    }

    async exportLogs() {
        this.showNotification('正在导出日志...', 'info');

        try {
            const response = await fetch('/api/system/export-logs', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    start_date: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString(),
                    end_date: new Date().toISOString()
                })
            });

            if (response.ok) {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `system_logs_${new Date().toISOString().split('T')[0]}.zip`;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                window.URL.revokeObjectURL(url);

                this.showNotification('日志导出成功', 'success');
            } else {
                throw new Error('导出日志失败');
            }
        } catch (error) {
            console.error('导出日志出错:', error);
            this.showNotification('导出日志失败', 'error');
        }
    }

    async restartSystem() {
        const confirmed = confirm('确定要重启系统吗？这将中断所有正在运行的任务。');
        if (!confirmed) return;

        this.showNotification('正在重启系统...', 'warning');

        try {
            const response = await fetch('/api/system/restart', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`,
                    'Content-Type': 'application/json'
                }
            });

            if (response.ok) {
                this.showNotification('系统重启指令已发送，页面将在10秒后刷新', 'info');
                setTimeout(() => {
                    window.location.reload();
                }, 10000);
            } else {
                throw new Error('重启系统失败');
            }
        } catch (error) {
            console.error('重启系统出错:', error);
            this.showNotification('重启系统失败', 'error');
        }
    }

    async loadSystemInfo() {
        try {
            const response = await fetch('/api/system/info', {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                }
            });

            const data = await response.json();

            if (data.success) {
                const info = data.data;

                // 更新系统信息显示
                const elements = {
                    maxFileSize: document.getElementById('maxFileSize'),
                    smtpServer: document.getElementById('smtpServer'),
                    senderEmail: document.getElementById('senderEmail'),
                    sessionTimeout: document.getElementById('sessionTimeout'),
                    minPasswordLength: document.getElementById('minPasswordLength'),
                    autoBackup: document.getElementById('autoBackup'),
                    enableEmailNotify: document.getElementById('enableEmailNotify'),
                    requireStrongPassword: document.getElementById('requireStrongPassword')
                };

                if (elements.maxFileSize) elements.maxFileSize.value = info.max_file_size || 100;
                if (elements.smtpServer) elements.smtpServer.value = info.smtp_server || '';
                if (elements.senderEmail) elements.senderEmail.value = info.sender_email || '';
                if (elements.sessionTimeout) elements.sessionTimeout.value = info.session_timeout || 8;
                if (elements.minPasswordLength) elements.minPasswordLength.value = info.min_password_length || 8;
                if (elements.autoBackup) elements.autoBackup.checked = info.auto_backup || false;
                if (elements.enableEmailNotify) elements.enableEmailNotify.checked = info.enable_email_notify || false;
                if (elements.requireStrongPassword) elements.requireStrongPassword.checked = info.require_strong_password || true;
            }
        } catch (error) {
            console.error('加载系统信息出错:', error);
        }
    }

    clearAIChat() {
        const chatMessages = document.getElementById('chatMessages');
        if (chatMessages) {
            chatMessages.innerHTML = `
                <div class="message ai-message">
                    <div class="message-avatar">
                        <i class="fas fa-robot"></i>
                    </div>
                    <div class="message-content">
                        <p>你好！我是巧满装载平台的AI助手。我可以帮助您：</p>
                        <ul>
                            <li>分析优化结果和装载效率</li>
                            <li>提供最佳装载方案建议</li>
                            <li>检查系统运行状态</li>
                            <li>生成各类报告和分析</li>
                        </ul>
                        <p>有什么我可以帮助您的吗？</p>
                    </div>
                </div>
            `;
            this.showNotification('对话已清空', 'success');
        }
    }

    // API集成和数据加载功能
    async apiRequest(endpoint, options = {}) {
        const defaultOptions = {
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('token')}`,
                'Content-Type': 'application/json'
            }
        };

        const finalOptions = {
            ...defaultOptions,
            ...options,
            headers: {
                ...defaultOptions.headers,
                ...options.headers
            }
        };

        try {
            const response = await fetch(endpoint, finalOptions);

            if (response.status === 401) {
                // Token过期，重定向到登录页
                localStorage.removeItem('token');
                window.location.href = '/login.html';
                return;
            }

            const data = await response.json();
            return data;
        } catch (error) {
            console.error('API请求失败:', error);
            throw error;
        }
    }

    // 表单提交处理器
    setupFormHandlers() {
        // 优化任务表单
        const optimizationForm = document.getElementById('optimization-form');
        if (optimizationForm) {
            optimizationForm.addEventListener('submit', async (e) => {
                e.preventDefault();
                await this.submitOptimizationTask(e.target);
            });
        }

        // 用户管理表单
        const userForm = document.getElementById('user-form');
        if (userForm) {
            userForm.addEventListener('submit', async (e) => {
                e.preventDefault();
                await this.handleUserFormSubmit(e.target);
            });
        }

        // 设置页面保存按钮
        const saveSettingsBtn = document.getElementById('saveSettings');
        if (saveSettingsBtn) {
            saveSettingsBtn.addEventListener('click', () => this.saveSystemSettings());
        }
    }

    async submitOptimizationTask(form) {
        const formData = new FormData(form);
        const taskData = {
            algorithm: formData.get('algorithm'),
            data_source: formData.get('data-source'),
            generate_visualization: formData.get('generate-viz') === 'on',
            parameters: {}
        };

        this.showNotification('正在启动优化任务...', 'info');

        try {
            const response = await this.apiRequest('/api/optimization/run', {
                method: 'POST',
                body: JSON.stringify(taskData)
            });

            if (response.success) {
                this.showNotification(`优化任务已启动，任务ID: ${response.data.task_id}`, 'success');
                // 切换到任务监控页面
                this.navigateToPage('task-monitor');
                // 刷新任务列表
                await this.loadTaskMonitorPage();
            } else {
                throw new Error(response.message);
            }
        } catch (error) {
            console.error('提交优化任务失败:', error);
            this.showNotification('启动优化任务失败', 'error');
        }
    }

    async handleUserFormSubmit(form) {
        const formData = new FormData(form);
        const userData = {
            username: formData.get('username'),
            email: formData.get('email'),
            role: formData.get('role'),
            department: formData.get('department')
        };

        if (formData.get('password')) {
            userData.password = formData.get('password');
        }

        const isEdit = form.dataset.mode === 'edit';
        const userId = form.dataset.userId;

        try {
            const endpoint = isEdit ? `/api/users/${userId}` : '/api/users';
            const method = isEdit ? 'PUT' : 'POST';

            const response = await this.apiRequest(endpoint, {
                method: method,
                body: JSON.stringify(userData)
            });

            if (response.success) {
                this.showNotification(isEdit ? '用户信息已更新' : '用户创建成功', 'success');
                // 关闭模态框
                const modal = document.querySelector('.modal.show');
                if (modal) {
                    modal.classList.remove('show');
                }
                // 刷新用户列表
                await this.loadUserManagementPage();
            } else {
                throw new Error(response.message);
            }
        } catch (error) {
            console.error('保存用户信息失败:', error);
            this.showNotification('保存用户信息失败', 'error');
        }
    }

    async saveSystemSettings() {
        const settings = {
            max_file_size: document.getElementById('maxFileSize')?.value || 100,
            smtp_server: document.getElementById('smtpServer')?.value || '',
            sender_email: document.getElementById('senderEmail')?.value || '',
            session_timeout: document.getElementById('sessionTimeout')?.value || 8,
            min_password_length: document.getElementById('minPasswordLength')?.value || 8,
            auto_backup: document.getElementById('autoBackup')?.checked || false,
            enable_email_notify: document.getElementById('enableEmailNotify')?.checked || false,
            require_strong_password: document.getElementById('requireStrongPassword')?.checked || true
        };

        this.showNotification('正在保存系统设置...', 'info');

        try {
            const response = await this.apiRequest('/api/system/settings', {
                method: 'PUT',
                body: JSON.stringify(settings)
            });

            if (response.success) {
                this.showNotification('系统设置保存成功', 'success');
            } else {
                throw new Error(response.message);
            }
        } catch (error) {
            console.error('保存系统设置失败:', error);
            this.showNotification('保存系统设置失败', 'error');
        }
    }

    // 文件上传处理
    setupFileUpload() {
        const uploadZone = document.querySelector('.upload-zone');
        const fileInput = document.getElementById('fileInput');

        if (uploadZone && fileInput) {
            // 拖拽上传
            uploadZone.addEventListener('dragover', (e) => {
                e.preventDefault();
                uploadZone.classList.add('drag-over');
            });

            uploadZone.addEventListener('dragleave', () => {
                uploadZone.classList.remove('drag-over');
            });

            uploadZone.addEventListener('drop', (e) => {
                e.preventDefault();
                uploadZone.classList.remove('drag-over');
                const files = e.dataTransfer.files;
                if (files.length > 0) {
                    this.handleFileUpload(files[0]);
                }
            });

            // 点击上传
            uploadZone.addEventListener('click', () => {
                fileInput.click();
            });

            fileInput.addEventListener('change', (e) => {
                if (e.target.files.length > 0) {
                    this.handleFileUpload(e.target.files[0]);
                }
            });
        }
    }

    async handleFileUpload(file) {
        if (!file.name.match(/\.(xlsx|xls)$/i)) {
            this.showNotification('请选择Excel文件 (.xlsx 或 .xls)', 'error');
            return;
        }

        const maxSize = 100 * 1024 * 1024; // 100MB
        if (file.size > maxSize) {
            this.showNotification('文件大小超过限制', 'error');
            return;
        }

        const formData = new FormData();
        formData.append('file', file);

        this.showNotification('正在上传文件...', 'info');

        try {
            const response = await fetch('/api/data/upload', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                },
                body: formData
            });

            const data = await response.json();

            if (data.success) {
                this.showNotification('文件上传成功', 'success');
                // 显示数据预览
                this.showDataPreview(data.data);
            } else {
                throw new Error(data.message);
            }
        } catch (error) {
            console.error('文件上传失败:', error);
            this.showNotification('文件上传失败', 'error');
        }
    }

    showDataPreview(data) {
        const previewContainer = document.querySelector('.data-preview');
        if (previewContainer && data.preview) {
            previewContainer.style.display = 'block';

            const tableHTML = `
                <table>
                    <thead>
                        <tr>
                            ${data.headers.map(header => `<th>${header}</th>`).join('')}
                        </tr>
                    </thead>
                    <tbody>
                        ${data.preview.slice(0, 5).map(row => `
                            <tr>
                                ${row.map(cell => `<td>${cell}</td>`).join('')}
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            `;

            const previewTable = previewContainer.querySelector('.preview-table');
            if (previewTable) {
                previewTable.innerHTML = tableHTML;
            }

            const previewInfo = previewContainer.querySelector('.preview-info');
            if (previewInfo) {
                previewInfo.textContent = `共 ${data.total_rows} 行数据，显示前 5 行`;
            }
        }
    }
}

// 全局实例
let adminDashboard;

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', () => {
    adminDashboard = new AdminDashboard();
});

// 页面卸载时清理
window.addEventListener('beforeunload', () => {
    if (adminDashboard) {
        adminDashboard.destroy();
    }
});

// CSS for notifications (添加到现有的CSS中)
const notificationStyles = `
.notifications-container {
    pointer-events: none;
}

.notification {
    background: white;
    border-radius: 8px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    padding: 16px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    min-width: 300px;
    pointer-events: auto;
    animation: slideInRight 0.3s ease;
    border-left: 4px solid #3498db;
}

.notification-success {
    border-left-color: #27ae60;
}

.notification-error {
    border-left-color: #e74c3c;
}

.notification-warning {
    border-left-color: #f39c12;
}

.notification-content {
    display: flex;
    align-items: center;
    gap: 12px;
    flex: 1;
}

.notification-content i {
    font-size: 16px;
}

.notification-success .notification-content i {
    color: #27ae60;
}

.notification-error .notification-content i {
    color: #e74c3c;
}

.notification-warning .notification-content i {
    color: #f39c12;
}

.notification-close {
    background: none;
    border: none;
    color: #7f8c8d;
    cursor: pointer;
    padding: 4px;
    border-radius: 4px;
}

.notification-close:hover {
    background: #ecf0f1;
    color: #2c3e50;
}

@keyframes slideInRight {
    from {
        transform: translateX(100%);
        opacity: 0;
    }
    to {
        transform: translateX(0);
        opacity: 1;
    }
}

@keyframes slideOutRight {
    from {
        transform: translateX(0);
        opacity: 1;
    }
    to {
        transform: translateX(100%);
        opacity: 0;
    }
}

/* 拖拽上传样式 */
.upload-area {
    max-width: 800px;
    margin: 0 auto;
}

.upload-zone {
    border: 2px dashed #dee2e6;
    border-radius: 12px;
    padding: 60px 20px;
    text-align: center;
    background: #f8f9fa;
    transition: all 0.3s ease;
    cursor: pointer;
}

.upload-zone:hover,
.upload-zone.drag-over {
    border-color: #3498db;
    background: rgba(52, 152, 219, 0.05);
}

.upload-icon {
    font-size: 48px;
    color: #3498db;
    margin-bottom: 16px;
}

.upload-zone h3 {
    margin-bottom: 8px;
    color: #2c3e50;
}

.upload-btn {
    background: #3498db;
    color: white;
    border: none;
    padding: 8px 16px;
    border-radius: 6px;
    cursor: pointer;
    text-decoration: underline;
}

.upload-info {
    margin-top: 12px;
    color: #7f8c8d;
}

.upload-progress {
    margin-top: 20px;
    padding: 20px;
    background: white;
    border-radius: 8px;
    border: 1px solid #dee2e6;
}

.progress-bar {
    width: 100%;
    height: 8px;
    background: #ecf0f1;
    border-radius: 4px;
    overflow: hidden;
    margin-bottom: 8px;
}

.progress-fill {
    height: 100%;
    background: #3498db;
    border-radius: 4px;
    transition: width 0.3s ease;
    width: 0%;
}

.progress-text {
    text-align: center;
    color: #7f8c8d;
    font-size: 14px;
}

.data-preview {
    margin-top: 30px;
    background: white;
    border-radius: 8px;
    border: 1px solid #dee2e6;
    overflow: hidden;
}

.data-preview h3 {
    padding: 20px;
    margin: 0;
    background: #f8f9fa;
    border-bottom: 1px solid #dee2e6;
}

.preview-table table {
    width: 100%;
    border-collapse: collapse;
}

.preview-table th,
.preview-table td {
    padding: 12px;
    text-align: left;
    border-bottom: 1px solid #dee2e6;
}

.preview-table th {
    background: #f8f9fa;
    font-weight: 600;
}

.preview-info {
    padding: 16px 20px;
    background: #f8f9fa;
    border-top: 1px solid #dee2e6;
    color: #7f8c8d;
    font-size: 14px;
}

.preview-actions {
    padding: 20px;
    display: flex;
    gap: 12px;
    justify-content: flex-end;
}
`;

// 添加样式到页面
const styleSheet = document.createElement('style');
styleSheet.textContent = notificationStyles;
document.head.appendChild(styleSheet);

// ================== 优化功能实现 ==================

    // 显示优化启动模态框
    showOptimizationStartModal() {
        const modal = document.getElementById('modal');
        if (!modal) {
            this.createModal();
        }

        const modalContent = `
            <div class="modal-header">
                <h3 class="modal-title">
                    <i class="fas fa-rocket"></i>
                    启动优化运算
                </h3>
                <button class="modal-close" onclick="adminDashboard.closeModal()">
                    <i class="fas fa-times"></i>
                </button>
            </div>
            <div class="modal-body">
                <div class="optimization-config">
                    <div class="config-section">
                        <h4>
                            <i class="fas fa-cogs"></i>
                            优化算法选择
                        </h4>
                        <div class="config-grid">
                            <div class="config-item">
                                <label>
                                    <input type="radio" name="algorithm" value="gurobi_3dpp" checked>
                                    <span>Gurobi 3D装载优化</span>
                                </label>
                                <small>高精度3D装载求解，适合大型货物</small>
                            </div>
                            <div class="config-item">
                                <label>
                                    <input type="radio" name="algorithm" value="ltl_optimizer">
                                    <span>LTL拼装优化</span>
                                </label>
                                <small>零担货物智能拼装算法</small>
                            </div>
                            <div class="config-item">
                                <label>
                                    <input type="radio" name="algorithm" value="vrp_basic">
                                    <span>路径优化</span>
                                </label>
                                <small>基础车辆路径规划</small>
                            </div>
                            <div class="config-item">
                                <label>
                                    <input type="radio" name="algorithm" value="integrated">
                                    <span>集成优化</span>
                                </label>
                                <small>装载与路径集成解决方案</small>
                            </div>
                        </div>
                    </div>

                    <div class="config-section">
                        <h4>
                            <i class="fas fa-sliders-h"></i>
                            优化参数设置
                        </h4>
                        <div class="parameter-grid">
                            <div class="parameter-item">
                                <label>数据源</label>
                                <select id="dataSource">
                                    <option value="cargo_data.xlsx">货物数据.xlsx</option>
                                    <option value="orders_data.xlsx">订单数据.xlsx</option>
                                    <option value="synthetic">模拟数据</option>
                                </select>
                            </div>
                            <div class="parameter-item">
                                <label>最大车辆数</label>
                                <input type="number" id="maxTrucks" value="20" min="1" max="50">
                            </div>
                            <div class="parameter-item">
                                <label>时间限制(分钟)</label>
                                <input type="number" id="timeLimit" value="5" min="1" max="30">
                            </div>
                            <div class="parameter-item">
                                <label>启用可视化</label>
                                <input type="checkbox" id="enableVisualization" checked>
                            </div>
                        </div>
                    </div>

                    <div class="config-section">
                        <h4>
                            <i class="fas fa-info-circle"></i>
                            预估信息
                        </h4>
                        <div class="estimate-info">
                            <div class="estimate-item">
                                <span class="estimate-label">预计执行时间:</span>
                                <span class="estimate-value" id="estimatedTime">5-10 分钟</span>
                            </div>
                            <div class="estimate-item">
                                <span class="estimate-label">预计处理货物:</span>
                                <span class="estimate-value">约 500-800 件</span>
                            </div>
                            <div class="estimate-item">
                                <span class="estimate-label">内存需求:</span>
                                <span class="estimate-value">约 2-4 GB</span>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="modal-actions">
                    <button class="btn btn-secondary" onclick="adminDashboard.closeModal()">取消</button>
                    <button class="btn btn-primary" onclick="adminDashboard.startOptimization()">
                        <i class="fas fa-play"></i>
                        开始优化
                    </button>
                </div>
            </div>
        `;

        modal.innerHTML = modalContent;
        modal.style.display = 'flex';

        // 绑定算法选择事件
        document.querySelectorAll('input[name="algorithm"]').forEach(radio => {
            radio.addEventListener('change', (e) => this.updateAlgorithmEstimate(e.target.value));
        });

        // 绑定参数变更事件
        document.getElementById('timeLimit')?.addEventListener('change', (e) => {
            this.updateTimeEstimate(e.target.value);
        });
    }

    // 更新算法预估时间
    updateAlgorithmEstimate(algorithm) {
        const timeMap = {
            'gurobi_3dpp': '8-15 分钟',
            'ltl_optimizer': '3-5 分钟',
            'vrp_basic': '2-4 分钟',
            'integrated': '10-20 分钟'
        };
        document.getElementById('estimatedTime').textContent = timeMap[algorithm] || '5-10 分钟';
    }

    // 更新时间预估
    updateTimeEstimate(timeLimit) {
        const minutes = parseInt(timeLimit);
        const estimate = `${minutes}-${minutes * 2} 分钟`;
        document.getElementById('estimatedTime').textContent = estimate;
    }

    // 启动优化任务
    async startOptimization() {
        // 获取配置参数
        const algorithm = document.querySelector('input[name="algorithm"]:checked').value;
        const dataSource = document.getElementById('dataSource').value;
        const maxTrucks = parseInt(document.getElementById('maxTrucks').value);
        const timeLimit = parseInt(document.getElementById('timeLimit').value);
        const enableVisualization = document.getElementById('enableVisualization').checked;

        // 显示加载遮罩
        this.showLoading('启动优化任务中...');

        try {
            // 调用API启动优化
            const response = await fetch('/api/optimization/run', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    algorithm: algorithm,
                    data_source: dataSource,
                    parameters: {
                        max_trucks: maxTrucks,
                        optimization_time_limit: timeLimit * 60,
                        enable_visualization: enableVisualization,
                        enable_route_optimization: true,
                        use_enhanced: true
                    }
                })
            });

            const result = await response.json();

            if (result.success) {
                this.closeModal();
                this.hideLoading();

                // 显示任务启动成功
                this.showNotification('success', '优化任务启动成功',
                    `任务ID: ${result.data.task_id}，预计 ${timeLimit*2} 分钟内完成`);

                // 切换到任务监控页面
                setTimeout(() => {
                    this.navigateToPage('task-monitor');
                    this.startMonitoringTask(result.data.task_id);
                }, 1000);

            } else {
                throw new Error(result.message || '启动优化失败');
            }

        } catch (error) {
            this.hideLoading();
            this.showNotification('error', '优化启动失败', error.message);
        }
    }

    // 开始监控任务
    startMonitoringTask(taskId) {
        if (!taskId) return;

        this.currentTaskId = taskId;
        this.taskMonitoringInterval = setInterval(async () => {
            try {
                const response = await fetch(`/api/optimization/status/${taskId}`);
                const result = await response.json();

                if (result.success) {
                    this.updateTaskProgress(result.data);

                    // 如果任务完成，停止监控并显示结果
                    if (result.data.status === 'completed') {
                        clearInterval(this.taskMonitoringInterval);
                        this.showOptimizationResults(taskId);
                    } else if (result.data.status === 'failed') {
                        clearInterval(this.taskMonitoringInterval);
                        this.showNotification('error', '优化任务失败', result.data.message || '未知错误');
                    }
                }
            } catch (error) {
                console.error('监控任务状态失败:', error);
            }
        }, 2000); // 每2秒查询一次
    }

    // 更新任务进度
    updateTaskProgress(taskData) {
        // 更新进度条
        const progressBar = document.getElementById('taskProgressBar');
        if (progressBar) {
            progressBar.style.width = `${taskData.progress}%`;
            progressBar.textContent = `${taskData.progress}%`;
        }

        // 更新状态文本
        const statusText = document.getElementById('taskStatusText');
        if (statusText) {
            statusText.textContent = taskData.message;
        }

        // 更新状态徽章
        const statusBadge = document.getElementById('taskStatusBadge');
        if (statusBadge) {
            statusBadge.textContent = taskData.status;
            statusBadge.className = `status-badge ${taskData.status}`;
        }
    }

    // 显示优化结果
    async showOptimizationResults(taskId) {
        try {
            const response = await fetch(`/api/optimization/result/${taskId}`);
            const result = await response.json();

            if (result.success && result.data) {
                this.displayOptimizationResults(result.data);
                this.showNotification('success', '优化任务完成', `成功处理 ${result.data.total_items_processed} 个货物`);
            } else {
                throw new Error('获取优化结果失败');
            }

        } catch (error) {
            this.showNotification('error', '获取结果失败', error.message);
        }
    }

    // 显示优化结果详情
    displayOptimizationResults(data) {
        const resultsPage = document.getElementById('loading-results-page');
        if (!resultsPage) return;

        resultsPage.innerHTML = `
            <div class="page-header">
                <h2 class="page-title">
                    <i class="fas fa-check-circle" style="color: #4caf50;"></i>
                    优化任务结果
                </h2>
                <div class="page-actions">
                    <button class="btn btn-primary" onclick="adminDashboard.view3DResults()">
                        <i class="fas fa-cube"></i> 3D视图
                    </button>
                    <button class="btn btn-secondary" onclick="adminDashboard.downloadResults()">
                        <i class="fas fa-download"></i> 下载结果
                    </button>
                </div>
            </div>

            <!-- 结果摘要 -->
            <div class="results-summary">
                <div class="summary-grid">
                    <div class="summary-card">
                        <h3>🚛 处理车辆数</h3>
                        <p class="summary-value">${data.total_trucks}</p>
                    </div>
                    <div class="summary-card">
                        <h3>📦 处理货物数</h3>
                        <p class="summary-value">${data.total_items_processed}</p>
                    </div>
                    <div class="summary-card">
                        <h3>📊 平均装载率</h3>
                        <p class="summary-value">${data.average_loading_efficiency.toFixed(1)}%</p>
                    </div>
                    <div class="summary-card">
                        <h3>🛣️ 总行驶距离</h3>
                        <p class="summary-value">${data.total_distance_km.toFixed(1)} km</p>
                    </div>
                </div>
            </div>

            <!-- 3D可视化容器 -->
            <div class="visualization-container">
                <h3>
                    <i class="fas fa-cube"></i>
                    3D装载方案可视化
                </h3>
                <div class="visualization-tabs">
                    <button class="tab-btn active" onclick="adminDashboard.showVisualizationTab('overview')">总览</button>
                    <button class="tab-btn" onclick="adminDashboard.showVisualizationTab('details')">详细</button>
                    <button class="tab-btn" onclick="adminDashboard.showVisualizationTab('comparison')">对比</button>
                </div>
                <div id="visualizationContent" class="visualization-content">
                    ${this.generateVisualizationContent(data)}
                </div>
            </div>
        `;
    }

    // 生成可视化内容
    generateVisualizationContent(data) {
        // 如果有可视化文件，显示第一个
        if (data.visualization_files && data.visualization_files.length > 0) {
            const firstVisualization = data.visualization_files[0];
            return `
                <iframe
                    src="/visualizations/${firstVisualization}"
                    width="100%"
                    height="600px"
                    frameborder="0"
                    style="border-radius: 12px; box-shadow: 0 8px 25px rgba(0,0,0,0.1);">
                </iframe>
            `;
        }

        return `
            <div class="placeholder-content">
                <i class="fas fa-cube" style="font-size: 48px; color: #ccc;"></i>
                <p>3D可视化文件生成中...</p>
            </div>
        `;
    }

    // 创建模态框
    createModal() {
        const modal = document.createElement('div');
        modal.id = 'modal';
        modal.className = 'modal';
        modal.style.display = 'none';
        document.body.appendChild(modal);
    }

    // 显示加载遮罩
    showLoading(message = '加载中...') {
        let loadingOverlay = document.getElementById('loadingOverlay');
        if (!loadingOverlay) {
            loadingOverlay = document.createElement('div');
            loadingOverlay.id = 'loadingOverlay';
            loadingOverlay.className = 'loading-overlay';
            loadingOverlay.innerHTML = `
                <div class="loading-spinner">
                    <div class="spinner"></div>
                    <p class="loading-text">${message}</p>
                </div>
            `;
            document.body.appendChild(loadingOverlay);
        }
        loadingOverlay.querySelector('.loading-text').textContent = message;
        loadingOverlay.style.display = 'flex';
    }

    // 隐藏加载遮罩
    hideLoading() {
        const loadingOverlay = document.getElementById('loadingOverlay');
        if (loadingOverlay) {
            loadingOverlay.style.display = 'none';
        }
    }

    // 显示通知
    showNotification(type, title, message) {
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <div class="notification-icon">
                <i class="fas ${type === 'success' ? 'fa-check-circle' : 'fa-exclamation-circle'}"></i>
            </div>
            <div class="notification-content">
                <h4>${title}</h4>
                <p>${message}</p>
            </div>
            <button class="notification-close" onclick="this.parentElement.remove()">
                <i class="fas fa-times"></i>
            </button>
        `;

        document.body.appendChild(notification);

        // 自动移除通知
        setTimeout(() => {
            notification.remove();
        }, 5000);
    }