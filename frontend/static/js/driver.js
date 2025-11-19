/**
 * 司机端JavaScript功能
 * Driver Dashboard JavaScript Functions
 */

class DriverDashboard {
    constructor() {
        this.currentSection = 'dashboard';
        this.vehicleId = 'LARGE_TRUCK_000'; // 默认车辆ID
        this.loadingData = null;
        this.routeData = null;
        this.scheduleData = null;

        this.init();
    }

    /**
     * 初始化司机端仪表板
     */
    init() {
        this.setupEventListeners();
        this.loadDriverData();
        this.loadScheduleData();
        this.switchSection('dashboard');
    }

    /**
     * 设置事件监听器
     */
    setupEventListeners() {
        // 导航菜单点击事件
        document.querySelectorAll('.nav-link').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const sectionId = link.getAttribute('href').substring(1);
                this.switchSection(sectionId);
            });
        });

        // 3D视图控制
        document.getElementById('view-3d-btn')?.addEventListener('click', () => {
            this.showVisualization3D();
        });

        document.getElementById('view-list-btn')?.addEventListener('click', () => {
            this.showVisualizationList();
        });

        document.getElementById('fullscreen-btn')?.addEventListener('click', () => {
            this.toggleFullscreen('loading-visualization');
        });

        // 地图控制
        document.getElementById('refresh-map-btn')?.addEventListener('click', () => {
            this.refreshRouteMap();
        });

        document.getElementById('fullscreen-map-btn')?.addEventListener('click', () => {
            this.toggleFullscreen('route-map-container');
        });

        // 货物搜索和过滤
        document.getElementById('cargo-search')?.addEventListener('input', (e) => {
            this.filterCargoList(e.target.value);
        });

        document.getElementById('cargo-filter')?.addEventListener('change', (e) => {
            this.filterCargoListByType(e.target.value);
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
            case 'loading':
                this.loadLoadingData();
                break;
            case 'route':
                this.loadRouteData();
                break;
        }
    }

    /**
     * 加载司机数据
     */
    async loadDriverData() {
        try {
            // 模拟司机数据
            const driverData = {
                name: '张师傅',
                id: 'D001',
                vehicleId: this.vehicleId,
                status: 'active'
            };

            // 更新页面显示
            document.getElementById('driver-name').textContent = driverData.name;
            document.getElementById('driver-name-profile').textContent = driverData.name;
            document.getElementById('driver-id').textContent = `工号: ${driverData.id}`;
            document.getElementById('vehicle-id').textContent = driverData.vehicleId;

        } catch (error) {
            console.error('加载司机数据失败:', error);
        }
    }

    /**
     * 加载日程数据
     */
    async loadScheduleData() {
        const container = document.getElementById('timeline-container');

        try {
            this.showLoading(container);

            // 模拟日程数据
            const scheduleData = [
                {
                    time: '08:00',
                    title: '签到出车',
                    description: '在配送中心签到，领取车辆钥匙',
                    type: 'checkin'
                },
                {
                    time: '08:30',
                    title: '装货检查',
                    description: '检查装载货物清单，确认装载方案',
                    type: 'loading'
                },
                {
                    time: '09:00',
                    title: '开始配送',
                    description: '离开配送中心，开始第一单配送',
                    type: 'departure'
                },
                {
                    time: '12:00',
                    title: '午餐休息',
                    description: '在服务区休息用餐',
                    type: 'break'
                },
                {
                    time: '14:30',
                    title: '配送完成',
                    description: '完成所有配送任务，准备返程',
                    type: 'complete'
                },
                {
                    time: '16:00',
                    title: '返回签退',
                    description: '返回配送中心，归还车辆钥匙',
                    type: 'checkout'
                }
            ];

            this.scheduleData = scheduleData;
            this.renderScheduleTimeline(scheduleData);

        } catch (error) {
            console.error('加载日程数据失败:', error);
            this.showError(container, '加载日程数据失败');
        }
    }

    /**
     * 渲染日程时间线
     */
    renderScheduleTimeline(scheduleData) {
        const container = document.getElementById('timeline-container');

        const timelineHTML = scheduleData.map((item, index) => `
            <div class="timeline-item">
                <div class="timeline-time">${item.time}</div>
                <div class="timeline-content">
                    <h4>${item.title}</h4>
                    <p>${item.description}</p>
                </div>
            </div>
        `).join('');

        container.innerHTML = timelineHTML;
    }

    /**
     * 加载装载数据
     */
    async loadLoadingData() {
        try {
            // 模拟装载数据
            const loadingData = {
                vehicleId: this.vehicleId,
                totalItems: 45,
                totalWeight: 1250,
                loadingEfficiency: 78.5,
                volumeUtilization: 82.3,
                cargoTypes: ['食品', '日用品', '建材'],
                cargoList: [
                    { id: 'C001', name: '食品箱A', type: 'small', weight: 15, volume: 0.03 },
                    { id: 'C002', name: '日用品B', type: 'medium', weight: 25, volume: 0.08 },
                    { id: 'C003', name: '建材C', type: 'large', weight: 80, volume: 0.25 },
                    { id: 'C004', name: '食品箱D', type: 'small', weight: 12, volume: 0.025 },
                    { id: 'C005', name: '日用品E', type: 'medium', weight: 30, volume: 0.09 }
                ]
            };

            this.loadingData = loadingData;
            this.updateLoadingStats(loadingData);
            this.renderCargoList(loadingData.cargoList);

        } catch (error) {
            console.error('加载装载数据失败:', error);
        }
    }

    /**
     * 更新装载统计信息
     */
    updateLoadingStats(loadingData) {
        document.getElementById('total-items').textContent = loadingData.totalItems;
        document.getElementById('total-weight').textContent = loadingData.totalWeight;
        document.getElementById('loading-efficiency').textContent = loadingData.loadingEfficiency.toFixed(1);
        document.getElementById('volume-utilization').textContent = loadingData.volumeUtilization.toFixed(1);
        document.getElementById('cargo-types').textContent = loadingData.cargoTypes.length;
    }

    /**
     * 渲染货物清单
     */
    renderCargoList(cargoList) {
        const container = document.getElementById('cargo-list-container');

        const cargoHTML = cargoList.map(cargo => `
            <div class="cargo-item" data-type="${cargo.type}">
                <div class="cargo-info">
                    <h5>${cargo.name}</h5>
                    <p>ID: ${cargo.id} | 重量: ${cargo.weight}kg | 体积: ${cargo.volume}m³</p>
                </div>
                <div class="cargo-meta">
                    <div class="cargo-type ${cargo.type}">${this.getCargoTypeLabel(cargo.type)}</div>
                </div>
            </div>
        `).join('');

        container.innerHTML = cargoHTML;
    }

    /**
     * 获取货物类型标签
     */
    getCargoTypeLabel(type) {
        const labels = {
            'large': '大货物',
            'medium': '中货物',
            'small': '小货物'
        };
        return labels[type] || '未知';
    }

    /**
     * 显示3D可视化
     */
    showVisualization3D() {
        document.getElementById('view-3d-btn').classList.add('active');
        document.getElementById('view-list-btn').classList.remove('active');

        const container = document.getElementById('loading-visualization');
        container.innerHTML = `
            <iframe
                src="/visualizations/single_category_3dpp_${this.vehicleId}.html"
                width="100%"
                height="100%"
                frameborder="0"
                style="border-radius: 10px;">
            </iframe>
        `;
    }

    /**
     * 显示列表视图
     */
    showVisualizationList() {
        document.getElementById('view-list-btn').classList.add('active');
        document.getElementById('view-3d-btn').classList.remove('active');

        const container = document.getElementById('loading-visualization');
        if (this.loadingData) {
            container.innerHTML = `
                <div style="padding: 2rem;">
                    <h3>装载详情清单</h3>
                    <p>车辆: ${this.loadingData.vehicleId}</p>
                    <p>总货物数: ${this.loadingData.totalItems} 件</p>
                    <p>总重量: ${this.loadingData.totalWeight} kg</p>
                    <p>装载率: ${this.loadingData.loadingEfficiency}%</p>
                    <hr>
                    ${this.loadingData.cargoList.map(cargo => `
                        <div style="margin: 1rem 0; padding: 1rem; background: #f8f9fa; border-radius: 5px;">
                            <strong>${cargo.name}</strong><br>
                            类型: ${this.getCargoTypeLabel(cargo.type)}<br>
                            重量: ${cargo.weight}kg, 体积: ${cargo.volume}m³
                        </div>
                    `).join('')}
                </div>
            `;
        }
    }

    /**
     * 加载路径数据
     */
    async loadRouteData() {
        try {
            // 模拟路径数据
            const routeData = {
                vehicleId: this.vehicleId,
                totalStops: 8,
                totalDistance: 45.6,
                fuelCost: 180,
                estimatedDuration: 6.5,
                stops: [
                    {
                        number: 1,
                        type: 'depot',
                        name: '配送中心',
                        address: '成都市锦江区配送中心',
                        arrivalTime: '09:00',
                        action: '出发'
                    },
                    {
                        number: 2,
                        type: 'pickup',
                        name: '客户A',
                        address: '成都市武侯区天府大道100号',
                        arrivalTime: '09:30',
                        action: '送货',
                        cargo: '食品箱A'
                    },
                    {
                        number: 3,
                        type: 'delivery',
                        name: '客户B',
                        address: '成都市高新区天府大道200号',
                        arrivalTime: '10:15',
                        action: '送货',
                        cargo: '日用品B'
                    }
                ]
            };

            this.routeData = routeData;
            this.updateRouteStats(routeData);
            this.renderRouteMap();
            this.renderStopsList(routeData.stops);

        } catch (error) {
            console.error('加载路径数据失败:', error);
        }
    }

    /**
     * 更新路径统计信息
     */
    updateRouteStats(routeData) {
        document.getElementById('total-stops').textContent = routeData.totalStops;
        document.getElementById('route-distance').textContent = `${routeData.totalDistance} km`;
        document.getElementById('fuel-cost').textContent = `¥${routeData.fuelCost}`;
        document.getElementById('total-distance').textContent = `${routeData.totalDistance} km`;
        document.getElementById('estimated-duration').textContent = `${routeData.estimatedDuration} 小时`;
    }

    /**
     * 渲染路径地图
     */
    renderRouteMap() {
        const container = document.getElementById('route-map-container');

        // 使用固定的成都路径地图文件
        // 注意：从A:\ 转换为可在Web服务器访问的路径
        // 这里使用相对路径，通过FastAPI的static file serving提供访问

        container.innerHTML = `
            <iframe
                src="/chengdu_route_map"
                width="100%"
                height="100%"
                frameborder="0"
                style="border-radius: 10px;">
            </iframe>
        `;

        // 添加地图加载完成的回调
        const iframe = container.querySelector('iframe');
        if (iframe) {
            iframe.onload = () => {
                console.log('路径地图加载完成');
                // 可以在这里添加与iframe通信的代码，比如高亮当前车辆
            };
        }
    }

    /**
     * 渲染停靠点列表
     */
    renderStopsList(stops) {
        const container = document.getElementById('stops-list-container');

        const stopsHTML = stops.map(stop => `
            <div class="stop-item">
                <div class="stop-number">${stop.number}</div>
                <div class="stop-details">
                    <h5>${stop.name}</h5>
                    <p>${stop.address}</p>
                    <p><strong>时间:</strong> ${stop.arrivalTime} | <strong>操作:</strong> ${stop.action}</p>
                    ${stop.cargo ? `<p><strong>货物:</strong> ${stop.cargo}</p>` : ''}
                </div>
            </div>
        `).join('');

        container.innerHTML = stopsHTML;
    }

    /**
     * 刷新路径地图
     */
    refreshRouteMap() {
        const container = document.getElementById('route-map-container');
        container.innerHTML = '<div class="map-placeholder"><i class="fas fa-sync-alt fa-spin"></i><p>刷新地图中...</p></div>';

        setTimeout(() => {
            this.renderRouteMap();
        }, 1000);
    }

    /**
     * 过滤货物列表
     */
    filterCargoList(searchTerm) {
        const items = document.querySelectorAll('.cargo-item');
        items.forEach(item => {
            const text = item.textContent.toLowerCase();
            if (text.includes(searchTerm.toLowerCase())) {
                item.style.display = 'flex';
            } else {
                item.style.display = 'none';
            }
        });
    }

    /**
     * 按类型过滤货物列表
     */
    filterCargoListByType(type) {
        const items = document.querySelectorAll('.cargo-item');
        items.forEach(item => {
            if (type === 'all' || item.dataset.type === type) {
                item.style.display = 'flex';
            } else {
                item.style.display = 'none';
            }
        });
    }

    /**
     * 切换全屏
     */
    toggleFullscreen(elementId) {
        const element = document.getElementById(elementId);
        if (!document.fullscreenElement) {
            element.requestFullscreen().catch(err => {
                console.error('无法进入全屏模式:', err);
            });
        } else {
            document.exitFullscreen();
        }
    }

    /**
     * 显示加载状态
     */
    showLoading(container) {
        container.innerHTML = `
            <div class="loading-placeholder">
                <i class="fas fa-spinner fa-spin"></i>
                <p>加载数据中...</p>
            </div>
        `;
    }

    /**
     * 显示错误信息
     */
    showError(container, message) {
        container.innerHTML = `
            <div class="loading-placeholder">
                <i class="fas fa-exclamation-triangle" style="color: #e74c3c;"></i>
                <p style="color: #e74c3c;">${message}</p>
                <button onclick="location.reload()" class="view-btn" style="margin-top: 1rem;">
                    <i class="fas fa-redo"></i> 重新加载
                </button>
            </div>
        `;
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

function closeModal() {
    document.getElementById('modal').style.display = 'none';
}

/**
 * 初始化司机端仪表板
 */
document.addEventListener('DOMContentLoaded', () => {
    window.driverDashboard = new DriverDashboard();
});