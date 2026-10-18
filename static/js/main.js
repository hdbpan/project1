// 全局JavaScript函数

// 格式化货币
function formatCurrency(amount) {
    return '¥' + parseFloat(amount).toFixed(2);
}

// 格式化日期时间
function formatDateTime(dateStr) {
    const date = new Date(dateStr);
    return date.toLocaleString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    });
}

// Toast通知
function showToast(type, message, duration = 3000) {
    // 移除已存在的toast
    const existingToasts = document.querySelectorAll('.custom-toast');
    existingToasts.forEach(toast => toast.remove());

    // 创建新的toast
    const toast = document.createElement('div');
    toast.className = `alert alert-${type} alert-dismissible fade show custom-toast`;
    toast.style.cssText = `
        position: fixed;
        top: 80px;
        right: 20px;
        z-index: 9999;
        min-width: 300px;
        box-shadow: 0 0.5rem 1rem rgba(0,0,0,0.15);
        animation: slideInRight 0.3s ease-out;
    `;

    const icon = {
        'success': 'check-circle',
        'danger': 'exclamation-circle',
        'warning': 'exclamation-triangle',
        'info': 'info-circle'
    }[type] || 'info-circle';

    toast.innerHTML = `
        <i class="bi bi-${icon}"></i> ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;

    document.body.appendChild(toast);

    // 自动移除
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }, duration);
}

// 添加动画CSS
if (!document.getElementById('custom-toast-style')) {
    const style = document.createElement('style');
    style.id = 'custom-toast-style';
    style.textContent = `
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
    `;
    document.head.appendChild(style);
}

// 确认对话框
function confirmAction(message, callback) {
    if (confirm(message)) {
        callback();
    }
}

// AJAX请求封装
function ajaxRequest(url, options = {}) {
    const defaultOptions = {
        method: 'GET',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        credentials: 'same-origin'
    };

    const finalOptions = { ...defaultOptions, ...options };

    return fetch(url, finalOptions)
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .catch(error => {
            console.error('Request failed:', error);
            showToast('danger', '请求失败，请稍后重试');
            throw error;
        });
}

// 防抖函数
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// 节流函数
function throttle(func, limit) {
    let inThrottle;
    return function(...args) {
        if (!inThrottle) {
            func.apply(this, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

// 表单验证
function validateForm(formId) {
    const form = document.getElementById(formId);
    if (!form) return false;

    const inputs = form.querySelectorAll('input[required], select[required], textarea[required]');
    let isValid = true;

    inputs.forEach(input => {
        if (!input.value.trim()) {
            input.classList.add('is-invalid');
            isValid = false;
        } else {
            input.classList.remove('is-invalid');
        }
    });

    return isValid;
}

// 清除表单验证状态
function clearValidation(formId) {
    const form = document.getElementById(formId);
    if (!form) return;

    form.querySelectorAll('.is-invalid').forEach(element => {
        element.classList.remove('is-invalid');
    });

    form.querySelectorAll('.invalid-feedback').forEach(element => {
        element.style.display = 'none';
    });
}

// 数字动画
function animateNumber(element, start, end, duration = 1000) {
    let startTime = null;

    function animate(currentTime) {
        if (!startTime) startTime = currentTime;
        const progress = Math.min((currentTime - startTime) / duration, 1);

        const value = Math.floor(progress * (end - start) + start);
        element.textContent = value;

        if (progress < 1) {
            requestAnimationFrame(animate);
        }
    }

    requestAnimationFrame(animate);
}

// 本地存储操作
const Storage = {
    set(key, value) {
        try {
            localStorage.setItem(key, JSON.stringify(value));
            return true;
        } catch (e) {
                        console.error('Storage set error:', e);
            return false;
        }
    },

    get(key, defaultValue = null) {
        try {
            const value = localStorage.getItem(key);
            return value ? JSON.parse(value) : defaultValue;
        } catch (e) {
            console.error('Storage get error:', e);
            return defaultValue;
        }
    },

    remove(key) {
        try {
            localStorage.removeItem(key);
            return true;
        } catch (e) {
            console.error('Storage remove error:', e);
            return false;
        }
    },

    clear() {
        try {
            localStorage.clear();
            return true;
        } catch (e) {
            console.error('Storage clear error:', e);
            return false;
        }
    }
};

// 复制到剪贴板
function copyToClipboard(text) {
    if (navigator.clipboard && navigator.clipboard.writeText) {
        return navigator.clipboard.writeText(text)
            .then(() => {
                showToast('success', '已复制到剪贴板');
                return true;
            })
            .catch(err => {
                console.error('Copy failed:', err);
                return fallbackCopy(text);
            });
    } else {
        return fallbackCopy(text);
    }
}

// 备用复制方法
function fallbackCopy(text) {
    const textarea = document.createElement('textarea');
    textarea.value = text;
    textarea.style.position = 'fixed';
    textarea.style.opacity = '0';
    document.body.appendChild(textarea);
    textarea.select();

    try {
        const successful = document.execCommand('copy');
        if (successful) {
            showToast('success', '已复制到剪贴板');
        } else {
            showToast('danger', '复制失败');
        }
        return successful;
    } catch (err) {
        console.error('Fallback copy failed:', err);
        showToast('danger', '复制失败');
        return false;
    } finally {
        document.body.removeChild(textarea);
    }
}

// 获取URL参数
function getUrlParam(name) {
    const params = new URLSearchParams(window.location.search);
    return params.get(name);
}

// 滚动到顶部
function scrollToTop(smooth = true) {
    if (smooth) {
        window.scrollTo({
            top: 0,
            behavior: 'smooth'
        });
    } else {
        window.scrollTo(0, 0);
    }
}

// 页面加载完成后执行
document.addEventListener('DOMContentLoaded', function() {
    // 初始化所有tooltip
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // 初始化所有popover
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function(popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });

    // 自动关闭alert
    const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
    alerts.forEach(alert => {
        setTimeout(() => {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });

    // 图片加载错误处理
    document.querySelectorAll('img').forEach(img => {
        img.addEventListener('error', function() {
            if (!this.dataset.errorHandled) {
                this.src = '/static/images/default.jpg';
                this.dataset.errorHandled = 'true';
            }
        });
    });

    // 表单输入自动移除验证提示
    document.querySelectorAll('input, select, textarea').forEach(element => {
        element.addEventListener('input', function() {
            this.classList.remove('is-invalid');
        });
    });

    // 数字输入框只允许数字
    document.querySelectorAll('input[type="number"]').forEach(input => {
        input.addEventListener('keypress', function(e) {
            const charCode = e.which ? e.which : e.keyCode;
            if (charCode > 31 && (charCode < 48 || charCode > 57) && charCode !== 46) {
                e.preventDefault();
            }
        });
    });

    // 返回顶部按钮
    const backToTopBtn = document.createElement('button');
    backToTopBtn.innerHTML = '<i class="bi bi-arrow-up"></i>';
    backToTopBtn.className = 'btn btn-primary btn-back-to-top';
    backToTopBtn.style.cssText = `
        position: fixed;
        bottom: 20px;
        right: 20px;
        z-index: 1000;
        display: none;
        border-radius: 50%;
        width: 50px;
        height: 50px;
        padding: 0;
        box-shadow: 0 2px 10px rgba(0,0,0,0.3);
    `;

    document.body.appendChild(backToTopBtn);

    // 监听滚动显示/隐藏返回顶部按钮
    window.addEventListener('scroll', throttle(function() {
        if (window.pageYOffset > 300) {
            backToTopBtn.style.display = 'block';
        } else {
            backToTopBtn.style.display = 'none';
        }
    }, 200));

    backToTopBtn.addEventListener('click', function() {
        scrollToTop(true);
    });
});

// 网络状态监听
window.addEventListener('online', function() {
    showToast('success', '网络已连接');
});

window.addEventListener('offline', function() {
    showToast('warning', '网络已断开');
});

// 导出全局函数
window.AppUtils = {
    formatCurrency,
    formatDateTime,
    showToast,
    confirmAction,
    ajaxRequest,
    debounce,
    throttle,
    validateForm,
    clearValidation,
    animateNumber,
    Storage,
    copyToClipboard,
    getUrlParam,
    scrollToTop
};

