/**
 * 客户端JavaScript功能
 * Customer Dashboard JavaScript Functions
 */

class OrderWizard {
    constructor() {
        this.currentStep = 1;
        this.orderData = {};
        this.init();
    }

    /**
     * 初始化下单向导
     */
    init() {
        this.setupEventListeners();
        this.setupFormValidation();
    }

    /**
     * 设置事件监听器
     */
    setupEventListeners() {
        // 时间类型选择
        document.querySelectorAll('input[name="timeType"]').forEach(radio => {
            radio.addEventListener('change', (e) => {
                this.handleTimeTypeChange(e.target.value);
            });
        });

        // 货物信息表单验证
        const cargoForm = document.getElementById('cargo-form');
        if (cargoForm) {
            cargoForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.saveStepData();
                if (this.validateStep(1)) {
                    this.nextStep();
                }
            });
        }

        // 实时计算费用
        document.getElementById('cargo-weight')?.addEventListener('input', () => {
            this.calculateCost();
        });

        document.getElementById('receiver-address')?.addEventListener('input', () => {
            this.calculateCost();
        });
    }

    /**
     * 设置表单验证
     */
    setupFormValidation() {
        // 添加输入验证
        const inputs = document.querySelectorAll('input[required], select[required]');
        inputs.forEach(input => {
            input.addEventListener('blur', () => {
                this.validateField(input);
            });
        });
    }

    /**
     * 处理时间类型变化
     */
    handleTimeTypeChange(timeType) {
        const scheduledTimeGroup = document.getElementById('scheduled-time');
        if (timeType === 'scheduled') {
            scheduledTimeGroup.style.display = 'block';
            // 设置最小日期为明天
            const tomorrow = new Date();
            tomorrow.setDate(tomorrow.getDate() + 1);
            document.getElementById('delivery-date').min = tomorrow.toISOString().split('T')[0];
        } else {
            scheduledTimeGroup.style.display = 'none';
        }
        this.updateDeliveryEstimate();
        this.calculateCost();
    }

    /**
     * 更新配送时间预估
     */
    updateDeliveryEstimate() {
        const timeType = document.querySelector('input[name="timeType"]:checked')?.value;
        const estimateElement = document.getElementById('estimated-delivery-time');

        if (!estimateElement) return;

        const now = new Date();
        let estimateText = '';

        switch (timeType) {
            case 'normal':
                const normalDate = new Date(now.getTime() + (2 * 24 * 60 * 60 * 1000));
                estimateText = `${normalDate.getMonth() + 1}月${normalDate.getDate()}日 送达`;
                break;
            case 'express':
                const expressDate = new Date(now.getTime() + (24 * 60 * 60 * 1000));
                estimateText = `明日 ${expressDate.getHours()}:00 前送达`;
                break;
            case 'scheduled':
                const deliveryDate = document.getElementById('delivery-date')?.value;
                const deliveryTime = document.getElementById('delivery-time')?.value;
                if (deliveryDate && deliveryTime) {
                    const timeMap = {
                        'morning': '上午',
                        'afternoon': '下午',
                        'evening': '晚上'
                    };
                    estimateText = `${deliveryDate} ${timeMap[deliveryTime]} 送达`;
                } else {
                    estimateText = '请选择配送日期和时段';
                }
                break;
            default:
                estimateText = '请选择配送时间类型';
        }

        estimateElement.textContent = estimateText;
    }

    /**
     * 保存当前步骤数据
     */
    saveStepData() {
        switch (this.currentStep) {
            case 1:
                const cargoForm = document.getElementById('cargo-form');
                const formData = new FormData(cargoForm);
                this.orderData.cargo = Object.fromEntries(formData);
                break;
            case 2:
                const deliveryForm = document.getElementById('delivery-form');
                const deliveryData = new FormData(deliveryForm);
                this.orderData.delivery = Object.fromEntries(deliveryData);
                break;
            case 3:
                const timeForm = document.getElementById('time-form');
                const timeData = new FormData(timeForm);
                this.orderData.time = Object.fromEntries(timeData);
                this.updateDeliveryEstimate();
                break;
        }
    }

    /**
     * 验证当前步骤
     */
    validateStep(step) {
        let isValid = true;
        let form;

        switch (step) {
            case 1:
                form = document.getElementById('cargo-form');
                break;
            case 2:
                form = document.getElementById('delivery-form');
                break;
            case 3:
                form = document.getElementById('time-form');
                break;
        }

        if (!form) return true;

        const requiredFields = form.querySelectorAll('[required]');
        requiredFields.forEach(field => {
            if (!this.validateField(field)) {
                isValid = false;
            }
        });

        return isValid;
    }

    /**
     * 验证单个字段
     */
    validateField(field) {
        const value = field.value.trim();

        if (field.hasAttribute('required') && !value) {
            this.showFieldError(field, '此字段为必填项');
            return false;
        }

        if (field.type === 'tel') {
            const phoneRegex = /^1[3-9]\d{9}$/;
            if (value && !phoneRegex.test(value)) {
                this.showFieldError(field, '请输入有效的手机号码');
                return false;
            }
        }

        if (field.type === 'number') {
            const num = parseFloat(value);
            const min = parseFloat(field.min);
            if (min && num < min) {
                this.showFieldError(field, `数值不能小于 ${min}`);
                return false;
            }
        }

        this.clearFieldError(field);
        return true;
    }

    /**
     * 显示字段错误
     */
    showFieldError(field, message) {
        this.clearFieldError(field);
        field.style.borderColor = '#e74c3c';

        const errorElement = document.createElement('div');
        errorElement.className = 'field-error';
        errorElement.textContent = message;
        errorElement.style.color = '#e74c3c';
        errorElement.style.fontSize = '0.875rem';
        errorElement.style.marginTop = '0.25rem';

        field.parentNode.appendChild(errorElement);
    }

    /**
     * 清除字段错误
     */
    clearFieldError(field) {
        field.style.borderColor = '';
        const errorElement = field.parentNode.querySelector('.field-error');
        if (errorElement) {
            errorElement.remove();
        }
    }

    /**
     * 下一步
     */
    nextStep() {
        if (this.currentStep < 4) {
            this.saveStepData();

            if (!this.validateStep(this.currentStep)) {
                return;
            }

            // 标记当前步骤为完成
            document.querySelector(`.step[data-step="${this.currentStep}"]`).classList.add('completed');

            this.currentStep++;
            this.showStep(this.currentStep);

            if (this.currentStep === 4) {
                this.showOrderSummary();
            }
        }
    }

    /**
     * 上一步
     */
    prevStep() {
        if (this.currentStep > 1) {
            // 移除后续步骤的完成状态
            for (let i = this.currentStep; i <= 4; i++) {
                document.querySelector(`.step[data-step="${i}"]`).classList.remove('completed');
            }

            this.currentStep--;
            this.showStep(this.currentStep);
        }
    }

    /**
     * 显示指定步骤
     */
    showStep(step) {
        // 更新步骤指示器
        document.querySelectorAll('.step').forEach(s => s.classList.remove('active'));
        document.querySelector(`.step[data-step="${step}"]`).classList.add('active');

        // 更新内容区域
        document.querySelectorAll('.wizard-step').forEach(s => s.classList.remove('active'));
        document.querySelector(`.wizard-step[data-step="${step}"]`).classList.add('active');

        // 滚动到顶部
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }

    /**
     * 显示订单摘要
     */
    showOrderSummary() {
        // 填充货物信息摘要
        const cargoSummary = document.getElementById('summary-cargo');
        if (cargoSummary && this.orderData.cargo) {
            cargoSummary.innerHTML = `
                <div class="summary-item">
                    <span>货物名称:</span>
                    <span>${this.orderData.cargo.cargoName}</span>
                </div>
                <div class="summary-item">
                    <span>货物类型:</span>
                    <span>${this.orderData.cargo.cargoType}</span>
                </div>
                <div class="summary-item">
                    <span>数量:</span>
                    <span>${this.orderData.cargo.quantity} 件</span>
                </div>
                <div class="summary-item">
                    <span>重量:</span>
                    <span>${this.orderData.cargo.weight} kg</span>
                </div>
                ${this.orderData.cargo.length ? `
                <div class="summary-item">
                    <span>尺寸:</span>
                    <span>${this.orderData.cargo.length}×${this.orderData.cargo.width}×${this.orderData.cargo.height} m</span>
                </div>` : ''}
                ${this.orderData.cargo.description ? `
                <div class="summary-item">
                    <span>描述:</span>
                    <span>${this.orderData.cargo.description}</span>
                </div>` : ''}
            `;
        }

        // 填充配送信息摘要
        const deliverySummary = document.getElementById('summary-delivery');
        if (deliverySummary && this.orderData.delivery) {
            deliverySummary.innerHTML = `
                <div class="summary-item">
                    <span>发件人:</span>
                    <span>${this.orderData.delivery.senderName} (${this.orderData.delivery.senderPhone})</span>
                </div>
                <div class="summary-item">
                    <span>发件地址:</span>
                    <span>${this.orderData.delivery.senderAddress}</span>
                </div>
                <div class="summary-item">
                    <span>收件人:</span>
                    <span>${this.orderData.delivery.receiverName} (${this.orderData.delivery.receiverPhone})</span>
                </div>
                <div class="summary-item">
                    <span>收件地址:</span>
                    <span>${this.orderData.delivery.receiverAddress}</span>
                </div>
            `;
        }

        // 计算并显示费用
        this.calculateCost();
    }

    /**
     * 计算费用
     */
    calculateCost() {
        const weight = parseFloat(this.orderData.cargo?.weight || 0);
        const timeType = this.orderData.time?.timeType || 'normal';

        // 模拟费用计算
        let baseCost = 20; // 基础运费
        let weightCost = Math.max(0, (weight - 5)) * 2; // 超过5kg的部分，每kg加2元
        let distanceCost = 15; // 模拟距离费用
        let expressCost = timeType === 'express' ? 25 : 0; // 加急费用

        const totalCost = baseCost + weightCost + distanceCost + expressCost;

        // 更新费用显示
        document.getElementById('base-cost').textContent = `¥${baseCost}`;
        document.getElementById('weight-cost').textContent = `¥${weightCost}`;
        document.getElementById('distance-cost').textContent = `¥${distanceCost}`;

        const expressCostElement = document.getElementById('express-cost');
        if (expressCostElement) {
            expressCostElement.textContent = `¥${expressCost}`;
            expressCostElement.parentNode.style.display = expressCost > 0 ? 'flex' : 'none';
        }

        document.getElementById('total-cost').textContent = `¥${totalCost}`;

        // 保存费用信息
        this.orderData.cost = {
            base: baseCost,
            weight: weightCost,
            distance: distanceCost,
            express: expressCost,
            total: totalCost
        };
    }

    /**
     * 提交订单
     */
    async submitOrder() {
        try {
            // 显示加载状态
            const submitBtn = document.querySelector('.btn-submit');
            const originalText = submitBtn.innerHTML;
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 提交中...';
            submitBtn.disabled = true;

            // 生成订单号
            const orderNumber = this.generateOrderNumber();

            // 模拟API调用
            await this.simulateApiCall();

            // 显示成功模态框
            this.showSuccessModal(orderNumber);

        } catch (error) {
            console.error('提交订单失败:', error);
            alert('提交订单失败，请重试');
        } finally {
            // 恢复按钮状态
            const submitBtn = document.querySelector('.btn-submit');
            submitBtn.innerHTML = '<i class="fas fa-check"></i> 确认下单';
            submitBtn.disabled = false;
        }
    }

    /**
     * 生成订单号
     */
    generateOrderNumber() {
        const now = new Date();
        const dateStr = now.getFullYear().toString() +
                       (now.getMonth() + 1).toString().padStart(2, '0') +
                       now.getDate().toString().padStart(2, '0');
        const randomStr = Math.random().toString(36).substr(2, 6).toUpperCase();
        return `ORD${dateStr}${randomStr}`;
    }

    /**
     * 模拟API调用
     */
    simulateApiCall() {
        return new Promise(resolve => setTimeout(resolve, 1500));
    }

    /**
     * 显示成功模态框
     */
    showSuccessModal(orderNumber) {
        document.getElementById('new-order-number').textContent = orderNumber;
        document.getElementById('success-modal').style.display = 'flex';
    }

    /**
     * 重置向导
     */
    reset() {
        this.currentStep = 1;
        this.orderData = {};

        // 重置步骤指示器
        document.querySelectorAll('.step').forEach(s => {
            s.classList.remove('active', 'completed');
        });
        document.querySelector('.step[data-step="1"]').classList.add('active');

        // 重置表单
        document.querySelectorAll('.order-form').forEach(form => {
            form.reset();
        });

        // 显示第一步
        this.showStep(1);

        // 重置时间选择
        document.getElementById('scheduled-time').style.display = 'none';
    }
}

