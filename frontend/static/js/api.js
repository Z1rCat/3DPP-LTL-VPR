/**
 * API接口封装类
 * API Interface Wrapper Class
 */

class LogisticsAPI {
    constructor(baseURL = '/api') {
        this.baseURL = baseURL;
    }

    /**
     * 发送HTTP请求的通用方法
     */
    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;

        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
            },
        };

        const mergedOptions = { ...defaultOptions, ...options };

        if (mergedOptions.body && typeof mergedOptions.body === 'object') {
            mergedOptions.body = JSON.stringify(mergedOptions.body);
        }

        try {
            const response = await fetch(url, mergedOptions);
            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.message || `HTTP error! status: ${response.status}`);
            }

            return data;
        } catch (error) {
            console.error(`API请求失败: ${endpoint}`, error);
            throw error;
        }
    }

    /**
     * GET请求方法
     */
    async get(endpoint, params = {}) {
        const queryString = new URLSearchParams(params).toString();
        const url = queryString ? `${endpoint}?${queryString}` : endpoint;

        return this.request(url, {
            method: 'GET',
        });
    }

    /**
     * POST请求方法
     */
    async post(endpoint, data = {}) {
        return this.request(endpoint, {
            method: 'POST',
            body: data,
        });
    }

    /**
     * DELETE请求方法
     */
    async delete(endpoint) {
        return this.request(endpoint, {
            method: 'DELETE',
        });
    }

    // ===== 可视化相关接口 =====

    /**
     * 获取可视化文件列表
     */
    async getVisualizations(params = {}) {
        return this.get('/visualizations/list', params);
    }

    /**
     * 获取可视化类型列表
     */
    async getVisualizationTypes() {
        return this.get('/visualizations/types');
    }

    /**
     * 获取可视化统计信息
     */
    async getVisualizationStats() {
        return this.get('/visualizations/stats');
    }

    /**
     * 生成新的可视化
     */
    async generateVisualization(request) {
        return this.post('/visualizations/generate', request);
    }

    // ===== 数据相关接口 =====

    /**
     * 获取卡车数据
     */
    async getTrucks(params = {}) {
        return this.get('/data/trucks', params);
    }

    /**
     * 获取路径数据
     */
    async getRoutes(params = {}) {
        return this.get('/data/routes', params);
    }

    /**
     * 获取特定卡车详细信息
     */
    async getTruckDetail(vehicleId) {
        return this.get(`/data/trucks/${vehicleId}`);
    }

    /**
     * 获取数据摘要统计
     */
    async getDataSummary() {
        return this.get('/data/summary');
    }

    // ===== 优化相关接口 =====

    /**
     * 运行优化任务
     */
    async runOptimization(request) {
        return this.post('/optimization/run', request);
    }

    /**
     * 获取优化任务状态
     */
    async getOptimizationStatus(taskId) {
        return this.get(`/optimization/status/${taskId}`);
    }

    /**
     * 获取优化任务结果
     */
    async getOptimizationResult(taskId) {
        return this.get(`/optimization/result/${taskId}`);
    }

    /**
     * 获取优化任务历史
     */
    async getOptimizationHistory(params = {}) {
        return this.get('/optimization/history', params);
    }

    /**
     * 删除优化任务
     */
    async deleteOptimizationTask(taskId) {
        return this.delete(`/optimization/task/${taskId}`);
    }

    /**
     * 获取可用算法列表
     */
    async getAvailableAlgorithms() {
        return this.get('/optimization/algorithms');
    }

    // ===== 系统相关接口 =====

    /**
     * 健康检查
     */
    async healthCheck() {
        try {
            const response = await fetch('/health');
            return await response.json();
        } catch (error) {
            return { status: 'offline', error: error.message };
        }
    }

    // ===== 工具方法 =====

    /**
     * 轮询任务状态直到完成
     */
    async pollTaskStatus(taskId, onUpdate = null, maxAttempts = 60, interval = 5000) {
        let attempts = 0;

        while (attempts < maxAttempts) {
            try {
                const response = await this.getOptimizationStatus(taskId);

                if (onUpdate) {
                    onUpdate(response.data);
                }

                if (response.data.status === 'completed' || response.data.status === 'failed') {
                    return response.data;
                }

                await this.sleep(interval);
                attempts++;
            } catch (error) {
                console.error('轮询任务状态失败:', error);
                attempts++;
                await this.sleep(interval);
            }
        }

        throw new Error('任务状态轮询超时');
    }

    /**
     * 延时函数
     */
    sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    /**
     * 格式化文件大小
     */
    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';

        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));

        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    /**
     * 格式化日期时间
     */
    formatDateTime(dateString) {
        const date = new Date(dateString);
        return date.toLocaleString('zh-CN', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
        });
    }

    /**
     * 获取可视化类型的中文名称
     */
    getVisualizationTypeName(type) {
        const typeNames = {
            '3dpp': '3D装载可视化',
            'multi_3dpp': '多品类3D可视化',
            'heatmap': '装载密度热力图',
            'efficiency': '装载效率仪表盘',
            'route': '路径优化地图',
            '3d_analysis': '3D装载效率分析',
            'unknown': '未知类型'
        };

        return typeNames[type] || typeNames['unknown'];
    }

    /**
     * 获取任务状态的中文名称
     */
    getTaskStatusName(status) {
        const statusNames = {
            'started': '已开始',
            'running': '运行中',
            'completed': '已完成',
            'failed': '失败',
            'cancelled': '已取消'
        };

        return statusNames[status] || status;
    }

    /**
     * 获取任务状态对应的CSS类名
     */
    getTaskStatusClass(status) {
        const statusClasses = {
            'completed': 'completed',
            'running': 'running',
            'started': 'running',
            'failed': 'failed',
            'cancelled': 'failed'
        };

        return statusClasses[status] || '';
    }
}

// 创建全局API实例
window.logisticsAPI = new LogisticsAPI();