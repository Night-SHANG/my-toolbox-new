/**
 * 菜单管理模块 - 处理右键菜单的显示和交互
 */
export class MenuManager {
    constructor(app) {
        this.app = app;
    }

    // 添加右键菜单支持，用于将脚本分配到分类
    addScriptContextMenu(scriptId, scriptName) {
        const scriptElement = event.target.closest('.script-card');
        if (!scriptElement) return;

        // 创建右键菜单
        const menu = document.createElement('div');
        menu.className = 'context-menu';
        menu.style.position = 'fixed';
        menu.style.left = event.clientX + 'px';
        menu.style.top = event.clientY + 'px';
        menu.style.zIndex = '1000';
        menu.style.backgroundColor = 'var(--card-bg)';
        menu.style.border = '1px solid var(--border-color)';
        menu.style.borderRadius = '4px';
        menu.style.padding = '4px 0';
        menu.style.boxShadow = '0 2px 10px rgba(0,0,0,0.1)';

        // 获取所有分类并添加到菜单
        const userPrefs = this.getUserPreferencesSync(); // 需要一个同步获取分类的方法
        const allCategories = [...new Set([...this.getCurrentSystemCategories(), ...(userPrefs.custom_categories || [])])];

        allCategories.forEach(category => {
            const menuItem = document.createElement('div');
            menuItem.className = 'context-menu-item';
            menuItem.textContent = `移动到 "${category}"`;
            menuItem.style.padding = '8px 16px';
            menuItem.style.cursor = 'pointer';
            menuItem.style.color = 'var(--text-color)';

            menuItem.addEventListener('mouseover', () => {
                menuItem.style.backgroundColor = 'var(--secondary-bg)';
            });

            menuItem.addEventListener('mouseout', () => {
                menuItem.style.backgroundColor = '';
            });

            menuItem.addEventListener('click', async () => {
                try {
                    await window.pywebview.api.assign_script_to_category(scriptId, category);
                    // 重新加载界面
                    await this.app.scriptManager.loadScripts();
                    await this.app.categoryManager.loadCategories();
                    this.app.scriptManager.renderScripts();
                    document.body.removeChild(menu);
                } catch (error) {
                    console.error('分配脚本到分类失败:', error);
                }
            });

            menu.appendChild(menuItem);
        });

        // 添加删除选项
        const deleteItem = document.createElement('div');
        deleteItem.className = 'context-menu-item';
        deleteItem.textContent = '从分类移除';
        deleteItem.style.padding = '8px 16px';
        deleteItem.style.cursor = 'pointer';
        deleteItem.style.color = 'var(--text-color)';

        deleteItem.addEventListener('mouseover', () => {
            deleteItem.style.backgroundColor = 'var(--secondary-bg)';
        });

        deleteItem.addEventListener('mouseout', () => {
            deleteItem.style.backgroundColor = '';
        });

        deleteItem.addEventListener('click', async () => {
            try {
                await window.pywebview.api.assign_script_to_category(scriptId, '未分类');
                // 重新加载界面
                await this.app.scriptManager.loadScripts();
                await this.app.categoryManager.loadCategories();
                this.app.scriptManager.renderScripts();
                document.body.removeChild(menu);
            } catch (error) {
                console.error('移除脚本分类失败:', error);
            }
        });

        menu.appendChild(deleteItem);

        document.body.appendChild(menu);

        // 点击其他地方关闭菜单
        const closeMenu = () => {
            if (document.body.contains(menu)) {
                document.body.removeChild(menu);
            }
            document.removeEventListener('click', closeMenu);
        };

        setTimeout(() => {
            document.addEventListener('click', closeMenu);
        }, 0);
    }

    // 一个同步获取当前系统分类的方法（简单实现）
    getCurrentSystemCategories() {
        const categories = ['未分类']; // 基础分类
        // 从当前脚本中提取所有分类
        this.app.scripts.forEach(script => {
            const category = script.category || '未分类';
            if (!categories.includes(category)) {
                categories.push(category);
            }
        });
        return categories;
    }