class OrderTracking {
    constructor() {
        this.init();
    }

    init() {
        // 初始化追踪功能
    }

    search() {
        const searchValue = document.getElementById('order-number-input').value.trim();

        if (!searchValue) {
            alert('请输入订单号或手机号');
            return;
        }

        // 模拟搜索
        this.showTrackingResult(searchValue);
    }

    showTrackingResult(searchValue) {
        const resultContainer = document.getElementById('tracking-result');

        // 模拟追踪数据
        const trackingData = {
            orderNumber: 'ORD20240115ABC123',
            status: 'processing',
            currentLocation: '成都市高新区',
            estimatedDelivery: '2024-01-16 14:00',
            timeline: [
                { time: '2024-01-15 09:30', status: '订单已创建', location: '系统' },
                { time: '2024-01-15 10:15', status: '已揽收', location: '成都市武侯区' },
                { time: '2024-01-15 11:30', status: '运输中', location: '成都市高新区' },
                { time: '预计 2024-01-16 14:00', status: '派送中', location: '目的地' }
            ]
        };

        const resultHTML = `
            <div class="tracking-card">
                <div class="tracking-header">
                    <h3>订单追踪</h3>
                    <div class="order-status-badge processing">配送中</div>
                </div>

                <div class="tracking-info">
                    <div class="info-item">
                        <span>订单号:</span>
                        <strong>${trackingData.orderNumber}</strong>
                    </div>
                    <div class="info-item">
                        <span>当前位置:</span>
                        <strong>${trackingData.currentLocation}</strong>
                    </div>
                    <div class="info-item">
                        <span>预计送达:</span>
                        <strong>${trackingData.estimatedDelivery}</strong>
                    </div>
                </div>

                <div class="tracking-timeline">
                    <h4>物流轨迹</h4>
                    ${trackingData.timeline.map((item, index) => `
                        <div class="timeline-item ${index === trackingData.timeline.length - 1 ? 'current' : ''}">
                            <div class="timeline-dot ${index < trackingData.timeline.length - 1 ? 'completed' : ''}"></div>
                            <div class="timeline-content">
                                <div class="timeline-time">${item.time}</div>
                                <div class="timeline-status">${item.status}</div>
                                <div class="timeline-location">${item.location}</div>
                            </div>
                        </div>
                    `).join('')}
                </div>

                <div class="tracking-actions">
                    <button class="action-btn" onclick="orderTracking.refreshTracking()">
                        <i class="fas fa-sync-alt"></i> 刷新
                    </button>
                    <button class="action-btn" onclick="orderTracking.contactDriver()">
                        <i class="fas fa-phone"></i> 联系司机
                    </button>
                </div>
            </div>
        `;

        resultContainer.innerHTML = resultHTML;
        resultContainer.style.display = 'block';
    }

