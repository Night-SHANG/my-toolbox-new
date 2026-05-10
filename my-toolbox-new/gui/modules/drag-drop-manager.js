/**
 * 拖拽管理模块 - 基于 SortableJS 实现丝滑的拖拽排序
 */
export class DragDropManager {
    constructor(app) {
        this.app = app;
        this.scriptSortable = null;   // 脚本网格的 Sortable 实例
        this.categorySortable = null; // 分类列表的 Sortable 实例
    }

    /**
     * 启用脚本卡片拖拽排序功能（基于 SortableJS）
     */
    enableScriptDragAndDrop(grid) {
        // 销毁旧实例，避免重复绑定
        if (this.scriptSortable) {
            this.scriptSortable.destroy();
            this.scriptSortable = null;
        }

        this.scriptSortable = new Sortable(grid, {
            animation: 200,           // 拖拽动画时长（毫秒）
            easing: 'cubic-bezier(0.25, 1, 0.5, 1)', // 缓动函数
            ghostClass: 'placeholder', // 占位符样式类
            dragClass: 'dragging',     // 被拖拽元素的样式类
            delay: 100,                // 延迟触发拖拽，防止误触
            delayOnTouchOnly: true,    // 仅触摸设备启用延迟

            // 拖拽结束时：更新前端数据 + 保存到后端
            onEnd: (evt) => {
                // 强制清除所有残留的 dragging 样式，防止卡片歪斜
                document.querySelectorAll('.dragging').forEach(el => el.classList.remove('dragging'));
                // 从当前 DOM 顺序重建脚本数组
                this.syncScriptsFromDOM(grid);
                // 保存新排序到后端
                this.saveScriptOrder(grid);
            }
        });
    }

    /**
     * 启用分类拖拽排序功能（基于 SortableJS）
     */
    enableCategoryDragAndDrop(categoryList) {
        // 销毁旧实例
        if (this.categorySortable) {
            this.categorySortable.destroy();
            this.categorySortable = null;
        }

        this.categorySortable = new Sortable(categoryList, {
            animation: 200,
            easing: 'cubic-bezier(0.25, 1, 0.5, 1)',
            ghostClass: 'placeholder',
            dragClass: 'dragging',

            // 过滤器：禁止拖动"全部脚本"分类项
            filter: '[data-category="all"]',

            // 拖拽结束时保存分类顺序
            onEnd: (evt) => {
                // 强制清除所有残留的 dragging 样式
                document.querySelectorAll('.dragging').forEach(el => el.classList.remove('dragging'));
                // 确保"全部脚本"始终在最顶部
                const allItem = categoryList.querySelector('[data-category="all"]');
                if (allItem && allItem !== categoryList.firstChild) {
                    categoryList.insertBefore(allItem, categoryList.firstChild);
                }
                this.saveCategoryOrder(categoryList);
            }
        });
    }

    /**
     * 根据 DOM 中卡片的当前顺序，同步更新 app.scripts 数组
     */
    syncScriptsFromDOM(grid) {
        const cardIds = Array.from(grid.querySelectorAll('.script-card'))
            .map(card => card.dataset.scriptId);

        // 创建 ID -> 脚本对象的映射
        const scriptMap = new Map();
        this.app.scripts.forEach(script => {
            scriptMap.set(script.id, script);
        });

        // 按照 DOM 顺序重建脚本数组
        const newScripts = [];
        cardIds.forEach(id => {
            const script = scriptMap.get(id);
            if (script) {
                newScripts.push(script);
            }
        });

        // 把不在当前视图中的脚本（被过滤掉的）追加到末尾
        this.app.scripts.forEach(script => {
            if (!cardIds.includes(script.id)) {
                newScripts.push(script);
            }
        });

        this.app.scripts = newScripts;
    }

    /**
     * 保存脚本顺序到后端
     */
    async saveScriptOrder(grid) {
        const scriptCards = grid.querySelectorAll('.script-card');
        const scriptOrder = Array.from(scriptCards).map(card => card.dataset.scriptId);

        try {
            await window.pywebview.api.save_script_order(scriptOrder);
        } catch (error) {
            console.error('保存脚本顺序失败:', error);
        }
    }

    /**
     * 保存分类顺序到后端
     */
    async saveCategoryOrder(categoryList) {
        const categoryItems = categoryList.querySelectorAll('.category-item');
        let categoryOrder = Array.from(categoryItems)
            .map(item => item.dataset.category)
            .filter(category => category !== 'all'); // 过滤掉 "all" 分类

        try {
            await window.pywebview.api.save_category_order(categoryOrder);
        } catch (error) {
            console.error('保存分类顺序失败:', error);
        }
    }
}