    // 同步获取用户偏好（简单实现）
    getUserPreferencesSync() {
        // 由于pywebview API是异步的，我们暂时返回一个模拟对象
        // 在实际应用中，我们会缓存用户偏好
        if (this.app.cachedUserPreferences) {
            return this.app.cachedUserPreferences;
        }
        return { custom_categories: [] };
    }

    // 显示脚本右键菜单
    async showScriptContextMenu(event, script) {
        // 首先移除可能存在的其他菜单
        const existingMenus = document.querySelectorAll('.context-menu');
        existingMenus.forEach(menu => {
            if (document.body.contains(menu)) {
                document.body.removeChild(menu);
            }
        });

        // 创建右键菜单
        const menu = document.createElement('div');
        menu.className = 'context-menu';
        menu.style.position = 'fixed';
        menu.style.left = event.clientX + 'px';
        menu.style.top = event.clientY + 'px';
        menu.style.zIndex = '1000';
        menu.style.backgroundColor = 'var(--card-bg)';
        menu.style.border = '1px solid var(--border-color)';
        menu.style.borderRadius = '4px';
        menu.style.padding = '4px 0';
        menu.style.boxShadow = '0 2px 10px rgba(0,0,0,0.1)';
        menu.style.minWidth = '180px';

        // 编辑脚本信息
        const editItem = document.createElement('div');
        editItem.className = 'context-menu-item';
        editItem.textContent = '📝 编辑脚本';
        editItem.style.padding = '8px 16px';
        editItem.style.cursor = 'pointer';
        editItem.style.color = 'var(--text-color)';
        editItem.style.borderBottom = '1px solid var(--border-color)';

        editItem.addEventListener('mouseover', () => {
            editItem.style.backgroundColor = 'var(--secondary-bg)';
        });

        editItem.addEventListener('mouseout', () => {
            editItem.style.backgroundColor = '';
        });

        editItem.addEventListener('click', async () => {
            document.body.removeChild(menu);
            this.app.modalManager.showEditScriptModal(script);
        });

        menu.appendChild(editItem);

        // 删除脚本
        const deleteItem = document.createElement('div');
        deleteItem.className = 'context-menu-item';
        deleteItem.textContent = '❌ 删除脚本';
        deleteItem.style.padding = '8px 16px';
        deleteItem.style.cursor = 'pointer';
        deleteItem.style.color = 'var(--text-color)';
        deleteItem.style.borderBottom = '1px solid var(--border-color)';

        deleteItem.addEventListener('mouseover', () => {
            deleteItem.style.backgroundColor = 'var(--secondary-bg)';
        });

        deleteItem.addEventListener('mouseout', () => {
            deleteItem.style.backgroundColor = '';
        });

        deleteItem.addEventListener('click', async () => {
            if (confirm(`确定要永久删除脚本 "${script.name}" 吗？\n此操作不可恢复！`)) {
                try {
                    const result = await window.pywebview.api.delete_script(script.id);
                    if (result.success) {
                        // 重新加载界面以反映删除
                        await this.app.scriptManager.loadScripts();
                        await this.app.categoryManager.loadCategories();
                        this.app.scriptManager.renderScripts();
                    } else {
                        alert(`删除脚本失败: ${result.error}`);
                    }
                } catch (e) {
                    alert(`删除脚本时发生错误: ${e.message}`);
                }
                document.body.removeChild(menu);
            }
        });

        menu.appendChild(deleteItem);

        // 打开脚本所在文件夹
        const openFolderItem = document.createElement('div');
        openFolderItem.className = 'context-menu-item';
        openFolderItem.textContent = '📁 打开文件夹';
        openFolderItem.style.padding = '8px 16px';
        openFolderItem.style.cursor = 'pointer';
        openFolderItem.style.color = 'var(--text-color)';

        openFolderItem.addEventListener('mouseover', () => {
            openFolderItem.style.backgroundColor = 'var(--secondary-bg)';
        });

        openFolderItem.addEventListener('mouseout', () => {
            openFolderItem.style.backgroundColor = '';
        });

        openFolderItem.addEventListener('click', async () => {
            try {
                await window.pywebview.api.open_script_folder(script.file_path);
                document.body.removeChild(menu);
            } catch (error) {
                console.error('打开文件夹失败:', error);
                alert('打开文件夹失败: ' + error.message);
            }
        });

        menu.appendChild(openFolderItem);

        document.body.appendChild(menu);

        // Adjust position to prevent overflow
        const menuWidth = menu.offsetWidth;
        const menuHeight = menu.offsetHeight;
        const windowWidth = window.innerWidth;
        const windowHeight = window.innerHeight;

        let newLeft = event.clientX;
        let newTop = event.clientY;

        if (event.clientX + menuWidth > windowWidth) {
            newLeft = windowWidth - menuWidth - 5;
        }

        if (event.clientY + menuHeight > windowHeight) {
            newTop = windowHeight - menuHeight - 5;
        }

        menu.style.left = newLeft + 'px';
        menu.style.top = newTop + 'px';

        // 点击其他地方关闭菜单
        const closeMenu = (e) => {
            if (e.target !== menu && !menu.contains(e.target)) {
                if (document.body.contains(menu)) {
                    document.body.removeChild(menu);
                }
                document.removeEventListener('click', closeMenu);
            }
        };

        setTimeout(() => {
            document.addEventListener('click', closeMenu);
        }, 0);
    }