    refreshTracking() {
        this.search();
    }

    contactDriver() {
        alert('正在为您联系司机...');
    }

    viewOrder(orderNumber) {
        // 切换到追踪页面并查看订单
        document.querySelector('[href="#tracking"]').click();
        setTimeout(() => {
            document.getElementById('order-number-input').value = orderNumber;
            this.search();
        }, 100);
    }
}

class OrderHistory {
    constructor() {
        this.orders = [];
        this.init();
    }

    init() {
        this.loadOrders();
    }

    loadOrders() {
        // 模拟历史订单数据
        this.orders = [
            {
                id: 'ORD20240115ABC123',
                date: '2024-01-15',
                status: 'processing',
                cargo: '食品',
                amount: 125.50,
                from: '成都市武侯区',
                to: '成都市高新区'
            },
            {
                id: 'ORD20240114DEF456',
                date: '2024-01-14',
                status: 'completed',
                cargo: '日用品',
                amount: 89.00,
                from: '成都市锦江区',
                to: '成都市成华区'
            },
            {
                id: 'ORD20240113GHI789',
                date: '2024-01-13',
                status: 'completed',
                cargo: '建材',
                amount: 256.80,
                from: '成都市青羊区',
                to: '成都市金牛区'
            }
        ];

        this.renderOrders();
    }

