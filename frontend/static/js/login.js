/**
 * 巧满装载平台 - 登录页面JavaScript
 * Login Page JavaScript
 */

class LoginManager {
    constructor() {
        this.init();
    }

    // 初始化方法
    init() {
        this.bindEvents();
        this.checkSystemStatus();
        this.loadStoredCredentials();
        this.initTheme();
    }

    // 绑定事件监听器
    bindEvents() {
        // 登录表单
        const loginForm = document.getElementById('loginForm');
        if (loginForm) {
            loginForm.addEventListener('submit', (e) => this.handleLogin(e));
        }

        // 注册表单
        const registerForm = document.getElementById('registerForm');
        if (registerForm) {
            registerForm.addEventListener('submit', (e) => this.handleRegister(e));
        }

        // 密码显示切换
        const passwordToggle = document.getElementById('passwordToggle');
        if (passwordToggle) {
            passwordToggle.addEventListener('click', () => this.togglePasswordVisibility());
        }

        // 密码强度检测
        const passwordField = document.getElementById('password');
        if (passwordField) {
            passwordField.addEventListener('input', () => this.checkPasswordStrength());
            passwordField.addEventListener('focus', () => this.showPasswordStrength());
            passwordField.addEventListener('blur', () => this.hidePasswordStrength());
        }

        // 社交登录按钮
        const wechatBtn = document.getElementById('wechatLogin');
        const dingtalkBtn = document.getElementById('dingtalkLogin');

        if (wechatBtn) {
            wechatBtn.addEventListener('click', () => this.handleSocialLogin('wechat'));
        }

        if (dingtalkBtn) {
            dingtalkBtn.addEventListener('click', () => this.handleSocialLogin('dingtalk'));
        }

        // 深色模式切换
        const themeToggle = document.getElementById('themeToggle');
        if (themeToggle) {
            themeToggle.addEventListener('click', () => this.toggleTheme());
        }

        // 显示注册模态框
        const showRegister = document.getElementById('showRegister');
        if (showRegister) {
            showRegister.addEventListener('click', (e) => {
                e.preventDefault();
                this.showRegisterModal();
            });
        }

        // 关闭注册模态框
        const closeRegisterModal = document.getElementById('closeRegisterModal');
        if (closeRegisterModal) {
            closeRegisterModal.addEventListener('click', () => this.hideRegisterModal());
        }

        // 忘记密码
        const forgotPassword = document.getElementById('forgotPassword');
        if (forgotPassword) {
            forgotPassword.addEventListener('click', (e) => {
                e.preventDefault();
                this.handleForgotPassword();
            });
        }

        // 注册表单密码确认验证
        const regPasswordConfirm = document.getElementById('regPasswordConfirm');
        if (regPasswordConfirm) {
            regPasswordConfirm.addEventListener('input', () => this.validatePasswordMatch());
        }

        // 注册表单实时验证
        const regUsername = document.getElementById('regUsername');
        const regEmail = document.getElementById('regEmail');
        const regPassword = document.getElementById('regPassword');

        if (regUsername) {
            regUsername.addEventListener('input', () => this.validateUsername());
        }

        if (regEmail) {
            regEmail.addEventListener('input', () => this.validateEmail());
        }

        if (regPassword) {
            regPassword.addEventListener('input', () => this.validatePassword());
        }

        // 模态框外部点击关闭
        const registerModal = document.getElementById('registerModal');
        if (registerModal) {
            registerModal.addEventListener('click', (e) => {
                if (e.target === registerModal) {
                    this.hideRegisterModal();
                }
            });
        }

        // 键盘事件
        document.addEventListener('keydown', (e) => this.handleKeyboardEvents(e));

        // 表单输入框焦点样式
        this.setupInputFocusEffects();
    }