    // 显示分类右键菜单
    async showCategoryContextMenu(event, category) {
        // 首先移除可能存在的其他菜单
        const existingMenus = document.querySelectorAll('.context-menu');
        existingMenus.forEach(menu => {
            if (document.body.contains(menu)) {
                document.body.removeChild(menu);
            }
        });

        // 创建右键菜单
        const menu = document.createElement('div');
        menu.className = 'context-menu';
        menu.style.position = 'fixed';
        menu.style.left = event.clientX + 'px';
        menu.style.top = event.clientY + 'px';
        menu.style.zIndex = '1000';
        menu.style.backgroundColor = 'var(--card-bg)';
        menu.style.border = '1px solid var(--border-color)';
        menu.style.borderRadius = '4px';
        menu.style.padding = '4px 0';
        menu.style.boxShadow = '0 2px 10px rgba(0,0,0,0.1)';
        menu.style.minWidth = '150px';

        // 检查是否为自定义分类
        // 自定义分类包括：用户配置中的自定义分类 + 脚本文件中定义的非系统分类
        const userPrefs = await window.pywebview.api.get_user_preferences();
        const systemCategories = ['未分类', '收藏夹', '全部脚本']; // 系统分类列表

        // 检查是否是用户定义的自定义分类
        const isUserCustomCategory = userPrefs.custom_categories && userPrefs.custom_categories.includes(category);

        // 检查是否是非系统分类（在脚本中定义的分类）
        const isScriptDefinedCategory = category && !systemCategories.includes(category);

        // 如果是自定义分类（用户定义的或脚本定义的非系统分类），显示右键菜单
        if (isUserCustomCategory || isScriptDefinedCategory) {
            // 添加重命名选项
            const renameItem = document.createElement('div');
            renameItem.className = 'context-menu-item';
            renameItem.textContent = '✏️ 重命名';
            renameItem.style.padding = '8px 16px';
            renameItem.style.cursor = 'pointer';
            renameItem.style.color = 'var(--text-color)';
            renameItem.style.borderBottom = '1px solid var(--border-color)';

            renameItem.addEventListener('mouseover', () => {
                renameItem.style.backgroundColor = 'var(--secondary-bg)';
            });

            renameItem.addEventListener('mouseout', () => {
                renameItem.style.backgroundColor = '';
            });

            renameItem.addEventListener('click', async () => {
                const newName = prompt('请输入新的分类名称:', category);
                if (newName && newName.trim() !== '' && newName.trim() !== category) {
                    try {
                        // 如果是用户配置中的自定义分类，则删除它
                        if (isUserCustomCategory) {
                            await window.pywebview.api.remove_custom_category(category);
                        }

                        // 添加新分类到自定义分类列表
                        await window.pywebview.api.add_custom_category(newName.trim());

                        // 更新该分类下所有脚本的分类信息
                        const scriptsInCategory = this.app.scripts.filter(script => script.category === category);
                        for (const script of scriptsInCategory) {
                            await window.pywebview.api.assign_script_to_category(script.id, newName.trim());
                        }

                        // 重新加载界面
                        await this.app.scriptManager.loadScripts();
                        await this.app.categoryManager.loadCategories();
                        this.app.scriptManager.renderScripts();
                        document.body.removeChild(menu);
                    } catch (error) {
                        console.error('重命名分类失败:', error);
                        alert('重命名分类时发生错误: ' + error.message);
                    }
                }
            });

            menu.appendChild(renameItem);

            // 添加删除自定义分类选项
            const deleteItem = document.createElement('div');
            deleteItem.className = 'context-menu-item';
            deleteItem.textContent = '❌ 删除';
            deleteItem.style.padding = '8px 16px';
            deleteItem.style.cursor = 'pointer';
            deleteItem.style.color = 'var(--text-color)';

            deleteItem.addEventListener('mouseover', () => {
                deleteItem.style.backgroundColor = 'var(--secondary-bg)';
            });

            deleteItem.addEventListener('mouseout', () => {
                deleteItem.style.backgroundColor = '';
            });

            deleteItem.addEventListener('click', async () => {
                if (confirm(`确定要删除分类 "${category}" 吗？\n该操作会将分类中的所有脚本移至"未分类"`)) {
                    try {
                        // 从用户配置中移除分类
                        if (isUserCustomCategory) {
                            await window.pywebview.api.remove_custom_category(category);
                        }

                        // 将该分类下所有脚本重置为"未分类"
                        const scriptsInCategory = this.app.scripts.filter(script => script.category === category);
                        for (const script of scriptsInCategory) {
                            await window.pywebview.api.assign_script_to_category(script.id, '未分类');
                        }

                        // 切换到"全部脚本"，避免右侧仍过滤已删除的分类
                        this.app.currentCategory = 'all';

                        // 重新加载界面
                        await this.app.scriptManager.loadScripts();
                        await this.app.categoryManager.loadCategories();
                        this.app.scriptManager.renderScripts();
                        document.body.removeChild(menu);
                    } catch (error) {
                        console.error('删除分类失败:', error);
                        alert('删除分类时发生错误: ' + error.message);
                    }
                }
            });

            menu.appendChild(deleteItem);
        }

        document.body.appendChild(menu);

        // Adjust position to prevent overflow
        const menuWidth = menu.offsetWidth;
        const menuHeight = menu.offsetHeight;
        const windowWidth = window.innerWidth;
        const windowHeight = window.innerHeight;

        let newLeft = event.clientX;
        let newTop = event.clientY;

        if (event.clientX + menuWidth > windowWidth) {
            newLeft = windowWidth - menuWidth - 5;
        }

        if (event.clientY + menuHeight > windowHeight) {
            newTop = windowHeight - menuHeight - 5;
        }

        menu.style.left = newLeft + 'px';
        menu.style.top = newTop + 'px';

        // 点击其他地方关闭菜单
        const closeMenu = (e) => {
            if (e.target !== menu && !menu.contains(e.target)) {
                if (document.body.contains(menu)) {
                    document.body.removeChild(menu);
                }
                document.removeEventListener('click', closeMenu);
            }
        };

        setTimeout(() => {
            document.addEventListener('click', closeMenu);
        }, 0);
    }
}