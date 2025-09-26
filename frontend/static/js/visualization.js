/**
 * 可视化管理相关功能
 * Visualization Management Functions
 */

class VisualizationManager {
    constructor() {
        this.currentFilter = 'all';
        this.visualizations = [];
        this.init();
    }

    /**
     * 初始化可视化管理器
     */
    init() {
        this.setupEventListeners();
        this.loadVisualizations();
    }

    /**
     * 设置事件监听器
     */
    setupEventListeners() {
        // 类型过滤按钮
        const filterBtns = document.querySelectorAll('.filter-btn');
        filterBtns.forEach(btn => {
            btn.addEventListener('click', (e) => {
                this.setFilter(e.target.dataset.type);
            });
        });

        // 刷新按钮
        const refreshBtn = document.querySelector('.refresh-btn');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => {
                this.refreshVisualizations();
            });
        }
    }

    /**
     * 设置过滤器
     */
    setFilter(type) {
        this.currentFilter = type;

        // 更新按钮状态
        document.querySelectorAll('.filter-btn').forEach(btn => {
            btn.classList.remove('active');
        });

        document.querySelector(`[data-type="${type}"]`).classList.add('active');

        // 过滤显示
        this.filterVisualizations();
    }

    /**
     * 加载可视化文件列表
     */
    async loadVisualizations() {
        const grid = document.getElementById('visualization-grid');

        try {
            this.showLoading(grid);

            const response = await logisticsAPI.getVisualizations({ limit: 100 });

            if (response.success) {
                this.visualizations = response.data;
                this.renderVisualizations();
            } else {
                this.showError(grid, response.message);
            }

        } catch (error) {
            console.error('加载可视化文件失败:', error);
            this.showError(grid, '加载可视化文件失败，请检查API连接');
        }
    }

    /**
     * 刷新可视化列表
     */
    async refreshVisualizations() {
        const refreshBtn = document.querySelector('.refresh-btn');
        const originalHTML = refreshBtn.innerHTML;

        try {
            refreshBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 刷新中...';
            refreshBtn.disabled = true;

            await this.loadVisualizations();

        } finally {
            refreshBtn.innerHTML = originalHTML;
            refreshBtn.disabled = false;
        }
    }

    /**
     * 过滤可视化文件
     */
    filterVisualizations() {
        let filteredViz;

        if (this.currentFilter === 'all') {
            filteredViz = this.visualizations;
        } else {
            filteredViz = this.visualizations.filter(viz => viz.type === this.currentFilter);
        }

        this.renderVisualizations(filteredViz);
    }

    /**
     * 渲染可视化文件列表
     */
    renderVisualizations(vizList = null) {
        const grid = document.getElementById('visualization-grid');
        const visualizations = vizList || this.visualizations;

        if (visualizations.length === 0) {
            grid.innerHTML = `
                <div class="loading-placeholder">
                    <i class="fas fa-image"></i>
                    <p>没有找到可视化文件</p>
                    <p style="font-size: 0.9rem; color: #6c757d;">请先运行优化任务生成可视化文件</p>
                </div>
            `;
            return;
        }

        const cards = visualizations.map(viz => this.createVisualizationCard(viz)).join('');
        grid.innerHTML = cards;
    }

    /**
     * 创建可视化文件卡片
     */
    createVisualizationCard(viz) {
        const typeName = logisticsAPI.getVisualizationTypeName(viz.type);
        const fileSize = logisticsAPI.formatFileSize(viz.size);
        const modifiedTime = logisticsAPI.formatDateTime(viz.modified_at);

        return `
            <div class="viz-card" data-type="${viz.type}">
                <div class="viz-card-header">
                    <div class="viz-card-title">${typeName}</div>
                    <div class="viz-card-meta">
                        <div>${viz.filename}</div>
                        <div>${fileSize} • ${modifiedTime}</div>
                    </div>
                </div>
                <div class="viz-card-actions">
                    <a href="/visualizations/${viz.filename}"
                       target="_blank"
                       class="action-btn primary">
                        <i class="fas fa-external-link-alt"></i> 查看
                    </a>
                    <button class="action-btn" onclick="vizManager.showDetails('${viz.filename}')">
                        <i class="fas fa-info-circle"></i> 详情
                    </button>
                    <button class="action-btn" onclick="vizManager.downloadFile('${viz.filename}')">
                        <i class="fas fa-download"></i> 下载
                    </button>
                </div>
            </div>
        `;
    }

    /**
     * 显示文件详情
     */
    showDetails(filename) {
        const viz = this.visualizations.find(v => v.filename === filename);
        if (!viz) return;

        const typeName = logisticsAPI.getVisualizationTypeName(viz.type);
        const fileSize = logisticsAPI.formatFileSize(viz.size);
        const createdTime = logisticsAPI.formatDateTime(viz.created_at);
        const modifiedTime = logisticsAPI.formatDateTime(viz.modified_at);

        // 创建模态框显示详情
        const modal = document.createElement('div');
        modal.className = 'modal';
        modal.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <h3>可视化文件详情</h3>
                    <button class="modal-close" onclick="this.closest('.modal').remove()">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                <div class="modal-body">
                    <table class="details-table">
                        <tr><td>文件名</td><td>${viz.filename}</td></tr>
                        <tr><td>类型</td><td>${typeName}</td></tr>
                        <tr><td>大小</td><td>${fileSize}</td></tr>
                        <tr><td>创建时间</td><td>${createdTime}</td></tr>
                        <tr><td>修改时间</td><td>${modifiedTime}</td></tr>
                        <tr><td>文件路径</td><td>${viz.filepath}</td></tr>
                    </table>
                </div>
                <div class="modal-footer">
                    <a href="/visualizations/${viz.filename}"
                       target="_blank"
                       class="btn btn-primary">打开文件</a>
                    <button class="btn btn-secondary" onclick="this.closest('.modal').remove()">
                        关闭
                    </button>
                </div>
            </div>
        `;

        document.body.appendChild(modal);

        // 添加模态框样式
        this.addModalStyles();

        // 点击背景关闭
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.remove();
            }
        });
    }

    /**
     * 下载文件
     */
    downloadFile(filename) {
        const link = document.createElement('a');
        link.href = `/api/visualizations/file/${filename}`;
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }

    /**
     * 显示加载状态
     */
    showLoading(container) {
        container.innerHTML = `
            <div class="loading-placeholder">
                <i class="fas fa-spinner fa-spin"></i>
                <p>加载可视化文件中...</p>
            </div>
        `;
    }

    /**
     * 显示错误信息
     */
    showError(container, message) {
        container.innerHTML = `
            <div class="loading-placeholder">
                <i class="fas fa-exclamation-triangle" style="color: #dc3545;"></i>
                <p style="color: #dc3545;">加载失败</p>
                <p style="font-size: 0.9rem; color: #6c757d;">${message}</p>
                <button class="refresh-btn" onclick="vizManager.loadVisualizations()">
                    <i class="fas fa-redo"></i> 重试
                </button>
            </div>
        `;
    }

    /**
     * 添加模态框样式
     */
    addModalStyles() {
        if (document.getElementById('modal-styles')) return;

        const style = document.createElement('style');
        style.id = 'modal-styles';
        style.textContent = `
            .modal {
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(0,0,0,0.5);
                display: flex;
                align-items: center;
                justify-content: center;
                z-index: 2000;
            }

            .modal-content {
                background: white;
                border-radius: 10px;
                max-width: 600px;
                width: 90%;
                max-height: 90%;
                overflow: auto;
            }

            .modal-header {
                padding: 1.5rem;
                border-bottom: 1px solid #e9ecef;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }

            .modal-close {
                background: none;
                border: none;
                font-size: 1.2rem;
                cursor: pointer;
                color: #6c757d;
            }

            .modal-body {
                padding: 1.5rem;
            }

            .details-table {
                width: 100%;
                border-collapse: collapse;
            }

            .details-table td {
                padding: 0.5rem 0;
                border-bottom: 1px solid #f8f9fa;
            }

            .details-table td:first-child {
                font-weight: bold;
                width: 30%;
                color: #495057;
            }

            .modal-footer {
                padding: 1.5rem;
                border-top: 1px solid #e9ecef;
                display: flex;
                gap: 1rem;
                justify-content: flex-end;
            }

            .btn {
                padding: 0.5rem 1rem;
                border-radius: 5px;
                text-decoration: none;
                cursor: pointer;
                border: none;
            }

            .btn-primary {
                background: #007bff;
                color: white;
            }

            .btn-secondary {
                background: #6c757d;
                color: white;
            }
        `;

        document.head.appendChild(style);
    }

    /**
     * 获取可视化统计信息
     */
    async getStats() {
        try {
            const response = await logisticsAPI.getVisualizationStats();
            return response.success ? response.data : null;
        } catch (error) {
            console.error('获取可视化统计失败:', error);
            return null;
        }
    }
}

// 创建全局可视化管理器实例
window.vizManager = new VisualizationManager();