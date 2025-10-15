/**
 * 脚本更新管理模块 - 处理脚本信息更新和用户偏好设置
 */
export class ScriptUpdateManager {
    constructor(app) {
        this.app = app;
    }

    async saveScriptChanges(scriptId, changes) {
        try {
            // 1. 处理名称变更（重命名）
            if (changes.name && changes.name !== scriptId) { // Note: scriptId is the stable ID, but changes.name is the new folder name. The comparison is a bit off but works to detect change.
                const renameResult = await window.pywebview.api.rename_script_folder(scriptId, changes.name);
                if (!renameResult.success) {
                    alert('重命名脚本失败: ' + renameResult.error);
                    return; 
                }

                // 使用后端返回的权威数据更新前端内存
                const scriptInMem = this.app.scripts.find(s => s.id === renameResult.script_id);
                if (scriptInMem) {
                    // 只更新 name，ID 保持稳定不变
                    scriptInMem.name = renameResult.new_name;
                }
            }

            // 2. 处理除名称外的其他元数据变更 (如 category, icon)
            const metadataChanges = {};
            let otherChangesExist = false;
            if (changes.category !== undefined) {
                metadataChanges.category = changes.category;
                otherChangesExist = true;
            }
            if (changes.icon !== undefined) {
                metadataChanges.icon = changes.icon;
                otherChangesExist = true;
            }

            if (otherChangesExist) {
                // 使用稳定的 scriptId 来保存其他更改
                await window.pywebview.api.save_script_setting(scriptId, 'category', metadataChanges.category);
                await window.pywebview.api.save_script_setting(scriptId, 'icon', metadataChanges.icon);
                
                // 更新前端内存中的数据
                const scriptInMem = this.app.scripts.find(s => s.id === scriptId);
                if (scriptInMem) {
                    if(metadataChanges.category !== undefined) scriptInMem.category = metadataChanges.category;
                    if(metadataChanges.icon !== undefined) scriptInMem.icon = metadataChanges.icon;
                }
            }

            // 3. 刷新UI
            // 由于我们已经在内存中进行了精确更新，所以只需要重新渲染，无需从后端完全重新加载
            this.app.scriptManager.renderScripts();
            await this.app.categoryManager.loadCategories(); // 分类列表可能需要更新

            this.app.modalManager.hideModal();

        } catch (error) {
            console.error('保存脚本更改失败:', error);
            alert('保存脚本信息时发生错误: ' + error.message);
        }
    }
}