    // 处理登录
    async handleLogin(e) {
        e.preventDefault();

        const formData = new FormData(e.target);
        const credentials = {
            username: formData.get('username').trim(),
            password: formData.get('password'),
            rememberMe: formData.get('rememberMe') === 'on'
        };

        // 基础验证
        if (!this.validateLoginForm(credentials)) {
            return;
        }

        this.setLoginLoading(true);

        try {
            const response = await fetch('/api/auth/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(credentials)
            });

            const result = await response.json();

            if (response.ok && result.success) {
                // 登录成功
                this.showMessage('登录成功', '欢迎回来！', 'success');

                // 保存用户信息
                this.saveUserInfo(result.data);

                // 记住我功能
                if (credentials.rememberMe) {
                    this.saveCredentials(credentials.username);
                } else {
                    this.clearStoredCredentials();
                }

                // 延迟跳转
                setTimeout(() => {
                    window.location.href = '/admin.html';
                }, 1500);

            } else {
                // 登录失败
                this.showMessage('登录失败', result.message || '用户名或密码错误', 'error');
            }

        } catch (error) {
            console.error('登录请求失败:', error);
            this.showMessage('登录失败', '网络连接错误，请检查网络设置', 'error');
        } finally {
            this.setLoginLoading(false);
        }
    }

    // 处理注册
    async handleRegister(e) {
        e.preventDefault();

        const formData = new FormData(e.target);
        const userData = {
            username: formData.get('username').trim(),
            email: formData.get('email').trim(),
            password: formData.get('password'),
            passwordConfirm: formData.get('passwordConfirm'),
            role: formData.get('role'),
            agreeTerms: formData.get('agreeTerms') === 'on'
        };

        // 验证注册表单
        if (!this.validateRegisterForm(userData)) {
            return;
        }

        this.setRegisterLoading(true);

        try {
            const response = await fetch('/api/auth/register', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(userData)
            });

            const result = await response.json();

            if (response.ok && result.success) {
                // 注册成功
                this.showMessage('注册成功', '账户创建成功，请使用新账户登录', 'success');
                this.hideRegisterModal();

                // 自动填充登录表单
                document.getElementById('username').value = userData.username;
                document.getElementById('username').focus();

            } else {
                // 注册失败
                this.showMessage('注册失败', result.message || '注册过程中发生错误', 'error');
            }

        } catch (error) {
            console.error('注册请求失败:', error);
            this.showMessage('注册失败', '网络连接错误，请稍后重试', 'error');
        } finally {
            this.setRegisterLoading(false);
        }
    }

    // 验证登录表单
    validateLoginForm(credentials) {
        if (!credentials.username) {
            this.showMessage('输入错误', '请输入用户名', 'warning');
            document.getElementById('username').focus();
            return false;
        }

        if (!credentials.password) {
            this.showMessage('输入错误', '请输入密码', 'warning');
            document.getElementById('password').focus();
            return false;
        }

        if (credentials.username.length < 3) {
            this.showMessage('输入错误', '用户名至少需要3个字符', 'warning');
            document.getElementById('username').focus();
            return false;
        }

        return true;
    }

    // 验证注册表单
    validateRegisterForm(userData) {
        // 检查必填字段
        if (!userData.username || !userData.email || !userData.password ||
            !userData.passwordConfirm || !userData.role) {
            this.showMessage('输入错误', '请填写所有必填字段', 'warning');
            return false;
        }

        // 验证用户名
        if (!this.validateUsername(userData.username)) {
            return false;
        }

        // 验证邮箱
        if (!this.validateEmail(userData.email)) {
            return false;
        }

        // 验证密码
        if (!this.validatePassword(userData.password)) {
            return false;
        }

        // 验证密码确认
        if (userData.password !== userData.passwordConfirm) {
            this.showMessage('输入错误', '两次输入的密码不一致', 'warning');
            document.getElementById('regPasswordConfirm').focus();
            return false;
        }

        // 检查服务条款
        if (!userData.agreeTerms) {
            this.showMessage('注册要求', '请阅读并同意服务条款', 'warning');
            return false;
        }

        return true;
    }

    // 验证用户名
    validateUsername(username) {
        if (!username) {
            username = document.getElementById('regUsername')?.value;
        }

        const usernameRegex = /^[a-zA-Z0-9_]{3,20}$/;
        const isValid = usernameRegex.test(username);

        const field = document.getElementById('regUsername');
        if (field) {
            this.setFieldValidation(field, isValid,
                isValid ? '用户名格式正确' : '用户名只能包含字母、数字和下划线，长度3-20位');
        }

        return isValid;
    }

    // 验证邮箱
    validateEmail(email) {
        if (!email) {
            email = document.getElementById('regEmail')?.value;
        }

        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        const isValid = emailRegex.test(email);

        const field = document.getElementById('regEmail');
        if (field) {
            this.setFieldValidation(field, isValid,
                isValid ? '邮箱格式正确' : '请输入有效的邮箱地址');
        }

        return isValid;
    }

    // 验证密码
    validatePassword(password) {
        if (!password) {
            password = document.getElementById('regPassword')?.value;
        }

        const minLength = password.length >= 8;
        const hasNumber = /\d/.test(password);
        const hasLetter = /[a-zA-Z]/.test(password);
        const isValid = minLength && hasNumber && hasLetter;

        const field = document.getElementById('regPassword');
        if (field) {
            let message = '';
            if (!minLength) message = '密码至少需要8个字符';
            else if (!hasNumber) message = '密码需要包含至少一个数字';
            else if (!hasLetter) message = '密码需要包含至少一个字母';
            else message = '密码强度良好';

            this.setFieldValidation(field, isValid, message);
        }

        return isValid;
    }

    // 验证密码匹配
    validatePasswordMatch() {
        const password = document.getElementById('regPassword')?.value;
        const passwordConfirm = document.getElementById('regPasswordConfirm')?.value;
        const isValid = password === passwordConfirm && passwordConfirm.length > 0;

        const field = document.getElementById('regPasswordConfirm');
        if (field) {
            this.setFieldValidation(field, isValid,
                isValid ? '密码确认正确' : '两次输入的密码不一致');
        }

        return isValid;
    }

    // 设置字段验证状态
    setFieldValidation(field, isValid, message) {
        const container = field.closest('.form-group');
        if (!container) return;

        // 移除现有的验证提示
        const existingHint = container.querySelector('.validation-hint');
        if (existingHint) {
            existingHint.remove();
        }

        // 设置字段样式
        field.style.borderColor = isValid ? '#27ae60' : '#e74c3c';

        // 添加验证提示
        const hint = document.createElement('small');
        hint.className = `validation-hint ${isValid ? 'valid' : 'invalid'}`;
        hint.textContent = message;
        hint.style.color = isValid ? '#27ae60' : '#e74c3c';
        hint.style.fontSize = '12px';
        hint.style.marginTop = '4px';
        container.appendChild(hint);
    }

    // 切换密码显示
    togglePasswordVisibility() {
        const passwordField = document.getElementById('password');
        const toggleBtn = document.getElementById('passwordToggle');
        const icon = toggleBtn.querySelector('i');

        if (passwordField.type === 'password') {
            passwordField.type = 'text';
            icon.className = 'fas fa-eye-slash';
        } else {
            passwordField.type = 'password';
            icon.className = 'fas fa-eye';
        }
    }

    // 显示注册模态框
    showRegisterModal() {
        const modal = document.getElementById('registerModal');
        if (modal) {
            modal.classList.add('show');
            document.getElementById('regUsername')?.focus();
        }
    }

    // 隐藏注册模态框
    hideRegisterModal() {
        const modal = document.getElementById('registerModal');
        if (modal) {
            modal.classList.remove('show');
            this.clearRegisterForm();
        }
    }

    // 清空注册表单
    clearRegisterForm() {
        const form = document.getElementById('registerForm');
        if (form) {
            form.reset();
            // 清除验证提示
            form.querySelectorAll('.validation-hint').forEach(hint => hint.remove());
            form.querySelectorAll('input').forEach(input => {
                input.style.borderColor = '#e9ecef';
            });
        }
    }

    // 处理忘记密码
    handleForgotPassword() {
        const email = prompt('请输入您的邮箱地址，我们将发送重置密码的链接：');

        if (email) {
            if (this.validateEmail(email)) {
                this.showMessage('重置链接已发送', '请查看您的邮箱并按照说明重置密码', 'info');
                // 这里可以调用实际的密码重置API
            } else {
                this.showMessage('邮箱格式错误', '请输入有效的邮箱地址', 'warning');
            }
        }
    }

    // 检查系统状态
    async checkSystemStatus() {
        try {
            const response = await fetch('/health');
            const data = await response.json();

            const statusElement = document.getElementById('systemStatus');
            if (statusElement) {
                if (response.ok && data.status === 'healthy') {
                    statusElement.textContent = '正常';
                    statusElement.style.color = '#27ae60';
                } else {
                    statusElement.textContent = '异常';
                    statusElement.style.color = '#e74c3c';
                }
            }
        } catch (error) {
            const statusElement = document.getElementById('systemStatus');
            if (statusElement) {
                statusElement.textContent = '离线';
                statusElement.style.color = '#e74c3c';
            }
        }
    }

    // 保存用户信息
    saveUserInfo(userInfo) {
        sessionStorage.setItem('userInfo', JSON.stringify(userInfo));

        // 设置token（如果有）
        if (userInfo.token) {
            sessionStorage.setItem('authToken', userInfo.token);
        }
    }

    // 保存登录凭据（记住我功能）
    saveCredentials(username) {
        localStorage.setItem('rememberedUsername', username);
    }

    // 加载已保存的凭据
    loadStoredCredentials() {
        const rememberedUsername = localStorage.getItem('rememberedUsername');
        if (rememberedUsername) {
            const usernameField = document.getElementById('username');
            const rememberMeField = document.getElementById('rememberMe');

            if (usernameField) {
                usernameField.value = rememberedUsername;
            }

            if (rememberMeField) {
                rememberMeField.checked = true;
            }
        }
    }

    // 清除已保存的凭据
    clearStoredCredentials() {
        localStorage.removeItem('rememberedUsername');
    }

    // 设置登录按钮加载状态
    setLoginLoading(loading) {
        const btn = document.getElementById('loginBtn');
        const btnText = btn?.querySelector('.btn-text');
        const btnLoading = btn?.querySelector('.btn-loading');

        if (btn) {
            btn.disabled = loading;

            if (btnText && btnLoading) {
                btnText.style.display = loading ? 'none' : 'inline';
                btnLoading.style.display = loading ? 'flex' : 'none';
            }
        }
    }

    // 设置注册按钮加载状态
    setRegisterLoading(loading) {
        const btn = document.getElementById('registerBtn');
        const btnText = btn?.querySelector('.btn-text');
        const btnLoading = btn?.querySelector('.btn-loading');

        if (btn) {
            btn.disabled = loading;

            if (btnText && btnLoading) {
                btnText.style.display = loading ? 'none' : 'inline';
                btnLoading.style.display = loading ? 'flex' : 'none';
            }
        }
    }

    // 显示消息
    showMessage(title, text, type = 'info', duration = 4000) {
        const container = document.getElementById('messageContainer');
        if (!container) return;

        const messageId = 'msg_' + Date.now();
        const message = document.createElement('div');
        message.className = `message ${type}`;
        message.id = messageId;

        const iconMap = {
            success: 'fas fa-check-circle',
            error: 'fas fa-exclamation-circle',
            warning: 'fas fa-exclamation-triangle',
            info: 'fas fa-info-circle'
        };

        message.innerHTML = `
            <div class="message-icon">
                <i class="${iconMap[type]}"></i>
            </div>
            <div class="message-content">
                <div class="message-title">${title}</div>
                <div class="message-text">${text}</div>
            </div>
            <button class="message-close" onclick="loginManager.removeMessage('${messageId}')">
                <i class="fas fa-times"></i>
            </button>
        `;

        container.appendChild(message);

        // 自动移除
        setTimeout(() => {
            this.removeMessage(messageId);
        }, duration);
    }

    // 移除消息
    removeMessage(messageId) {
        const message = document.getElementById(messageId);
        if (message) {
            message.style.animation = 'slideOutRight 0.3s ease forwards';
            setTimeout(() => {
                if (message.parentNode) {
                    message.parentNode.removeChild(message);
                }
            }, 300);
        }
    }

    // 设置输入框焦点效果
    setupInputFocusEffects() {
        const inputs = document.querySelectorAll('input');
        inputs.forEach(input => {
            input.addEventListener('focus', () => {
                const inputGroup = input.closest('.input-group');
                if (inputGroup) {
                    inputGroup.classList.add('focused');
                }
            });

            input.addEventListener('blur', () => {
                const inputGroup = input.closest('.input-group');
                if (inputGroup) {
                    inputGroup.classList.remove('focused');
                }
            });
        });
    }

    // 检查密码强度
    checkPasswordStrength() {
        const password = document.getElementById('password')?.value;
        if (!password) {
            this.updatePasswordStrength(0, '');
            return;
        }

        let strength = 0;
        let feedback = '';

        // 长度检查
        if (password.length >= 8) strength += 1;
        if (password.length >= 12) strength += 1;

        // 复杂度检查
        if (/[a-z]/.test(password)) strength += 1;
        if (/[A-Z]/.test(password)) strength += 1;
        if (/\d/.test(password)) strength += 1;
        if (/[^a-zA-Z\d]/.test(password)) strength += 1;

        // 计算强度等级
        if (strength <= 2) {
            feedback = '密码强度：弱';
            this.updatePasswordStrength(25, 'weak', feedback);
        } else if (strength <= 4) {
            feedback = '密码强度：中等';
            this.updatePasswordStrength(50, 'fair', feedback);
        } else if (strength <= 5) {
            feedback = '密码强度：良好';
            this.updatePasswordStrength(75, 'good', feedback);
        } else {
            feedback = '密码强度：很强';
            this.updatePasswordStrength(100, 'strong', feedback);
        }
    }

    // 更新密码强度显示
    updatePasswordStrength(percentage, level, text) {
        const strengthFill = document.getElementById('strengthFill');
        const strengthText = document.getElementById('strengthText');

        if (strengthFill && strengthText) {
            strengthFill.style.width = percentage + '%';
            strengthFill.className = 'strength-fill ' + level;
            strengthText.textContent = text;
            strengthText.className = 'strength-text ' + level;
        }
    }

    // 显示密码强度指示器
    showPasswordStrength() {
        const passwordStrength = document.getElementById('passwordStrength');
        const password = document.getElementById('password')?.value;

        if (passwordStrength && password) {
            passwordStrength.style.display = 'block';
            this.checkPasswordStrength();
        }
    }

    // 隐藏密码强度指示器
    hidePasswordStrength() {
        const passwordStrength = document.getElementById('passwordStrength');
        if (passwordStrength) {
            passwordStrength.style.display = 'none';
        }
    }

    // 处理社交登录
    async handleSocialLogin(provider) {
        const btn = document.getElementById(provider + 'Login');

        if (!btn) return;

        // 设置加载状态
        btn.classList.add('loading');
        btn.disabled = true;

        try {
            this.showMessage('社交登录', `正在连接${provider === 'wechat' ? '微信' : '钉钉'}...`, 'info');

            // 模拟社交登录流程
            await new Promise(resolve => setTimeout(resolve, 1500));

            // 根据不同的社交平台处理登录
            if (provider === 'wechat') {
                // 微信登录逻辑
                await this.processWechatLogin();
            } else if (provider === 'dingtalk') {
                // 钉钉登录逻辑
                await this.processDingtalkLogin();
            }

        } catch (error) {
            console.error(`${provider}登录失败:`, error);
            this.showMessage('登录失败', `${provider === 'wechat' ? '微信' : '钉钉'}登录失败，请稍后重试`, 'error');
        } finally {
            // 恢复按钮状态
            btn.classList.remove('loading');
            btn.disabled = false;
        }
    }

    // 处理微信登录
    async processWechatLogin() {
        // 这里应该实现微信OAuth登录流程
        // 目前作为演示，模拟成功登录

        // 模拟微信授权
        const wechatCode = await this.getWechatAuthCode();

        if (wechatCode) {
            // 调用后端API验证微信授权
            const response = await fetch('/api/auth/wechat-login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ code: wechatCode })
            });

            if (response.ok) {
                const result = await response.json();
                if (result.success) {
                    this.showMessage('登录成功', '微信登录成功！', 'success');
                    this.saveUserInfo(result.data);
                    setTimeout(() => {
                        window.location.href = '/admin.html';
                    }, 1500);
                }
            }
        } else {
            // 演示模式
            this.showMessage('登录成功', '微信登录成功！（演示模式）', 'success');
            setTimeout(() => {
                window.location.href = '/admin.html';
            }, 1500);
        }
    }

    // 处理钉钉登录
    async processDingtalkLogin() {
        // 这里应该实现钉钉OAuth登录流程
        // 目前作为演示，模拟成功登录

        const dingtalkCode = await this.getDingtalkAuthCode();

        if (dingtalkCode) {
            // 调用后端API验证钉钉授权
            const response = await fetch('/api/auth/dingtalk-login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ code: dingtalkCode })
            });

            if (response.ok) {
                const result = await response.json();
                if (result.success) {
                    this.showMessage('登录成功', '钉钉登录成功！', 'success');
                    this.saveUserInfo(result.data);
                    setTimeout(() => {
                        window.location.href = '/admin.html';
                    }, 1500);
                }
            }
        } else {
            // 演示模式
            this.showMessage('登录成功', '钉钉登录成功！（演示模式）', 'success');
            setTimeout(() => {
                window.location.href = '/admin.html';
            }, 1500);
        }
    }

    // 获取微信授权码（模拟）
    async getWechatAuthCode() {
        // 实际应用中，这里会打开微信授权页面或使用微信SDK
        return new Promise((resolve) => {
            // 模拟获取授权码
            setTimeout(() => {
                resolve('mock_wechat_code_' + Date.now());
            }, 1000);
        });
    }

    // 获取钉钉授权码（模拟）
    async getDingtalkAuthCode() {
        // 实际应用中，这里会打开钉钉授权页面或使用钉钉SDK
        return new Promise((resolve) => {
            // 模拟获取授权码
            setTimeout(() => {
                resolve('mock_dingtalk_code_' + Date.now());
            }, 1000);
        });
    }

    // 初始化主题
    initTheme() {
        const savedTheme = localStorage.getItem('theme') || 'light';
        const systemPreference = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
        const theme = savedTheme || systemPreference;

        this.applyTheme(theme);
    }

    // 切换主题
    toggleTheme() {
        const currentTheme = document.documentElement.getAttribute('data-theme');
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';

        this.applyTheme(newTheme);
        localStorage.setItem('theme', newTheme);

        // 添加切换动画
        this.animateThemeToggle();
    }

    // 应用主题
    applyTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);

        const themeIcon = document.getElementById('themeIcon');
        if (themeIcon) {
            themeIcon.className = theme === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
        }

        // 更新CSS变量
        if (theme === 'dark') {
            this.enableDarkMode();
        } else {
            this.enableLightMode();
        }
    }

    // 启用深色模式
    enableDarkMode() {
        const root = document.documentElement;
        root.style.setProperty('--bg-primary', '#1a1a1a');
        root.style.setProperty('--bg-secondary', '#2d2d2d');
        root.style.setProperty('--bg-overlay', 'rgba(45, 45, 45, 0.95)');
        root.style.setProperty('--text-primary', '#ffffff');
        root.style.setProperty('--text-secondary', '#b0b0b0');
        root.style.setProperty('--text-muted', '#888888');
        root.style.setProperty('--border-color', '#404040');
        root.style.setProperty('--border-light', '#333333');
        root.style.setProperty('--primary-gradient', 'linear-gradient(135deg, #2980b9 0%, #1f2937 100%)');
    }

    // 启用浅色模式
    enableLightMode() {
        const root = document.documentElement;
        root.style.setProperty('--bg-primary', '#f8f9fa');
        root.style.setProperty('--bg-secondary', '#ffffff');
        root.style.setProperty('--bg-overlay', 'rgba(255, 255, 255, 0.95)');
        root.style.setProperty('--text-primary', '#2c3e50');
        root.style.setProperty('--text-secondary', '#7f8c8d');
        root.style.setProperty('--text-muted', '#95a5a6');
        root.style.setProperty('--border-color', '#dee2e6');
        root.style.setProperty('--border-light', '#e9ecef');
        root.style.setProperty('--primary-gradient', 'linear-gradient(135deg, #3498db 0%, #2c3e50 100%)');
    }

    // 主题切换动画
    animateThemeToggle() {
        const toggle = document.getElementById('themeToggle');
        if (toggle) {
            toggle.style.transform = 'scale(0.8) rotate(180deg)';
            setTimeout(() => {
                toggle.style.transform = 'scale(1) rotate(0deg)';
            }, 200);
        }

        // 添加页面过渡效果
        document.body.style.transition = 'background-color 0.3s ease';
    }

  // 处理键盘事件
    handleKeyboardEvents(e) {
        // ESC键关闭模态框
        if (e.key === 'Escape') {
            const modal = document.getElementById('registerModal');
            if (modal && modal.classList.contains('show')) {
                this.hideRegisterModal();
            }
        }

        // Enter键提交表单
        if (e.key === 'Enter') {
            const activeElement = document.activeElement;

            if (activeElement && activeElement.closest('#loginForm')) {
                e.preventDefault();
                document.getElementById('loginForm')?.dispatchEvent(new Event('submit'));
            } else if (activeElement && activeElement.closest('#registerForm')) {
                e.preventDefault();
                document.getElementById('registerForm')?.dispatchEvent(new Event('submit'));
            }
        }
    }

    // 清理方法
    destroy() {
        // 清理定时器和事件监听器
        console.log('LoginManager destroyed');
    }
}

