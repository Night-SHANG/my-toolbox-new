/**
 * 模态框管理模块 - 处理各种模态框的显示和交互
 */
export class ModalManager {
    constructor(app) {
        this.app = app;
    }
    
    hideModal() {
        document.getElementById('modal-overlay').style.display = 'none';
    }
    
    // 显示参数配置模态框
    async showParamModal(script) {
        document.getElementById('modal-title').textContent = `配置 - ${script.name}`;
        
        const modalBody = document.getElementById('modal-body');
        modalBody.innerHTML = ''; // 清空旧内容

        // --- 参数部分 ---
        if (script.parameters && script.parameters.length > 0) {
            const paramsContainer = document.createElement('div');
            script.parameters.forEach(param => {
                const formGroup = document.createElement('div');
                formGroup.className = 'form-group';
                
                const label = document.createElement('label');
                label.className = 'form-label';
                label.textContent = param.label || param.name;
                label.setAttribute('for', `param-${param.name}`);
                
            let input;
            let formRow = document.createElement('div');

            switch (param.type) {
                case 'file':
                case 'folder':
                    formRow.style.display = 'flex';
                    formRow.style.gap = '8px';
                    input = document.createElement('input');
                    input.type = 'text';
                    input.id = `param-${param.name}`;
                    input.className = 'form-input';
                    input.style.flex = '1';
                    input.placeholder = param.placeholder || '';
                    if (param.defaultValue !== undefined) input.value = param.defaultValue;

                    const browseBtn = document.createElement('button');
                    browseBtn.textContent = '浏览...';
                    browseBtn.className = 'btn btn-secondary';
                    browseBtn.type = 'button'; // 防止触发表单提交
                    browseBtn.onclick = async () => {
                        const dialogType = param.type === 'file' ? 10 : 20; // 10 for File, 20 for Folder
                        const result = await window.pywebview.api.show_file_dialog({ dialog_type: dialogType });
                        if (result.success && result.files && result.files.length > 0) {
                            input.value = result.files[0];
                        }
                    };

                    formRow.appendChild(input);
                    formRow.appendChild(browseBtn);

                    const saveBtn = document.createElement('button');
                    saveBtn.textContent = '保存';
                    saveBtn.className = 'btn btn-success';
                    saveBtn.type = 'button';
                    saveBtn.style.marginLeft = '8px';
                    saveBtn.onclick = async () => {
                        try {
                            // 1. 保存数据到后端
                            await window.pywebview.api.save_parameter_default(script.id, param.name, input.value);
                            
                            // 2. 加载新数据到前端内存
                            await this.app.scriptManager.loadScripts();
                            
                            // 3. 用新数据重绘界面
                            this.app.scriptManager.renderScripts();

                            // 提供用户反馈
                            saveBtn.textContent = '已保存!';
                            saveBtn.disabled = true;
                            setTimeout(() => {
                                saveBtn.textContent = '保存';
                                saveBtn.disabled = false;
                            }, 1500);
                        } catch (e) {
                            alert('保存失败: ' + e.message);
                        }
                    };
                    formRow.appendChild(saveBtn);
                    break;
                    
                case 'boolean':
                    input = document.createElement('input');
                    input.type = 'checkbox';
                    input.id = `param-${param.name}`;
                    // 标签和复选框的布局需要特殊处理
                    const labelWrapper = document.createElement('div');
                    labelWrapper.style.display = 'flex';
                    labelWrapper.style.alignItems = 'center';
                    label.style.marginRight = '10px';
                    if (param.defaultValue) input.checked = true;
                    labelWrapper.appendChild(label);
                    labelWrapper.appendChild(input);
                    formRow = labelWrapper; // 直接替换formRow
                    break;
                    
                case 'choice':
                    input = document.createElement('select');
                    input.id = `param-${param.name}`;
                    input.className = 'form-select';
                    param.choices.forEach(choice => {
                        const option = document.createElement('option');
                        option.value = choice.value;
                        option.textContent = choice.label || choice.value;
                        if (choice.value === param.defaultValue) option.selected = true;
                        input.appendChild(option);
                    });
                    formRow.appendChild(input);
                    break;
                    
                case 'textarea':
                    input = document.createElement('textarea');
                    input.id = `param-${param.name}`;
                    input.className = 'form-textarea';
                    input.placeholder = param.placeholder || '';
                    if (param.defaultValue !== undefined) input.value = param.defaultValue;
                    formRow.appendChild(input);
                    break;
                    
                default: // text, number
                    input = document.createElement('input');
                    input.type = param.type || 'text';
                    input.id = `param-${param.name}`;
                    input.className = 'form-input';
                    input.placeholder = param.placeholder || '';
                    if (param.defaultValue !== undefined) input.value = param.defaultValue;
                    formRow.appendChild(input);
            }
            
            if (param.required && input) {
                input.required = true;
            }
            
            // 将label和formRow（或labelWrapper）添加到formGroup
            if (param.type !== 'boolean') {
                formGroup.appendChild(label);
            }
            formGroup.appendChild(formRow);
            modalBody.appendChild(formGroup);
            });
            modalBody.appendChild(paramsContainer);
        }

        // --- 环境与依赖部分 ---
        const venvContainer = document.createElement('div');
        venvContainer.className = 'form-group';
        venvContainer.innerHTML = `
            <hr style="border: none; border-top: 1px solid var(--border-color); margin: 20px 0;">
            <h4>环境与依赖</h4>
            <div class="form-group">
                <label class="form-label">运行环境</label>
                <select class="form-select" id="script-venv-select"><option>加载中...</option></select>
            </div>
            <div class="form-group">
                <button class="btn btn-secondary" id="check-deps-btn">检测依赖</button>
                <button class="btn btn-primary" id="install-deps-btn" style="display: none;">一键安装</button>
            </div>
            <div id="deps-status-container" style="margin-top: 15px; font-size: 14px;"></div>
        `;
        modalBody.appendChild(venvContainer);

        // 填充虚拟环境下拉菜单
        const venvSelect = document.getElementById('script-venv-select');
        try {
            const venvs = await window.pywebview.api.get_venvs();
            console.log('获取到的虚拟环境:', venvs); // 在此处添加诊断日志
            venvSelect.innerHTML = ''; // 清空“加载中”
            Object.keys(venvs).forEach(venvName => {
                const option = document.createElement('option');
                option.value = venvName;
                option.textContent = venvName;
                // script.venv 需要在加载脚本时从 user_preferences 中获取
                if (this.app.scriptManager.getScriptConfig(script.id).venv === venvName) {
                    option.selected = true;
                }
                venvSelect.appendChild(option);
            });
        } catch (e) {
            venvSelect.innerHTML = '<option>加载环境失败</option>';
        }

        // 保存环境选择
        venvSelect.addEventListener('change', async (e) => {
            await window.pywebview.api.save_script_setting(script.id, 'venv', e.target.value);
            this.app.scriptManager.updateScriptConfig(script.id, { venv: e.target.value });
            document.getElementById('deps-status-container').innerHTML = '';
            document.getElementById('install-deps-btn').style.display = 'none';
        });

        // 依赖检测按钮
        document.getElementById('check-deps-btn').addEventListener('click', async () => {
            const selectedVenv = venvSelect.value;
            const statusContainer = document.getElementById('deps-status-container');
            statusContainer.innerHTML = '<p>正在检测...</p>';

            const result = await window.pywebview.api.check_script_dependencies(script.id, selectedVenv);
            
            if (!result.success) {
                statusContainer.innerHTML = `<p style="color: red;">检测失败: ${result.error}</p>`;
                return;
            }

            const statuses = result.dependencies_status;
            if (statuses.length === 0) {
                statusContainer.innerHTML = '<p style="color: green;">✅ 该脚本无需额外依赖。</p>';
                return;
            }

            let allMet = true;
            let html = '<ul style="list-style-type: none; padding: 0;">';
            statuses.forEach(dep => {
                if (dep.status !== '已安装') allMet = false;
                let icon = dep.status === '已安装' ? '✅' : (dep.status === '未安装' ? '❌' : '⚠️');
                html += `<li style="margin-bottom: 5px;">${icon} ${dep.requirement} <span style="color: var(--text-secondary);"> (状态: ${dep.status}, 当前: ${dep.installed_version || 'N/A'})</span></li>`;
            });
            html += '</ul>';
            statusContainer.innerHTML = html;

            document.getElementById('install-deps-btn').style.display = allMet ? 'none' : 'inline-block';
        });

        // 一键安装按钮
        document.getElementById('install-deps-btn').addEventListener('click', async () => {
            const selectedVenv = venvSelect.value;
            const statusContainer = document.getElementById('deps-status-container');
            
            // 将状态区域变为“迷你终端”
            statusContainer.innerHTML = '<p class="loading-msg">正在发送安装指令...</p>';
            statusContainer.style.backgroundColor = '#1e1e1e';
            statusContainer.style.color = '#d4d4d4';
            statusContainer.style.fontFamily = '"Courier New", monospace';
            statusContainer.style.padding = '15px';
            statusContainer.style.borderRadius = '6px';
            statusContainer.style.maxHeight = '200px';
            statusContainer.style.overflowY = 'auto';

            // 禁用检测按钮，防止重复操作
            document.getElementById('check-deps-btn').disabled = true;

            await window.pywebview.api.install_script_dependencies(script.id, selectedVenv);
        });
        
        // 重置按钮文本和事件
        document.getElementById('modal-execute').textContent = '执行';
        const executeBtn = document.getElementById('modal-execute');
        const newExecuteBtn = executeBtn.cloneNode(true);
        executeBtn.parentNode.replaceChild(newExecuteBtn, executeBtn);
        newExecuteBtn.addEventListener('click', () => { this.app.executeScriptWithParams(); });
        
        // 显示模态框
        document.getElementById('modal-overlay').style.display = 'flex';
    }
    
