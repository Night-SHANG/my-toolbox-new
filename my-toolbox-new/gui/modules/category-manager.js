/**
 * 分类管理模块 - 处理分类的加载、渲染和相关操作
 */
export class CategoryManager {
    constructor(app) {
        this.app = app;
    }
    
    async loadCategories() {
        try {
            // 后端 categoryOrder 现在是唯一且可靠的数据源，它已经排好序
            const orderedCategories = await window.pywebview.api.get_category_order();
            
            // 直接使用这个列表进行渲染
            this.renderCategories(orderedCategories);
        } catch (error) {
            console.error('加载分类失败:', error);
        }
    }
    
    renderCategories(categories) {
        const categoryList = document.getElementById('category-list');
        
        // 检查是否正在拖拽分类，如果是，保存当前拖拽元素的引用，然后重新渲染
        const draggingElement = document.querySelector('.dragging');
        if (!draggingElement) {
            categoryList.innerHTML = '';
            
            // 添加"全部"分类
            const allCategory = document.createElement('div');
            allCategory.className = 'category-item active';
            allCategory.textContent = '全部脚本';
            allCategory.dataset.category = 'all';
            allCategory.addEventListener('click', () => {
                this.app.switchCategory('all');
            });
            categoryList.appendChild(allCategory);
            
            // 只添加自定义分类，过滤掉"未分类"
            categories.forEach(category => {
                // 跳过"未分类"
                if (category === '未分类' || category === '收藏夹') {
                    return;
                }
                
                const categoryItem = document.createElement('div');
                categoryItem.className = 'category-item';
                categoryItem.draggable = true; // 启用拖拽
                
                categoryItem.textContent = category;
                categoryItem.dataset.category = category;
                categoryItem.addEventListener('click', () => {
                    this.app.switchCategory(category);
                });
                
                // 添加右键菜单以支持分类管理
                categoryItem.addEventListener('contextmenu', (e) => {
                    e.preventDefault();
                    this.app.menuManager.showCategoryContextMenu(e, category);
                });
                
                categoryList.appendChild(categoryItem);
            });
            
            // 启用 SortableJS 拖拽排序
            this.app.dragDropManager.enableCategoryDragAndDrop(categoryList);
        } else {
            // 如果正在拖拽，保留DOM结构，仅更新数据
            console.log("分类拖拽进行中，跳过渲染以保持拖拽状态");
        }
    }
    
    async addCustomCategory() {
        const categoryName = prompt('请输入新的分类名称:');
        if (categoryName && categoryName.trim() !== '') {
            try {
                const result = await window.pywebview.api.add_custom_category(categoryName.trim());
                if (result) {
                    // 重新加载分类
                    await this.loadCategories();
                    // 分类添加成功，但不显示提示
                } else {
                    console.log('添加分类失败或分类已存在');
                }
            } catch (error) {
                console.error('添加分类失败:', error);
            }
        }
    }
}