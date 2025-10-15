document.addEventListener('DOMContentLoaded', () => {
    // --- DOM 元素获取 ---
    const venvManagementBtn = document.getElementById('venv-management-btn');
    const venvModalOverlay = document.getElementById('venv-modal-overlay');
    const venvModalCloseBtn = document.getElementById('venv-modal-close');
    const venvListContainer = document.getElementById('venv-list');
    const addVenvBtn = document.getElementById('add-venv-btn');
    const venvDetailsTitle = document.getElementById('venv-details-title');
    const venvPackagesList = document.getElementById('venv-packages-list');
    const addDependencyBtn = document.getElementById('add-dependency-btn');

    let activeVenvName = null;

    // --- 全局API，供Python调用 ---
    window.scriptVenvUI = {
        updateCreateLog(message) {
            const logContainer = document.getElementById('progress-modal-log');
            if (logContainer) {
                logContainer.innerHTML += `<p style="margin: 0; padding: 2px 0;">${message}</p>`;
                logContainer.scrollTop = logContainer.scrollHeight;
            }
        },
        onCreateVenvComplete(result) {
            const logContainer = document.getElementById('progress-modal-log');
            const progressModal = document.getElementById('progress-modal-overlay');

            if (result.success) {
                this.updateCreateLog(`<p style="color: lightgreen; margin-top: 10px;">✅ 环境 '${result.name}' 创建成功！</p>`);
                // 成功后，等待2秒自动关闭
                setTimeout(() => {
                    if (progressModal) progressModal.style.display = 'none';
                    loadAndRenderVenvs();
                }, 2000);
            } else {
                this.updateCreateLog(`<p style="color: red; margin-top: 10px;">❌ 创建失败: ${result.error}</p>`);
                // 失败后，添加一个关闭按钮
                const closeBtn = document.createElement('button');
                closeBtn.textContent = '关闭';
                closeBtn.className = 'btn btn-primary';
                closeBtn.style.marginTop = '15px';
                closeBtn.onclick = () => { progressModal.style.display = 'none'; };
                if (logContainer) logContainer.appendChild(closeBtn);
            }
            // 重新激活主窗口的创建按钮
            document.getElementById('add-venv-btn').disabled = false;
        },
        updateInstallLog(line) {
            const logContainer = document.getElementById('deps-status-container');
            if (logContainer) {
                // 移除“正在发送指令”的初始消息
                const initialMsg = logContainer.querySelector('.loading-msg');
                if (initialMsg) initialMsg.remove();
                
                logContainer.innerHTML += line.replace(/\n/g, '<br>');
                logContainer.scrollTop = logContainer.scrollHeight; // 自动滚动到底部
            }
        },
        onInstallComplete(result, venvName) {
            // 尝试更新脚本配置弹窗中的“迷你终端”
            const logContainer = document.getElementById('deps-status-container');
            if (logContainer && logContainer.style.backgroundColor === 'rgb(30, 30, 30)') { // 检查是否是终端模式
                if (result.success) {
                    logContainer.innerHTML += '<br><p style="color: lightgreen;">✅ 操作完成。</p>';
                } else {
                    logContainer.innerHTML += `<br><p style="color: red;">❌ 操作失败: ${result.error || '未知错误'}</p>`;
                }
                logContainer.scrollTop = logContainer.scrollHeight;
                const checkBtn = document.getElementById('check-deps-btn');
                if(checkBtn) checkBtn.disabled = false;
            }

            // 同时，检查是否需要刷新主环境管理窗口的包列表
            const venvModalOverlay = document.getElementById('venv-modal-overlay');
            if (venvModalOverlay.style.display === 'flex' && venvName === activeVenvName) {
                loadAndRenderPackages(venvName);
            }

            // 如果操作失败，用弹窗提示用户
            if (!result.success) {
                alert(`操作失败: ${result.error || '未知错误'}`);
            }
        }
    };

    // --- 事件监听 ---
    venvManagementBtn.addEventListener('click', () => openVenvModal());
    venvModalCloseBtn.addEventListener('click', () => closeVenvModal());
    venvModalOverlay.addEventListener('click', (e) => {
        if (e.target === venvModalOverlay) closeVenvModal();
    });
    addVenvBtn.addEventListener('click', () => createNewVenv());

    venvListContainer.addEventListener('click', (e) => {
        const venvItem = e.target.closest('.venv-item');
        const renameBtn = e.target.closest('.rename-venv-btn');
        const deleteBtn = e.target.closest('.delete-venv-btn');

        if (renameBtn) {
            e.stopPropagation(); // 防止触发选中事件
            const venvName = renameBtn.closest('.venv-item').dataset.venvName;
            renameVenv(venvName);
        } else if (deleteBtn) {
            e.stopPropagation(); // 防止触发选中事件
            const venvName = deleteBtn.closest('.venv-item').dataset.venvName;
            deleteVenv(venvName);
        } else if (venvItem) {
            selectVenv(venvItem.dataset.venvName);
        }
    });

    addDependencyBtn.addEventListener('click', () => addDependency());

    venvPackagesList.addEventListener('click', (e) => {
        const deleteBtn = e.target.closest('.btn-delete-pkg');
        if (deleteBtn) {
            const packageName = deleteBtn.dataset.packageName;
            deletePackage(packageName);
        }
    });

    // --- 函数定义 ---

    async function openVenvModal() {
        venvModalOverlay.style.display = 'flex';
        await loadAndRenderVenvs();
        if (venvListContainer.querySelector('.venv-item')) {
            const firstVenvName = venvListContainer.querySelector('.venv-item').dataset.venvName;
            if (!activeVenvName) {
                selectVenv(firstVenvName);
            }
        }
    }

    function closeVenvModal() {
        venvModalOverlay.style.display = 'none';
    }

    async function loadAndRenderVenvs() {
        // ... (代码无变化，为简洁省略)
    }

    async function createNewVenv() {
        // ... (代码无变化，为简洁省略)
    }

    function selectVenv(venvName) {
        // ... (代码无变化，为简洁省略)
    }

    async function loadAndRenderPackages(venvName) {
        // ... (代码无变化，为简洁省略)
    }

    async function addDependency() {
        if (!activeVenvName) {
            alert("请先选择一个虚拟环境。");
            return;
        }
        const packageSpec = prompt(`为环境 "${activeVenvName}" 添加依赖：\n请输入包名（例如 requests 或 requests>=2.25.0）`);
        if (!packageSpec) return;

        venvPackagesList.innerHTML = `<p class="loading-msg">正在安装 ${packageSpec}，请稍候...</p>`;
        try {
            const result = await window.pywebview.api.install_package(activeVenvName, packageSpec);
            if (!result.success) {
                alert(`开始安装失败: ${result.error}`);
                loadAndRenderPackages(activeVenvName); // 失败时刷新回原列表
            }
        } catch (error) {
            alert(`发生未知错误: ${error}`);
            loadAndRenderPackages(activeVenvName);
        }
    }

    async function deletePackage(packageName) {
        if (!activeVenvName) return;

        if (confirm(`确定要在环境 "${activeVenvName}" 中卸载 "${packageName}" 吗？`)) {
            venvPackagesList.innerHTML = `<p class="loading-msg">正在卸载 ${packageName}，请稍候...</p>`;
            try {
                const result = await window.pywebview.api.uninstall_package(activeVenvName, packageName);
                if (!result.success) {
                    alert(`开始卸载失败: ${result.error}`);
                    loadAndRenderPackages(activeVenvName);
                }
            } catch (error) {
                alert(`发生未知错误: ${error}`);
                loadAndRenderPackages(activeVenvName);
            }
        }
    }

    // --- 将部分函数定义替换为完整版 ---
    async function loadAndRenderVenvs() {
        try {
            const venvs = await window.pywebview.api.get_venvs();
            venvListContainer.innerHTML = '';

            if (!venvs || Object.keys(venvs).length === 0) {
                venvListContainer.innerHTML = '<p class="empty-list-msg">未找到环境</p>';
                return;
            }

            const sortedVenvNames = Object.keys(venvs).sort((a, b) => {
                if (a === 'default') return -1;
                if (b === 'default') return 1;
                return a.localeCompare(b);
            });

            for (const venvName of sortedVenvNames) {
                const venv = venvs[venvName];
                const venvItem = document.createElement('div');
                venvItem.className = 'venv-item';
                venvItem.dataset.venvName = venvName;
                
                let actionsHtml = venv.editable ? `
                    <div class="venv-item-actions">
                        <button class="rename-venv-btn" title="重命名">✏️</button>
                        <button class="delete-venv-btn" title="删除">🗑️</button>
                    </div>` : '';

                venvItem.innerHTML = `<span class="venv-item-name">${venvName}</span>${actionsHtml}`;
                venvListContainer.appendChild(venvItem);
            }
        } catch (error) {
            console.error('加载虚拟环境列表失败:', error);
            venvListContainer.innerHTML = `<p class="error-msg">加载失败: ${error}</p>`;
        }
    }

    async function createNewVenv() {
        const venvName = prompt('请输入新虚拟环境的名称（仅限字母、数字、下划线）:');
        if (!venvName) return;

        // 禁用主窗口的创建按钮
        addVenvBtn.disabled = true;

        // 准备并显示进度弹窗
        const progressModal = document.getElementById('progress-modal-overlay');
        const logContainer = document.getElementById('progress-modal-log');
        
        logContainer.innerHTML = '<p style="margin: 0; padding: 2px 0;">正在初始化创建任务...</p>';
        progressModal.style.display = 'flex';

        // 调用后端API，无需等待
        window.pywebview.api.create_venv(venvName);
    }

    function selectVenv(venvName) {
        activeVenvName = venvName;
        document.querySelectorAll('.venv-item').forEach(item => {
            item.classList.toggle('active', item.dataset.venvName === venvName);
        });
        venvDetailsTitle.textContent = venvName;
        loadAndRenderPackages(venvName);
    }

    async function loadAndRenderPackages(venvName) {
        venvPackagesList.innerHTML = '<p class="loading-msg">正在加载依赖包...</p>';
        try {
            const result = await window.pywebview.api.list_venv_packages(venvName);
            if (!result.success) throw new Error(result.error);

            const packages = result.packages;
            venvPackagesList.innerHTML = '';

            if (packages.length === 0) {
                venvPackagesList.innerHTML = '<p class="empty-list-msg">该环境没有安装任何依赖包。</p>';
                return;
            }

            for (const pkg of packages) {
                const packageItem = document.createElement('div');
                packageItem.className = 'package-item';
                packageItem.innerHTML = `
                    <div>
                        <span class="package-name">${pkg.name}</span>
                        <span class="package-version">${pkg.version}</span>
                    </div>
                    <button class="btn-delete-pkg" data-package-name="${pkg.name}" title="卸载 ${pkg.name}">🗑️</button>
                `;
                venvPackagesList.appendChild(packageItem);
            }
        } catch (error) {
            console.error(`加载 ${venvName} 的包列表失败:`, error);
            venvPackagesList.innerHTML = `<p class="error-msg">加载依赖包失败: ${error.message}</p>`;
        }
    }

    async function renameVenv(oldName) {
        const newName = prompt(`重命名环境 "${oldName}":`, oldName);
        if (!newName || newName === oldName) return;

        try {
            const result = await window.pywebview.api.rename_venv(oldName, newName);
            if (result.success) {
                alert("重命名成功！");
                await loadAndRenderVenvs();
                selectVenv(newName); // 选中重命名后的环境
            } else {
                alert(`重命名失败: ${result.error}`);
            }
        } catch (e) {
            alert(`发生错误: ${e}`);
        }
    }

    async function deleteVenv(venvName) {
        if (confirm(`确定要删除环境 "${venvName}" 吗？\n此操作将永久删除文件夹，且不可恢复！`)) {
            try {
                            const result = await window.pywebview.api.delete_venv(venvName);
                            if (result.success) {
                                // alert("删除成功！"); // 移除多余的成功弹窗
                                activeVenvName = null; // 清除当前选择
                                venvDetailsTitle.textContent = '选择一个环境';
                                venvPackagesList.innerHTML = '';
                                await loadAndRenderVenvs();                } else {
                    alert(`删除失败: ${result.error}`);
                }
            } catch (e) {
                alert(`发生错误: ${e}`);
            }
        }
    }
});