/**
 * 拖拽管理模块 - 处理拖拽排序功能
 */
export class DragDropManager {
    constructor(app) {
        this.app = app;
    }
    
    // 启用脚本卡片拖拽排序功能
    enableScriptDragAndDrop(grid) {
        const self = this; // 保存DragDropManager实例引用
        
        // 避免重复添加事件监听器，先清除现有的
        if (grid._dragDropInitialized) {
            return;
        }
        grid._dragDropInitialized = true;
        
        const scriptCards = grid.querySelectorAll('.script-card');
        
        scriptCards.forEach(card => {
            card.draggable = true;
            
            card.addEventListener('dragstart', (e) => {
                e.dataTransfer.setData('text/plain', card.dataset.scriptId);
                card.classList.add('dragging');
                e.dataTransfer.effectAllowed = 'move';
            });
            
            card.addEventListener('dragend', (e) => {
                card.classList.remove('dragging');
                // 移除所有占位符类
                const placeholders = grid.querySelectorAll('.script-card.placeholder');
                placeholders.forEach(placeholder => {
                    placeholder.classList.remove('placeholder');
                });
                // 强制重新渲染所有脚本以应用新的排序
                self.app.scriptManager.renderScripts();
                // 现在DOM顺序已更新，保存新的排序状态
                setTimeout(() => {
                    self.saveScriptOrder(grid);
                }, 0);
            });

            // 添加拖拽相关事件监听器
            card.addEventListener('dragover', (e) => {
                e.preventDefault(); // 必须调用才能允许放置
                e.dataTransfer.dropEffect = 'move';
            });
            
            card.addEventListener('dragenter', (e) => {
                // 只有当不是被拖动的元素时才添加占位符类
                if (e.currentTarget !== document.querySelector('.dragging')) {
                    e.currentTarget.classList.add('placeholder');
                }
            });
            
            card.addEventListener('dragleave', (e) => {
                e.currentTarget.classList.remove('placeholder');
            });
            
            card.addEventListener('drop', (e) => {
                e.stopPropagation(); // 阻止事件冒泡
                const draggedElement = document.querySelector('.dragging');
                if (draggedElement && e.currentTarget !== draggedElement) {
                    // 实现交换逻辑
                    self.handleScriptDrop(grid, draggedElement, e.currentTarget);
                }
            });
        });
    }
    
    // 处理脚本卡片的拖拽放置逻辑
    handleScriptDrop(grid, draggedElement, targetElement) {
        const draggedScriptId = draggedElement.dataset.scriptId;
        const targetScriptId = targetElement.dataset.scriptId;
        
        // 从当前脚本数组中找到这两个脚本
        const draggedScriptIndex = this.app.scripts.findIndex(script => script.id === draggedScriptId);
        const targetScriptIndex = this.app.scripts.findIndex(script => script.id === targetScriptId);
        
        if (draggedScriptIndex !== -1 && targetScriptIndex !== -1 && draggedScriptIndex !== targetScriptIndex) {
            // 创建新数组并移动位置
            const newScripts = [...this.app.scripts];
            
            // 从原位置移除拖拽的脚本
            const [draggedScript] = newScripts.splice(draggedScriptIndex, 1);
            
            // 计算插入索引
            // 直接将元素插入到目标位置，不考虑移除操作对索引的影响
            const insertIndex = targetScriptIndex;
            
            // 插入到计算出的位置
            newScripts.splice(insertIndex, 0, draggedScript);
            
            // 更新app的脚本数组
            this.app.scripts = newScripts;
            
            // 重新渲染，使DOM顺序与数组顺序一致
            this.app.scriptManager.renderScripts();
            
            // 现在DOM顺序已更新，保存新的排序状态
            this.saveScriptOrder(grid);
        }
    }
    
