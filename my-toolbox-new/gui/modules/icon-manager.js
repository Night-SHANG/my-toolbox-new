/**
 * 图标管理器 - 处理脚本图标的前端显示和管理
 */

export class IconManager {
    constructor(app) {
        this.app = app;
        this.iconsCache = new Map(); // 缓存已加载的图标
    }

    /**
     * 为脚本卡片设置图标
     * @param {HTMLElement} scriptCard - 脚本卡片DOM元素
     * @param {Object} script - 脚本对象
     */
    setScriptIcon(scriptCard, script) {
        const iconContainer = scriptCard.querySelector('.card-icon');
        if (!iconContainer) {
            console.error('找不到图标容器');
            return;
        }

        // 清空现有图标内容
        iconContainer.innerHTML = '';

        if (script.icon) {
            // 尝试加载图像图标
            this.loadImageIcon(iconContainer, script.icon, script.name);
        } else {
            // 如果没有指定图标，保持为空或显示默认
            iconContainer.innerHTML = '<span class="emoji-icon">⚙️</span>';
        }
    }

    /**
     * 加载图像图标
     */
    async loadImageIcon(iconContainer, iconPath, scriptName) {
        // 创建加载中的占位元素
        iconContainer.innerHTML = '<div class="loading-icon">⏳</div>';

        try {
            // 通过API将图标文件转换为base64格式
            const result = await window.pywebview.api.get_icon_as_base64(iconPath);
            
            if (result.success) {
                // 创建图像元素
                const img = document.createElement('img');
                img.src = result.base64_data;
                img.alt = scriptName;
                img.classList.add('script-icon-img');

                // 设置加载成功回调
                img.onload = () => {
                    // 从占位符替换为实际图像
                    iconContainer.innerHTML = '';
                    iconContainer.appendChild(img);
                };

                // 设置加载失败回调
                img.onerror = () => {
                    // 如果加载失败，回退到默认图标
                    iconContainer.innerHTML = '<span class="emoji-icon">❌</span>';
                    console.warn(`加载图标失败: ${iconPath}`);
                };
            } else {
                // API调用失败，显示错误图标
                iconContainer.innerHTML = '<span class="emoji-icon">❌</span>';
                console.error(`获取图标base64数据失败: ${result.error} for path: ${iconPath}`);
            }
        } catch (error) {
            // 出现异常，显示错误图标
            iconContainer.innerHTML = '<span class="emoji-icon">❌</span>';
            console.error('加载图标时出错:', error);
        }
    }

    /**
     * 直接打开文件选择器选择图标
     */
    async openIconSelector(script) {
        try {
            // 获取脚本所在文件夹路径
            const scriptFolderPath = this.getScriptFolderPath(script.file_path);
            
            // 通过API打开文件选择对话框，默认路径为脚本文件夹
            const result = await window.pywebview.api.open_file_dialog();
            
            if (result.success) {
                // 用户选择了图标文件，更新脚本元数据
                const iconPath = result.file_path;
                
                // 更新脚本元数据
                const updateResult = await window.pywebview.api.update_script_metadata(script.id, { icon: iconPath });
                
                if (updateResult.success) {
                    // 更新前端显示
                    this.app.scriptManager.updateScriptDisplay(script.id, { icon: iconPath });
                    
                    // 如果编辑模态框已打开，也需要更新输入框
                    const iconInput = document.getElementById('edit-script-icon');
                    if (iconInput) {
                        iconInput.value = iconPath;
                    }
                    
                    console.log('图标更新成功');
                } else {
                    console.error('更新图标失败:', updateResult.error);
                    alert('更新图标失败: ' + updateResult.error);
                }
            }
        } catch (error) {
            console.error('选择图标时出错:', error);
            alert('选择图标时发生错误: ' + error.message);
        }
    }
    
    /**
     * 从脚本文件路径获取脚本文件夹路径
     */
    getScriptFolderPath(scriptFilePath) {
        // 处理Windows和Unix路径分隔符
        const normalizedPath = scriptFilePath.replace(/\\/g, '/');
        const lastSlashIndex = normalizedPath.lastIndexOf('/');
        if (lastSlashIndex !== -1) {
            return normalizedPath.substring(0, lastSlashIndex);
        }
        return normalizedPath;
    }
}