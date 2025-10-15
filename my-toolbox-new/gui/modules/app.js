/**
 * 脚本工具箱 - 应用入口和初始化
 */
import { ScriptManager } from './script-manager.js';
import { CategoryManager } from './category-manager.js';
import { ModalManager } from './modal-manager.js';
import { MenuManager } from './menu-manager.js';
import { DragDropManager } from './drag-drop-manager.js';
import { TerminalManager } from './terminal-manager.js';
import { ScriptUpdateManager } from './script-update-manager.js';
import { IconManager } from './icon-manager.js';

export class ScriptToolbox {
    constructor() {
        this.scriptManager = new ScriptManager(this);
        this.categoryManager = new CategoryManager(this);
        this.modalManager = new ModalManager(this);
        this.menuManager = new MenuManager(this);
        this.dragDropManager = new DragDropManager(this);
        this.terminalManager = new TerminalManager(this);
        this.scriptUpdateManager = new ScriptUpdateManager(this);
        this.iconManager = new IconManager(this);
        
        this.scripts = [];
        this.currentCategory = 'all';
        this.searchQuery = '';
        this.selectedScript = null;
        
        this.init();
    }
    
    async init() {
        this.setupEventListeners();
        await this.scriptManager.loadScripts();
        await this.categoryManager.loadCategories();
        this.scriptManager.renderScripts();
        
        // 尝试立即创建用户配置文件
        try {
            // 获取当前用户配置以确保文件存在
            const userPrefs = await window.pywebview.api.get_user_preferences();
            this.cachedUserPreferences = userPrefs;
        } catch (error) {
            console.error('获取用户偏好时出错:', error);
        }
    }
    
    setupEventListeners() {
        // 搜索功能
        document.getElementById('search-input').addEventListener('input', (e) => {
            this.searchQuery = e.target.value.toLowerCase();
            this.scriptManager.renderScripts();
        });
        
        // 刷新按钮
        document.getElementById('refresh-btn').addEventListener('click', async () => {
            await this.scriptManager.loadScripts();
            await this.categoryManager.loadCategories();
            this.scriptManager.renderScripts();
        });
        
        // 添加分类按钮
        document.getElementById('add-category-btn').addEventListener('click', () => {
            this.categoryManager.addCustomCategory();
        });
        
        // 模态框相关事件 - 现在在使用模态框时动态绑定事件
        document.getElementById('modal-close').addEventListener('click', () => {
            this.modalManager.hideModal();
        });
        
        document.getElementById('modal-cancel').addEventListener('click', () => {
            this.modalManager.hideModal();
        });
        
        // 初始执行按钮事件 - 会被具体使用时重写
        document.getElementById('modal-execute').addEventListener('click', () => {
            this.executeScriptWithParams();
        });
        
        // 终端视图关闭按钮
        document.getElementById('terminal-close').addEventListener('click', () => {
            document.getElementById('terminal-view').style.display = 'none';
        });

        // 终端视图终止任务按钮
        document.getElementById('terminal-kill-btn').addEventListener('click', async () => {
            if (confirm('确定要终止当前正在运行的任务吗？')) {
                try {
                    const result = await window.pywebview.api.terminate_current_script();
                    if (result.success) {
                        alert('终止信号已发送！请稍候查看输出结果。');
                    } else {
                        alert(result.error);
                    }
                } catch (e) {
                    alert(`发送终止信号失败: ${e.message}`);
                }
            }
        });
    }
    
    switchCategory(category) {
        // 更新分类选中状态
        document.querySelectorAll('.category-item').forEach(item => {
            item.classList.toggle('active', item.dataset.category === category);
        });
        
        this.currentCategory = category;
        this.scriptManager.renderScripts();
    }
    
    async executeScript(scriptId, params = {}) {
        // 显示终端视图
        document.getElementById('terminal-view').style.display = 'flex';
        document.getElementById('terminal-output').innerHTML = '';
        
        // 执行脚本
        try {
            await window.pywebview.api.execute_script(scriptId, params);
        } catch (error) {
            console.error('执行脚本失败:', error);
            const errorMsg = `<span style="color: red;">执行脚本时发生错误: ${error.message}</span><br>`;
            window.updateTerminal && window.updateTerminal(errorMsg);
        }
    }
    
    async executeScriptWithParams() {
        if (!this.selectedScript) return;
        
        const params = {};
        
        // 收集参数值
        this.selectedScript.parameters.forEach(param => {
            const input = document.getElementById(`param-${param.name}`);
            
            if (param.type === 'boolean') {
                params[param.name] = input.checked;
            } else {
                params[param.name] = input.value;
            }
        });
        
        this.modalManager.hideModal();
        await this.executeScript(this.selectedScript.id, params);
    }
    
    // 保存当前状态到用户配置
    async saveCurrentState() {
        try {
            // 保存当前脚本排序
            const scriptGrid = document.getElementById('scripts-grid');
            if (scriptGrid) {
                const scriptCards = scriptGrid.querySelectorAll('.script-card');
                const scriptOrder = Array.from(scriptCards).map(card => card.dataset.scriptId);
                await window.pywebview.api.save_script_order(scriptOrder);
            }
            
            // 保存当前分类排序
            const categoryList = document.getElementById('category-list');
            if (categoryList) {
                const categoryItems = categoryList.querySelectorAll('.category-item');
                const categoryOrder = Array.from(categoryItems)
                    .map(item => item.dataset.category)
                    .filter(category => category !== 'all'); // 过滤掉 “all” 分类
                await window.pywebview.api.save_category_order(categoryOrder);
            }
        } catch (error) {
            console.error('保存当前状态时出错:', error);
        }
    }
}

// 初始化应用 - 等待pywebview API准备就绪
function initializeApp() {
    if (window.pywebview && window.pywebview.api) {
        // API已准备就绪，创建应用实例
        window.scriptToolbox = new ScriptToolbox();
    } else {
        // API还未准备就绪，等待一段时间后重试
        setTimeout(initializeApp, 100);
    }
}

// 首先等待DOM加载完成
document.addEventListener('DOMContentLoaded', () => {
    // 立即尝试初始化，如果API不可用则稍后重试
    initializeApp();
});