// 全局实例
let loginManager;

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', () => {
    loginManager = new LoginManager();
});

// 页面卸载时清理
window.addEventListener('beforeunload', () => {
    if (loginManager) {
        loginManager.destroy();
    }
});

// 添加CSS动画
const additionalStyles = `
.input-group.focused {
    transform: translateY(-1px);
}

.input-group.focused i {
    color: var(--primary-color);
}

.message {
    transform: translateX(100%);
    animation: slideInRight 0.3s ease forwards;
}

@keyframes slideOutRight {
    from {
        opacity: 1;
        transform: translateX(0);
    }
    to {
        opacity: 0;
        transform: translateX(100%);
    }
}

.validation-hint {
    display: block;
    margin-top: 4px;
    font-size: 12px;
    transition: all 0.3s ease;
}

.validation-hint.valid {
    color: #27ae60;
}

.validation-hint.invalid {
    color: #e74c3c;
}

/* 按钮加载动画 */
@keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}

.fa-spinner {
    animation: spin 1s linear infinite;
}

/* 表单字段验证样式 */
input.valid {
    border-color: #27ae60 !important;
    box-shadow: 0 0 0 3px rgba(39, 174, 96, 0.1) !important;
}

input.invalid {
    border-color: #e74c3c !important;
    box-shadow: 0 0 0 3px rgba(231, 76, 60, 0.1) !important;
}

/* 改进的hover效果 */
.login-btn:hover:not(:disabled),
.register-btn:hover:not(:disabled) {
    background: linear-gradient(135deg, #2980b9 0%, #1f2937 100%);
}

/* 改进的focus效果 */
input:focus {
    border-color: var(--primary-color) !important;
    box-shadow: 0 0 0 3px rgba(52, 152, 219, 0.1) !important;
}

/* 模态框动画改进 */
.modal.show .modal-content {
    animation: modalSlideUp 0.4s cubic-bezier(0.25, 0.46, 0.45, 0.94);
}

@keyframes modalSlideUp {
    0% {
        opacity: 0;
        transform: translateY(50px) scale(0.95);
    }
    100% {
        opacity: 1;
        transform: translateY(0) scale(1);
    }
}
`;

// 添加样式到页面
const styleSheet = document.createElement('style');
styleSheet.textContent = additionalStyles;
document.head.appendChild(styleSheet);