    // 启用分类拖拽排序功能
    enableCategoryDragAndDrop(categoryList) {
        // 避免重复添加事件监听器，先清除现有的
        if (categoryList._dragDropInitialized) {
            return;
        }
        categoryList._dragDropInitialized = true;
        
        const categoryItems = categoryList.querySelectorAll('.category-item');
        
        categoryItems.forEach(item => {
            item.addEventListener('dragstart', (e) => {
                e.dataTransfer.setData('text/plain', item.dataset.category);
                item.classList.add('dragging');
                setTimeout(() => {
                    item.style.opacity = '0.4';
                }, 0);
            });
            
            item.addEventListener('dragend', (e) => {
                item.classList.remove('dragging');
                item.style.opacity = '1';
                // 保存分类顺序
                this.saveCategoryOrder(categoryList);
            });
            
            // 添加拖拽相关事件监听器
            item.addEventListener('dragover', (e) => {
                e.preventDefault(); // 必须调用才能允许放置
                e.dataTransfer.dropEffect = 'move';
            });
            
            item.addEventListener('dragenter', (e) => {
                // 只有当不是被拖动的元素时才添加占位符类
                if (e.currentTarget !== document.querySelector('.category-item.dragging')) {
                    e.currentTarget.classList.add('placeholder');
                }
            });
            
            item.addEventListener('dragleave', (e) => {
                e.currentTarget.classList.remove('placeholder');
            });
            
            item.addEventListener('drop', (e) => {
                e.stopPropagation(); // 阻止事件冒泡
                const draggedElement = document.querySelector('.category-item.dragging');
                if (draggedElement && e.currentTarget !== draggedElement) {
                    // 实现分类交换逻辑
                    this.handleCategoryDrop(categoryList, draggedElement, e.currentTarget);
                }
            });
        });
        
        categoryList.addEventListener('dragover', (e) => {
            e.preventDefault();
            const afterElement = this.getCategoryDragAfterElement(categoryList, e.clientY);
            const draggable = document.querySelector('.category-item.dragging');
            
            // 检查是否拖拽的是"全部脚本"分类，如果是，则不允许移动
            if (draggable && draggable.dataset.category === 'all') {
                return; // 不执行任何DOM操作，保持"全部脚本"在原位置
            }
            
            // 检查目标位置是否在"全部脚本"之前，如果是，则放置在"全部脚本"之后
            if (afterElement && afterElement.dataset.category === 'all') {
                // 将拖拽的元素放置在"全部脚本"分类之后
                categoryList.insertBefore(draggable, afterElement.nextSibling);
            } else if (afterElement == null && categoryList.firstChild && categoryList.firstChild.dataset.category === 'all') {
                // 如果是移动到列表末尾，但第一个是"全部脚本"，则正常处理
                categoryList.appendChild(draggable);
            } else {
                // 其他情况正常处理
                if (afterElement == null) {
                    categoryList.appendChild(draggable);
                } else {
                    categoryList.insertBefore(draggable, afterElement);
                }
            }
        });
        
        categoryList.addEventListener('drop', (e) => {
            e.preventDefault();
        });
    }
    
    // 处理分类的拖拽放置逻辑
    handleCategoryDrop(categoryList, draggedElement, targetElement) {
        const draggedCategory = draggedElement.dataset.category;
        const targetCategory = targetElement.dataset.category;
        
        // 保存分类顺序
        this.saveCategoryOrder(categoryList);
    }
    