    // 显示编辑脚本模态框
    async showEditScriptModal(script) {
        // 获取所有可用分类
        const userPrefs = await window.pywebview.api.get_user_preferences();
        let allCategories = Array.from(new Set([
            '未分类', 
            ...(userPrefs.custom_categories || []),
            ...this.app.scripts.map(s => s.category).filter(cat => cat)
        ]));
        
        // 过滤掉"未分类"和"收藏夹"分类
        allCategories = allCategories.filter(cat => cat !== '未分类' && cat !== '收藏夹');
        
        // 创建模态框内容
        document.getElementById('modal-title').textContent = `编辑脚本 - ${script.name}`;
        
        const modalBody = document.getElementById('modal-body');
        modalBody.innerHTML = `
            <div class="form-group">
                <label class="form-label">脚本名称</label>
                <input type="text" class="form-input" id="edit-script-name" value="${script.name || ''}">
            </div>
            <div class="form-group">
                <label class="form-label">分类</label>
                <div style="display: flex; gap: 10px;">
                    <select class="form-select" id="edit-script-category">
                        ${allCategories.map(cat => 
                            `<option value="${cat}" ${script.category === cat ? 'selected' : ''}>${cat}</option>`
                        ).join('')}
                        <option value="new" ${!allCategories.includes(script.category) ? 'selected' : ''}>自定义分类</option>
                    </select>
                    <input type="text" class="form-input" id="new-category-name" placeholder="输入新分类" style="display: ${!allCategories.includes(script.category) ? 'block' : 'none'};" value="${(!allCategories.includes(script.category) && script.category !== '未分类') ? (script.category || '') : ''}">
                </div>
            </div>
            <div class="form-group">
                <label class="form-label">自定义图标</label>
                <div style="display: flex; gap: 10px; align-items: center;">
                    <input type="text" class="form-input" id="edit-script-icon" value="${script.icon || ''}" placeholder="点击按钮选择图标">
                    <button id="select-icon-btn" class="btn btn-primary">选择图标</button>
                </div>
            </div>
        `;
        
        // 添加分类选择变化事件
        const categorySelect = document.getElementById('edit-script-category');
        const newCategoryInput = document.getElementById('new-category-name');
        
        categorySelect.addEventListener('change', function() {
            if (this.value === 'new') {
                newCategoryInput.style.display = 'block';
            } else {
                newCategoryInput.style.display = 'none';
            }
        });
        
        // 添加选择图标按钮事件
        document.getElementById('select-icon-btn').addEventListener('click', () => {
            this.app.iconManager.openIconSelector(script);
        });
        
        // 更新执行按钮文本和功能
        document.getElementById('modal-execute').textContent = '保存';
        
        // 保存按钮事件
        const executeBtn = document.getElementById('modal-execute');
        // 移除之前的事件监听器（如果有的话）
        const newExecuteBtn = executeBtn.cloneNode(true);
        executeBtn.parentNode.replaceChild(newExecuteBtn, executeBtn);
        
        newExecuteBtn.addEventListener('click', async () => {
            await this.app.scriptUpdateManager.saveScriptChanges(script.id, {
                name: document.getElementById('edit-script-name').value || script.name,
                category: categorySelect.value === 'new' ? newCategoryInput.value || '未分类' : categorySelect.value,
                icon: document.getElementById('edit-script-icon').value || script.icon
            });
        });
        
        // 显示模态框
        document.getElementById('modal-overlay').style.display = 'flex';
    }
}