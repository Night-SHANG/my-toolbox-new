/**
 * 脚本管理模块 - 处理脚本的加载、渲染和相关操作
 */
import { IconManager } from './icon-manager.js';

export class ScriptManager {
    constructor(app) {
        this.app = app;
        this.iconManager = new IconManager(app);
    }
    
    async loadScripts() {
        try {
            this.app.scripts = await window.pywebview.api.get_scripts();
            console.log('已加载脚本:', this.app.scripts.length);
            
            // 获取保存的脚本排序
            const savedScriptOrder = await window.pywebview.api.get_script_order();
            
            // 如果有保存的排序，则按照保存的顺序重新排列脚本
            if (savedScriptOrder && savedScriptOrder.length > 0) {
                // 创建一个映射，把ID映射到排序位置
                const orderMap = new Map();
                savedScriptOrder.forEach((id, index) => {
                    orderMap.set(id, index);
                });
                
                // 按照保存的顺序对脚本进行排序
                this.app.scripts.sort((a, b) => {
                    const orderA = orderMap.has(a.id) ? orderMap.get(a.id) : Infinity;
                    const orderB = orderMap.has(b.id) ? orderMap.get(b.id) : Infinity;
                    return orderA - orderB;
                });
            }
        } catch (error) {
            console.error('加载脚本失败:', error);
        }
    }
    
    renderScripts() {
        const grid = document.getElementById('scripts-grid');
        
        // 检查是否正在拖拽，如果是，保存当前拖拽元素的引用，然后重新渲染
        const draggingElement = document.querySelector('.dragging');
        let draggingScriptId = null;
        if (draggingElement) {
            draggingScriptId = draggingElement.dataset.scriptId;
        }
        
        // 只有在不是拖拽状态或需要强制刷新时才清空并重新渲染
        if (!draggingElement) {
            grid.innerHTML = '';
            
            let filteredScripts = this.app.scripts;
            
            // 按分类过滤
            if (this.app.currentCategory !== 'all') {
                filteredScripts = filteredScripts.filter(script => 
                    script.category === this.app.currentCategory
                );
            }
            
            // 按搜索关键词过滤
            if (this.app.searchQuery) {
                filteredScripts = filteredScripts.filter(script => 
                    script.name.toLowerCase().includes(this.app.searchQuery) ||
                    script.description.toLowerCase().includes(this.app.searchQuery) ||
                    (script.category && script.category.toLowerCase().includes(this.app.searchQuery))
                );
            }
            
            // 渲染脚本卡片
            filteredScripts.forEach(script => {
                const card = this.createScriptCard(script);
                grid.appendChild(card);
            });
            
            // 在所有视图中启用脚本拖拽功能
            // 清除之前的拖拽初始化标记，以便重新设置事件
            delete grid._dragDropInitialized;
            this.app.dragDropManager.enableScriptDragAndDrop(grid);
        } else {
            // 如果正在拖拽，保留DOM结构，仅更新数据
            // 这样可以避免中断拖拽操作
            console.log("拖拽进行中，跳过渲染以保持拖拽状态");
        }
    }
    
    createScriptCard(script) {
        const card = document.createElement('div');
        card.className = 'script-card';
        card.dataset.scriptId = script.id; // 添加scriptId数据属性
        
        card.innerHTML = `
            <div class="card-category">${script.category || '未分类'}</div>
            <div class="card-icon" id="icon-${script.id}">⏳</div>  <!-- 图标容器 -->
            <div class="card-title" title="${script.name}">${script.name}</div>
            <div class="card-description" title="${script.description || ''}">${script.description || '暂无描述'}</div>
        `;
        
        // 设置脚本图标
        this.iconManager.setScriptIcon(card, script);
        
        card.addEventListener('click', () => {
            this.onScriptCardClick(script);
        });
        
        // 添加右键菜单以支持脚本管理
        card.addEventListener('contextmenu', (e) => {
            e.preventDefault();
            this.app.menuManager.showScriptContextMenu(e, script);
        });
        
        return card;
    }
    
    async onScriptCardClick(script) {
        this.app.selectedScript = script;
        
        // 检查脚本是否有参数
        if (script.parameters && script.parameters.length > 0) {
            // 显示参数配置模态框
            this.app.modalManager.showParamModal(script);
        } else {
            // 直接执行无参数脚本
            this.app.executeScript(script.id, {});
        }
    }
    
    updateScriptDisplay(scriptId, updates) {
        // 更新应用中的脚本数据
        const script = this.app.scripts.find(s => s.id === scriptId);
        if (script) {
            Object.assign(script, updates);
        }

        // 重新渲染脚本卡片
        this.renderScripts();
    }

    getScriptConfig(scriptId) {
        return this.app.cachedUserPreferences?.scripts?.[scriptId] || {};
    }

    updateScriptConfig(scriptId, newConfig) {
        if (!this.app.cachedUserPreferences.scripts) {
            this.app.cachedUserPreferences.scripts = {};
        }
        if (!this.app.cachedUserPreferences.scripts[scriptId]) {
            this.app.cachedUserPreferences.scripts[scriptId] = {};
        }
        Object.assign(this.app.cachedUserPreferences.scripts[scriptId], newConfig);
    }
}