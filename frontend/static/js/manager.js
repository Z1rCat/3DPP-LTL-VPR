/**
 * 管理层JavaScript功能
 * Manager Dashboard JavaScript Functions
 */

class ManagerDashboard {
    constructor() {
        this.currentSection = 'dashboard';
        this.currentDate = new Date();
        this.currentView = 'day';
        this.costData = null;
        this.vehicleData = null;
        this.charts = {};

        this.init();
    }

    /**
     * 初始化管理层仪表板
     */
    init() {
        this.setupEventListeners();
        this.setDateInput();
        this.loadDashboardData();
        this.switchSection('dashboard');
    }

    /**
     * 设置事件监听器
     */
    setupEventListeners() {
        // 导航菜单
        document.querySelectorAll('.nav-link').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const sectionId = link.getAttribute('href').substring(1);
                this.switchSection(sectionId);
            });
        });

        // 日期控制
        document.getElementById('prev-day-btn')?.addEventListener('click', () => {
            this.changeDate(-1);
        });

        document.getElementById('next-day-btn')?.addEventListener('click', () => {
            this.changeDate(1);
        });

        document.getElementById('today-btn')?.addEventListener('click', () => {
            this.setCurrentDate();
        });

        document.getElementById('date-input')?.addEventListener('change', (e) => {
            this.currentDate = new Date(e.target.value);
            this.loadDashboardData();
        });

        // 视图控制
        document.querySelectorAll('.view-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                document.querySelectorAll('.view-btn').forEach(b => b.classList.remove('active'));
                e.target.classList.add('active');
                this.currentView = e.target.dataset.view;
                this.loadDashboardData();
            });
        });

        // 成本分析控制
        document.getElementById('cost-period-select')?.addEventListener('change', () => {
            this.updateCostTrendChart();
        });

        // 车辆搜索
        document.getElementById('vehicle-search')?.addEventListener('input', (e) => {
            this.filterVehicleTable(e.target.value);
        });

        // 导出按钮
        document.getElementById('export-btn')?.addEventListener('click', () => {
            this.exportToExcel();
        });

        // 车辆地图控制
        document.getElementById('refresh-vehicle-map-btn')?.addEventListener('click', () => {
            this.refreshVehicleMap();
        });

        document.getElementById('vehicle-filter-select')?.addEventListener('change', (e) => {
            this.filterVehicles(e.target.value);
        });

        // 报告生成
        document.getElementById('generate-report-btn')?.addEventListener('click', () => {
            this.generateReport();
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

        this.currentSection = sectionId;

        // 根据当前部分加载数据
        switch(sectionId) {
            case 'dashboard':
                this.loadDashboardData();
                break;
            case 'vehicles':
                this.loadVehicleData();
                break;
            case 'efficiency':
                this.loadEfficiencyData();
                break;
            case 'reports':
                this.loadReportsData();
                break;
        }
    }

    /**
     * 设置日期输入
     */
    setDateInput() {
        const dateInput = document.getElementById('date-input');
        if (dateInput) {
            dateInput.value = this.formatDate(this.currentDate);
        }
    }

    /**
     * 格式化日期
     */
    formatDate(date) {
        return date.toISOString().split('T')[0];
    }

    /**
     * 改变日期
     */
    changeDate(days) {
        this.currentDate.setDate(this.currentDate.getDate() + days);
        this.setDateInput();
        this.loadDashboardData();
    }

    /**
     * 设置当前日期
     */
    setCurrentDate() {
        this.currentDate = new Date();
        this.setDateInput();
        this.loadDashboardData();
    }

    /**
     * 加载仪表板数据
     */
    async loadDashboardData() {
        try {
            this.updateMetrics();
            this.initializeCharts();
            this.loadCostTable();
        } catch (error) {
            console.error('加载仪表板数据失败:', error);
        }
    }

    /**
     * 更新关键指标
     */
    updateMetrics() {
        // 模拟数据
        const metrics = {
            dailyTotalCost: 12580,
            fuelCost: 3200,
            avgLoadingRate: 78.5,
            carbonEmission: 245.6
        };

        document.getElementById('daily-total-cost').textContent = `¥${metrics.dailyTotalCost.toLocaleString()}`;
        document.getElementById('fuel-cost').textContent = `¥${metrics.fuelCost.toLocaleString()}`;
        document.getElementById('avg-loading-rate').textContent = `${metrics.avgLoadingRate}%`;
        document.getElementById('carbon-emission').textContent = `${metrics.carbonEmission}kg`;
    }

    /**
     * 初始化图表
     */
    initializeCharts() {
        this.createCostTrendChart();
        this.createCostBreakdownChart();
        this.createVehicleCostChart();
        this.createEfficiencyCostChart();
    }

    /**
     * 创建成本趋势图表
     */
    createCostTrendChart() {
        const ctx = document.getElementById('costTrendChart');
        if (!ctx) return;

        if (this.charts.costTrend) {
            this.charts.costTrend.destroy();
        }

        const days = parseInt(document.getElementById('cost-period-select')?.value || 7);
        const labels = [];
        const data = [];

        for (let i = days - 1; i >= 0; i--) {
            const date = new Date();
            date.setDate(date.getDate() - i);
            labels.push(this.formatDate(date));
            data.push(Math.floor(Math.random() * 5000) + 10000);
        }

        this.charts.costTrend = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: '每日总成本',
                    data: data,
                    borderColor: '#3498db',
                    backgroundColor: 'rgba(52, 152, 219, 0.1)',
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
                        position: 'top'
                    }
                },
                scales: {
                    y: {
                        beginAtZero: false,
                        ticks: {
                            callback: function(value) {
                                return '¥' + value.toLocaleString();
                            }
                        }
                    }
                }
            }
        });
    }

    /**
     * 创建成本构成图表
     */
    createCostBreakdownChart() {
        const ctx = document.getElementById('costBreakdownChart');
        if (!ctx) return;

        if (this.charts.costBreakdown) {
            this.charts.costBreakdown.destroy();
        }

        this.charts.costBreakdown = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['燃油成本', '人工成本', '维护成本', '折旧成本', '其他成本'],
                datasets: [{
                    data: [3200, 4800, 1800, 2200, 580],
                    backgroundColor: [
                        '#e74c3c',
                        '#3498db',
                        '#f39c12',
                        '#27ae60',
                        '#9b59b6'
                    ]
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'right'
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const label = context.label || '';
                                const value = context.parsed || 0;
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = ((value / total) * 100).toFixed(1);
                                return `${label}: ¥${value.toLocaleString()} (${percentage}%)`;
                            }
                        }
                    }
                }
            }
        });
    }

    /**
     * 创建车辆成本对比图表
     */
    createVehicleCostChart() {
        const ctx = document.getElementById('vehicleCostChart');
        if (!ctx) return;

        if (this.charts.vehicleCost) {
            this.charts.vehicleCost.destroy();
        }

        const vehicles = ['LARGE_TRUCK_000', 'LARGE_TRUCK_001', 'LTL_TRUCK_000', 'LTL_TRUCK_001'];
        const costs = vehicles.map(() => Math.floor(Math.random() * 3000) + 2000);

        this.charts.vehicleCost = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: vehicles,
                datasets: [{
                    label: '车辆成本',
                    data: costs,
                    backgroundColor: '#3498db',
                    borderColor: '#2980b9',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: function(value) {
                                return '¥' + value.toLocaleString();
                            }
                        }
                    }
                }
            }
        });
    }

    /**
     * 创建装载率vs成本关系图表
     */
    createEfficiencyCostChart() {
        const ctx = document.getElementById('efficiencyCostChart');
        if (!ctx) return;

        if (this.charts.efficiencyCost) {
            this.charts.efficiencyCost.destroy();
        }

        // 生成散点数据
        const data = [];
        for (let i = 0; i < 20; i++) {
            data.push({
                x: Math.random() * 40 + 60, // 装载率 60-100%
                y: Math.random() * 2000 + 1500 // 成本 1500-3500
            });
        }

        this.charts.efficiencyCost = new Chart(ctx, {
            type: 'scatter',
            data: {
                datasets: [{
                    label: '车辆',
                    data: data,
                    backgroundColor: 'rgba(52, 152, 219, 0.6)',
                    borderColor: '#3498db',
                    pointRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    x: {
                        title: {
                            display: true,
                            text: '装载率 (%)'
                        },
                        min: 50,
                        max: 100
                    },
                    y: {
                        title: {
                            display: true,
                            text: '成本 (¥)'
                        },
                        ticks: {
                            callback: function(value) {
                                return '¥' + value.toLocaleString();
                            }
                        }
                    }
                }
            }
        });
    }

    /**
     * 加载成本表格
     */
    async loadCostTable() {
        const tbody = document.getElementById('cost-table-body');
        if (!tbody) return;

        try {
            // 模拟数据
            const vehicles = [
                { id: 'LARGE_TRUCK_000', type: '大型货车', cost: 3280, fuel: 1200, labor: 1500, maintenance: 380, depreciation: 200, loadingRate: 85, distance: 125, carbon: 45.2, status: 'active' },
                { id: 'LARGE_TRUCK_001', type: '大型货车', cost: 2950, fuel: 980, labor: 1500, maintenance: 270, depreciation: 200, loadingRate: 78, distance: 98, carbon: 38.1, status: 'active' },
                { id: 'LTL_TRUCK_000', type: '零担货车', cost: 1850, fuel: 620, labor: 800, maintenance: 180, depreciation: 150, loadingRate: 92, distance: 65, carbon: 23.5, status: 'idle' },
                { id: 'LTL_TRUCK_001', type: '零担货车', cost: 2200, fuel: 750, labor: 800, maintenance: 250, depreciation: 200, loadingRate: 88, distance: 78, carbon: 28.3, status: 'maintenance' }
            ];

            this.vehicleData = vehicles;
            this.renderCostTable(vehicles);

        } catch (error) {
            console.error('加载成本表格失败:', error);
            tbody.innerHTML = '<tr><td colspan="10" class="loading-row">加载数据失败</td></tr>';
        }
    }

    /**
     * 渲染成本表格
     */
    renderCostTable(vehicles) {
        const tbody = document.getElementById('cost-table-body');
        if (!tbody) return;

        const rows = vehicles.map(vehicle => `
            <tr>
                <td><strong>${vehicle.id}</strong></td>
                <td>${vehicle.type}</td>
                <td>¥${vehicle.cost.toLocaleString()}</td>
                <td>¥${vehicle.fuel.toLocaleString()}</td>
                <td>¥${vehicle.labor.toLocaleString()}</td>
                <td>${vehicle.loadingRate}%</td>
                <td>${vehicle.distance} km</td>
                <td>${vehicle.carbon} kg</td>
                <td><span class="status-badge ${vehicle.status}">${this.getStatusText(vehicle.status)}</span></td>
                <td>
                    <button class="action-btn view" onclick="managerDashboard.viewVehicleDetails('${vehicle.id}')">
                        <i class="fas fa-eye"></i> 查看
                    </button>
                </td>
            </tr>
        `).join('');

        tbody.innerHTML = rows;
    }

    /**
     * 获取状态文本
     */
    getStatusText(status) {
        const statusMap = {
            'active': '运行中',
            'idle': '空闲',
            'maintenance': '维护中'
        };
        return statusMap[status] || status;
    }

    /**
     * 过滤车辆表格
     */
    filterVehicleTable(searchTerm) {
        if (!this.vehicleData) return;

        const filtered = this.vehicleData.filter(vehicle =>
            vehicle.id.toLowerCase().includes(searchTerm.toLowerCase()) ||
            vehicle.type.toLowerCase().includes(searchTerm.toLowerCase())
        );

        this.renderCostTable(filtered);
    }

    /**
     * 查看车辆详情
     */
    viewVehicleDetails(vehicleId) {
        alert(`查看车辆 ${vehicleId} 的详细信息`);
    }

    /**
     * 导出Excel
     */
    exportToExcel() {
        // 模拟导出功能
        const link = document.createElement('a');
        link.href = '/api/analytics/export/cost-analysis';
        link.download = `成本分析_${this.formatDate(this.currentDate)}.xlsx`;
        link.click();
    }

    /**
     * 加载车辆数据
     */
    async loadVehicleData() {
        try {
            this.updateFleetOverview();
            this.loadVehicleMap();
            this.loadVehicleList();
        } catch (error) {
            console.error('加载车辆数据失败:', error);
        }
    }

    /**
     * 更新车队概览
     */
    updateFleetOverview() {
        const stats = {
            total: 12,
            active: 8,
            idle: 3,
            maintenance: 1
        };

        document.getElementById('total-vehicles').textContent = stats.total;
        document.getElementById('active-vehicles').textContent = stats.active;
        document.getElementById('idle-vehicles').textContent = stats.idle;
        document.getElementById('maintenance-vehicles').textContent = stats.maintenance;
    }

    /**
     * 加载车辆地图
     */
    loadVehicleMap() {
        const container = document.getElementById('vehicle-map-container');
        if (container) {
            container.innerHTML = `
                <iframe
                    src="/visualizations/route_overview_all_vehicles.html"
                    width="100%"
                    height="100%"
                    frameborder="0">
                </iframe>
            `;
        }
    }

    /**
     * 刷新车辆地图
     */
    refreshVehicleMap() {
        const container = document.getElementById('vehicle-map-container');
        if (container) {
            container.innerHTML = '<div class="map-placeholder"><i class="fas fa-sync-alt fa-spin"></i><p>刷新地图中...</p></div>';
            setTimeout(() => {
                this.loadVehicleMap();
            }, 1000);
        }
    }

    /**
     * 加载车辆列表
     */
    loadVehicleList() {
        const container = document.getElementById('vehicle-list-container');
        if (!container) return;

        const vehicles = [
            { id: 'LARGE_TRUCK_000', type: '大型货车', driver: '张师傅', status: 'active', location: '成都市武侯区', load: '85%', nextStop: '客户A' },
            { id: 'LARGE_TRUCK_001', type: '大型货车', driver: '李师傅', status: 'active', location: '成都市高新区', load: '78%', nextStop: '客户B' },
            { id: 'LTL_TRUCK_000', type: '零担货车', driver: '王师傅', status: 'idle', location: '配送中心', load: '0%', nextStop: '-' }
        ];

        const vehicleCards = vehicles.map(vehicle => `
            <div class="vehicle-card">
                <div class="vehicle-header">
                    <div class="vehicle-title">${vehicle.id}</div>
                    <span class="status-badge ${vehicle.status}">${this.getStatusText(vehicle.status)}</span>
                </div>
                <div class="vehicle-details">
                    <div class="vehicle-detail-item">
                        <span>类型:</span>
                        <span>${vehicle.type}</span>
                    </div>
                    <div class="vehicle-detail-item">
                        <span>司机:</span>
                        <span>${vehicle.driver}</span>
                    </div>
                    <div class="vehicle-detail-item">
                        <span>位置:</span>
                        <span>${vehicle.location}</span>
                    </div>
                    <div class="vehicle-detail-item">
                        <span>装载率:</span>
                        <span>${vehicle.load}</span>
                    </div>
                    <div class="vehicle-detail-item">
                        <span>下一站:</span>
                        <span>${vehicle.nextStop}</span>
                    </div>
                </div>
            </div>
        `).join('');

        container.innerHTML = vehicleCards;
    }

    /**
     * 过滤车辆
     */
    filterVehicles(filter) {
        // 实现车辆过滤逻辑
        console.log('过滤车辆:', filter);
    }

    /**
     * 加载效率数据
     */
    loadEfficiencyData() {
        try {
            this.updateEfficiencyOverview();
            this.createOptimizationChart();
        } catch (error) {
            console.error('加载效率数据失败:', error);
        }
    }

    /**
     * 更新效率概览
     */
    updateEfficiencyOverview() {
        const metrics = {
            overall: 82.5,
            route: 78.3,
            time: 85.7
        };

        document.getElementById('overall-efficiency').textContent = `${metrics.overall}%`;
        document.getElementById('route-efficiency').textContent = `${metrics.route}%`;
        document.getElementById('time-efficiency').textContent = `${metrics.time}%`;
    }

    /**
     * 创建优化效果对比图表
     */
    createOptimizationChart() {
        const ctx = document.getElementById('optimizationChart');
        if (!ctx) return;

        if (this.charts.optimization) {
            this.charts.optimization.destroy();
        }

        this.charts.optimization = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: ['优化前', '优化后'],
                datasets: [
                    {
                        label: '装载率 (%)',
                        data: [65, 82],
                        backgroundColor: '#3498db',
                        borderColor: '#2980b9',
                        borderWidth: 1
                    },
                    {
                        label: '成本 (¥)',
                        data: [15000, 12580],
                        backgroundColor: '#e74c3c',
                        borderColor: '#c0392b',
                        borderWidth: 1,
                        yAxisID: 'y1'
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        type: 'linear',
                        display: true,
                        position: 'left',
                        title: {
                            display: true,
                            text: '装载率 (%)'
                        }
                    },
                    y1: {
                        type: 'linear',
                        display: true,
                        position: 'right',
                        title: {
                            display: true,
                            text: '成本 (¥)'
                        },
                        grid: {
                            drawOnChartArea: false
                        }
                    }
                }
            }
        });
    }

    /**
     * 加载报告数据
     */
    loadReportsData() {
        const container = document.getElementById('reports-list-container');
        if (!container) return;

        const reports = [
            { id: 1, title: '日报 - 2024-01-15', date: '2024-01-15 09:30', type: 'daily', size: '2.3MB' },
            { id: 2, title: '周报 - 2024年第2周', date: '2024-01-15 10:15', type: 'weekly', size: '8.7MB' },
            { id: 3, title: '月报 - 2024年1月', date: '2024-01-15 11:00', type: 'monthly', size: '15.2MB' }
        ];

        const reportItems = reports.map(report => `
            <div class="report-item">
                <div class="report-info">
                    <h5>${report.title}</h5>
                    <p>生成时间: ${report.date} | 文件大小: ${report.size}</p>
                </div>
                <div class="report-actions">
                    <button class="report-action-btn view" onclick="managerDashboard.viewReport(${report.id})">
                        <i class="fas fa-eye"></i> 查看
                    </button>
                    <button class="report-action-btn download" onclick="managerDashboard.downloadReport(${report.id})">
                        <i class="fas fa-download"></i> 下载
                    </button>
                </div>
            </div>
        `).join('');

        container.innerHTML = reportItems;
    }

    /**
     * 查看报告
     */
    viewReport(reportId) {
        alert(`查看报告 ${reportId}`);
    }

    /**
     * 下载报告
     */
    downloadReport(reportId) {
        alert(`下载报告 ${reportId}`);
    }

    /**
     * 生成报告
     */
    generateReport() {
        const reportType = document.getElementById('report-type-select').value;
        const startDate = document.getElementById('start-date').value;
        const endDate = document.getElementById('end-date').value;

        if (!startDate || !endDate) {
            alert('请选择开始和结束日期');
            return;
        }

        // 模拟报告生成
        alert(`正在生成 ${reportType} 报告 (${startDate} 至 ${endDate})`);
    }
}

/**
 * 全局函数
 */
function logout() {
    if (confirm('确定要退出登录吗？')) {
        window.location.href = '/login';
    }
}

/**
 * 初始化管理层仪表板
 */
document.addEventListener('DOMContentLoaded', () => {
    window.managerDashboard = new ManagerDashboard();
});