    renderOrders() {
        const container = document.getElementById('order-list');
        if (!container) return;

        const orderHTML = this.orders.map(order => `
            <div class="order-card">
                <div class="order-header">
                    <div class="order-number">${order.id}</div>
                    <div class="order-status ${order.status}">${this.getStatusText(order.status)}</div>
                </div>

                <div class="order-details">
                    <div class="detail-item">
                        <span>下单日期:</span>
                        <span>${order.date}</span>
                    </div>
                    <div class="detail-item">
                        <span>货物类型:</span>
                        <span>${order.cargo}</span>
                    </div>
                    <div class="detail-item">
                        <span>配送路线:</span>
                        <span>${order.from} → ${order.to}</span>
                    </div>
                    <div class="detail-item">
                        <span>订单金额:</span>
                        <strong>¥${order.amount}</strong>
                    </div>
                </div>

                <div class="order-actions-card">
                    ${order.status === 'processing' ?
                        `<button class="action-btn track" onclick="orderTracking.viewOrder('${order.id}')">
                            <i class="fas fa-map-marker-alt"></i> 追踪
                        </button>` : ''
                    }
                    <button class="action-btn view" onclick="orderHistory.viewOrderDetails('${order.id}')">
                        <i class="fas fa-eye"></i> 查看
                    </button>
                </div>
            </div>
        `).join('');

        container.innerHTML = orderHTML;
    }