    // 辅助函数：确定拖拽元素应插入的位置（针对网格布局优化）
    getDragAfterElement(container, y, x) {
        const draggableElements = [...container.querySelectorAll('.script-card:not(.dragging)')];
        
        if (draggableElements.length === 0) return null;
        
        // 创建一个包含位置信息的数组并排序（按视觉顺序：从上到下，从左到右）
        const elementsWithPosition = draggableElements.map((element, index) => {
            const rect = element.getBoundingClientRect();
            return {
                element,
                index,
                top: rect.top,
                left: rect.left,
                centerX: rect.left + rect.width / 2,
                centerY: rect.top + rect.height / 2,
                rect: rect
            };
        });
        
        // 按视觉顺序排序（先按top，再按left）
        elementsWithPosition.sort((a, b) => {
            // 如果在不同行（垂直位置差异大于元素高度），按垂直位置排序
            if (Math.abs(a.top - b.top) > draggableElements[0].offsetHeight / 2) {
                return a.top - b.top;
            }
            // 如果在同一行，按水平位置排序
            return a.left - b.left;
        });
        
        // 寻找最合适的插入位置
        for (let i = 0; i < elementsWithPosition.length; i++) {
            const currentItem = elementsWithPosition[i];
            
            // 检查是否应该插入到当前项之前
            // 使用更直观的判断逻辑：根据鼠标坐标直接比较
            const rect = currentItem.rect;
            
            // 网格布局中，我们可以使用一种"视觉最近"的算法
            // 计算鼠标位置到每个元素的距离，并考虑视觉顺序
            const nextItem = i < elementsWithPosition.length - 1 ? elementsWithPosition[i + 1] : null;
            
            // 如果有下一项，判断鼠标是在当前项和下一项的哪个影响范围内
            if (nextItem) {
                const currentRect = currentItem.rect;
                const nextRect = nextItem.rect;
                
                // 如果在同一行
                if (Math.abs(currentRect.top - nextRect.top) < currentRect.height / 2) {
                    // 水平方向比较
                    const currentCenterX = currentRect.left + currentRect.width / 2;
                    const nextCenterX = nextRect.left + nextRect.width / 2;
                    const midX = (currentCenterX + nextCenterX) / 2;
                    
                    if (x < midX) {
                        return currentItem.element;
                    } else {
                        continue; // 跳到下一个
                    }
                } else {
                    // 不同行，垂直方向比较
                    const currentCenterY = currentRect.top + currentRect.height / 2;
                    const nextCenterY = nextRect.top + nextRect.height / 2;
                    const midY = (currentCenterY + nextCenterY) / 2;
                    
                    if (y < midY) {
                        return currentItem.element;
                    } else {
                        continue; // 跳到下一个
                    }
                }
            } else {
                // 最后一项，直接比较
                const currentCenterY = rect.top + rect.height / 2;
                const currentCenterX = rect.left + rect.width / 2;
                
                // 如果在同一行范围但更靠右
                if (Math.abs(y - currentCenterY) <= rect.height / 2 && x > currentCenterX) {
                    return null; // 插入到最后
                } else if (y < currentCenterY || (Math.abs(y - currentCenterY) <= rect.height / 2 && x < currentCenterX)) {
                    return currentItem.element;
                }
            }
        }
        
        return null;
    }
    
    // 辅助函数：确定分类拖拽元素应插入的位置（优化垂直列表）
    getCategoryDragAfterElement(container, y) {
        const draggableElements = [...container.querySelectorAll('.category-item:not(.dragging)')];
        
        return draggableElements.reduce((closest, child) => {
            const box = child.getBoundingClientRect();
            const offset = y - box.top - box.height / 2;
            
            if (offset < 0 && offset > closest.offset) {
                return { offset: offset, element: child };
            } else {
                return closest;
            }
        }, { offset: Number.NEGATIVE_INFINITY }).element;
    }
    
    // 保存脚本顺序
    async saveScriptOrder(grid) {
        const scriptCards = grid.querySelectorAll('.script-card');
        const scriptOrder = Array.from(scriptCards).map(card => card.dataset.scriptId);
        
        try {
            // 通过API保存脚本顺序
            await window.pywebview.api.save_script_order(scriptOrder);
        } catch (error) {
            console.error('保存脚本顺序失败:', error);
        }
    }
    
    // 保存分类顺序
    async saveCategoryOrder(categoryList) {
        const categoryItems = categoryList.querySelectorAll('.category-item');
        let categoryOrder = Array.from(categoryItems)
            .map(item => item.dataset.category)
            .filter(category => category !== 'all'); // 过滤掉 “all” 分类
        
        try {
            // 通过API保存分类顺序
            await window.pywebview.api.save_category_order(categoryOrder);
        } catch (error) {
            console.error('保存分类顺序失败:', error);
        }
    }
}