    getStatusText(status) {
        const statusMap = {
            'pending': '待处理',
            'processing': '配送中',
            'completed': '已完成',
            'cancelled': '已取消'
        };
        return statusMap[status] || status;
    }

    filter() {
        const statusFilter = document.getElementById('status-filter').value;
        const timeFilter = document.getElementById('time-filter').value;

        let filteredOrders = [...this.orders];

        // 状态过滤
        if (statusFilter !== 'all') {
            filteredOrders = filteredOrders.filter(order => order.status === statusFilter);
        }

        // 时间过滤
        if (timeFilter !== 'all') {
            const days = parseInt(timeFilter);
            const cutoffDate = new Date();
            cutoffDate.setDate(cutoffDate.getDate() - days);

            filteredOrders = filteredOrders.filter(order => {
                const orderDate = new Date(order.date);
                return orderDate >= cutoffDate;
            });
        }

        // 临时替换订单列表并重新渲染
        const originalOrders = this.orders;
        this.orders = filteredOrders;
        this.renderOrders();
        this.orders = originalOrders;
    }

    viewOrderDetails(orderId) {
        alert(`查看订单 ${orderId} 的详细信息`);
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

function closeModal(modalId) {
    document.getElementById(modalId).style.display = 'none';
}

/**
 * 初始化客户端功能
 */
document.addEventListener('DOMContentLoaded', () => {
    window.orderWizard = new OrderWizard();
    window.orderTracking = new OrderTracking();
    window.orderHistory = new OrderHistory();

    // 设置页面导航
    document.querySelectorAll('.nav-link').forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const sectionId = link.getAttribute('href').substring(1);

            // 更新导航状态
            document.querySelectorAll('.nav-link').forEach(l => l.classList.remove('active'));
            link.classList.add('active');

            // 切换内容区域
            document.querySelectorAll('.section').forEach(section => {
                section.classList.remove('active');
            });
            document.getElementById(sectionId).classList.add('active');
        });
    });

    // 加载客户数据
    loadCustomerData();
});

/**
 * 加载客户数据
 */
function loadCustomerData() {
    // 模拟客户数据
    const customerData = {
        name: '张三',
        phone: '138****8888'
    };

    // 更新页面显示
    document.getElementById('customer-name').textContent = customerData.name;
    document.getElementById('customer-name-profile').textContent = customerData.name;
    document.getElementById('customer-phone').textContent = `手机号: ${customerData.phone}`;
}