"""
API层 - 处理GUI与核心功能之间的通信
"""
import threading
import json
import subprocess
import sys
from pathlib import Path
from core.script_manager import ScriptManager
from core.process_runner import ProcessRunner
from core.venv_manager import VenvManager


class Api:
    def __init__(self):
        self._base_dir = Path(__file__).parent.parent  # 项目根目录
        self.script_manager = ScriptManager()
        self.process_runner = ProcessRunner()
        # 将 VenvManager 初始化放在这里
        self.venv_manager = VenvManager(base_dir=self._base_dir)
        self._window = None  # 使用私有属性防止被暴露到前端

    def set_window(self, window):
        """设置窗口对象（避免在初始化时直接暴露复杂对象）"""
        self._window = window

    def get_scripts(self):
        """获取所有脚本信息"""
        return self.script_manager.get_all_scripts()

    def execute_script(self, script_id, params=None):
        """
        执行指定脚本
        :param script_id: 脚本ID
        :param params: 脚本参数
        """
        script = self.script_manager.get_script_by_id(script_id)
        if not script:
            error_msg = f'<span style="color:red;">错误：找不到脚本 {script_id}</span><br>'
            if self._window:
                self._window.evaluate_js(f'updateTerminal({repr(error_msg)})')
            return

        # 在新线程中执行脚本，避免阻塞GUI
        thread = threading.Thread(
            target=self._execute_script_thread, 
            args=(script, params or {})
        )
        thread.start()

    def _execute_script_thread(self, script, params):
        """在新线程中执行脚本，并管理其进程"""
        try:
            venv_name = self.script_manager.get_user_preferences().get('scripts', {}).get(script['id'], {}).get('venv', 'default')
            python_executable = self.venv_manager.get_python_executable_for_venv(venv_name)
            if not python_executable:
                raise FileNotFoundError(f"在虚拟环境 '{venv_name}' 中未找到 Python 解释器。")

            command_parts = self.script_manager.build_command(script, params)
            final_command = [python_executable] + command_parts

            if self._window:
                # 启动进程并保存进程对象
                self.script_process = self.process_runner.run_script(final_command, self._window)
                if self.script_process:
                    # 等待进程结束
                    self.script_process.wait()

        except Exception as e:
            error_msg = f'<span style="color:red;">执行脚本时发生错误: {str(e)}</span><br>'
            if self._window:
                self._window.evaluate_js(f'updateTerminal({json.dumps(error_msg)})')
        finally:
            # 任务结束后，清除进程引用
            self.script_process = None

    def terminate_current_script(self):
        """终止当前正在运行的脚本进程"""
        if self.process_runner.shutdown():
            return {"success": True, "message": "终止信号已发送。"}
        else:
            return {"success": False, "error": "没有正在运行的脚本任务。"}

    def get_script_categories(self):
        """获取脚本分类"""
        return self.script_manager.get_categories()

    def search_scripts(self, query):
        """搜索脚本"""
        return self.script_manager.search_scripts(query)

    def get_user_preferences(self):
        """获取用户偏好设置"""
        return self.script_manager.get_user_preferences()

    def save_user_preferences(self, preferences):
        """保存用户偏好设置"""
        return self.script_manager.save_user_preferences(preferences)

    def save_script_order(self, script_order):
        """保存脚本排序"""
        return self.script_manager.save_script_order(script_order)

    def get_script_order(self):
        """获取脚本排序"""
        return self.script_manager.get_script_order()

    def save_category_order(self, category_order):
        """保存分类排序"""
        return self.script_manager.save_category_order(category_order)

    def get_category_order(self):
        """获取分类排序"""
        return self.script_manager.get_category_order()

    def open_script_folder(self, file_path):
        """打开脚本所在文件夹"""
        import os
        import subprocess
        import sys
        
        folder_path = os.path.dirname(file_path)
        try:
            if sys.platform == "win32":
                os.startfile(folder_path)
            elif sys.platform == "darwin":  # macOS
                subprocess.run(["open", folder_path])
            else:  # Linux
                subprocess.run(["xdg-open", folder_path])
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_default_icons(self):
        """获取默认图标列表"""
        import os
        from pathlib import Path
        
        icons_dir = Path(__file__).parent.parent / "assets" / "icons"
        if not icons_dir.exists():
            icons_dir.mkdir(parents=True, exist_ok=True)
        
        icons = []
        for icon_file in icons_dir.glob("*.ico"):
            icons.append(str(icon_file))
        for icon_file in icons_dir.glob("*.png"):
            icons.append(str(icon_file))
        for icon_file in icons_dir.glob("*.jpg"):
            icons.append(str(icon_file))
        for icon_file in icons_dir.glob("*.jpeg"):
            icons.append(str(icon_file))
        for icon_file in icons_dir.glob("*.gif"):
            icons.append(str(icon_file))
        for icon_file in icons_dir.glob("*.svg"):
            icons.append(str(icon_file))
        
        return {"success": True, "icons": icons}
    
    def get_script_folder_icons(self, script_file_path):
        """获取脚本所在文件夹的图标"""
        import os
        from pathlib import Path
        
        script_folder = Path(script_file_path).parent
        icons = []
        
        for icon_file in script_folder.glob("*.ico"):
            icons.append(str(icon_file))
        for icon_file in script_folder.glob("*.png"):
            icons.append(str(icon_file))
        for icon_file in script_folder.glob("*.jpg"):
            icons.append(str(icon_file))
        for icon_file in script_folder.glob("*.jpeg"):
            icons.append(str(icon_file))
        for icon_file in script_folder.glob("*.gif"):
            icons.append(str(icon_file))
        for icon_file in script_folder.glob("*.svg"):
            icons.append(str(icon_file))
        
        return {"success": True, "icons": icons}

    def add_custom_category(self, category_name):
        """添加自定义分类"""
        return self.script_manager.add_custom_category(category_name)

    def remove_custom_category(self, category_name):
        """移除自定义分类"""
        return self.script_manager.remove_custom_category(category_name)

    def assign_script_to_category(self, script_id, category_name):
        """将脚本分配到指定分类"""
        return self.script_manager.assign_script_to_category(script_id, category_name)
    
    def update_script_metadata(self, script_id, metadata_changes):
        """更新脚本文件中的元数据"""
        return self.script_manager.update_script_metadata(script_id, metadata_changes)
    
    def rename_script_folder(self, script_id, new_name):
        """重命名脚本文件夹"""
        return self.script_manager.rename_script_folder(script_id, new_name)

    def delete_script(self, script_id):
        """删除一个脚本（包括文件和配置）"""
        return self.script_manager.delete_script(script_id)


    def open_file_dialog(self):
        """打开文件选择对话框"""
        try:
            # 检查窗口对象是否存在
            if not hasattr(self, '_window') or self._window is None:
                return {"success": False, "error": "Window object not available"}
            
            # 使用窗口对象的文件对话框功能
            result = self._window.create_file_dialog(
                dialog_type=10,  # OPEN_DIALOG
                directory=".",
                allow_multiple=False,
                file_types=('Image Files (*.ico;*.png;*.jpg;*.jpeg;*.gif;*.svg)',)
            )
            if result and len(result) > 0:
                if isinstance(result, (list, tuple)):
                    return {"success": True, "file_path": result[0]}
                else:
                    return {"success": True, "file_path": result}
            else:
                return {"success": False, "error": "No file selected"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_script_icon(self, script_file_path):
        """获取脚本的图标路径"""
        import os
        from pathlib import Path
        from core.icon_manager import IconManager
        
        script_path = Path(script_file_path)
        script_folder = script_path.parent
        
        icon_manager = IconManager(Path(__file__).parent.parent)
        icon_path = icon_manager.get_script_icon(script_folder)
        
        return {"success": True, "icon_path": icon_path}
    
    def get_icon_as_base64(self, icon_path):
        """将图标文件转换为base64格式以供前端显示"""
        import base64
        from pathlib import Path
        
        try:
            icon_file = Path(icon_path)
            # 【重要修复】如果路径是相对路径，则基于项目根目录拼接成绝对路径
            if not icon_file.is_absolute():
                icon_file = self._base_dir / icon_file

            if not icon_file.exists():
                return {"success": False, "error": "图标文件不存在"}
            
            # 检测文件类型
            mime_type = self._get_mime_type(icon_file.suffix.lower())
            if not mime_type:
                return {"success": False, "error": f"不支持的文件类型: {icon_file.suffix}"}
            
            with open(icon_file, 'rb') as f:
                file_content = f.read()
                base64_content = base64.b64encode(file_content).decode('utf-8')
                
            return {
                "success": True, 
                "base64_data": f"data:{mime_type};base64,{base64_content}",
                "mime_type": mime_type
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _get_mime_type(self, file_extension):
        """获取文件扩展名对应的MIME类型"""
        mime_types = {
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.gif': 'image/gif',
            '.ico': 'image/x-icon',
            '.svg': 'image/svg+xml'
        }
        return mime_types.get(file_extension, None)

    # --- 虚拟环境管理 API ---

    def get_venvs(self):
        """获取所有虚拟环境的列表"""
        return self.venv_manager.get_venvs()

    def _create_venv_thread(self, name):
        """在后台线程中分步创建虚拟环境并提供反馈"""
        # 步骤0: 获取命令
        result = self.venv_manager.create_venv(name)
        if not result['success']:
            if self._window:
                self._window.evaluate_js(f'window.scriptVenvUI.onCreateVenvComplete({json.dumps(result)})')
            return

        commands = result['commands']
        venv_path = result['path']

        try:
            # 步骤1: 创建基础环境
            if self._window:
                self._window.evaluate_js(f'window.scriptVenvUI.updateCreateLog("正在创建基础环境...")')
            subprocess.run(commands['create'], capture_output=True, text=True, check=True, encoding='utf-8')

            # 步骤2: 更新PIP
            if self._window:
                self._window.evaluate_js(f'window.scriptVenvUI.updateCreateLog("正在联网更新 pip...")')
            subprocess.run(commands['upgrade_pip'], capture_output=True, text=True, check=True, encoding='utf-8')

            # 步骤3: 更新配置文件并通知成功
            self.venv_manager.venvs_config['venvs'][name] = {"path": venv_path, "editable": True}
            self.venv_manager._save_config(self.venv_manager.venvs_config)
            
            final_result = {"success": True, "name": name}
            if self._window:
                self._window.evaluate_js(f'window.scriptVenvUI.onCreateVenvComplete({json.dumps(final_result)})')

        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            error_message = str(e)
            if isinstance(e, subprocess.CalledProcessError):
                error_message += f"\n{e.stderr}"
            final_result = {"success": False, "error": error_message}
            if self._window:
                self._window.evaluate_js(f'window.scriptVenvUI.onCreateVenvComplete({json.dumps(final_result)})')

    def create_venv(self, name):
        """在新线程中创建虚拟环境"""
        thread = threading.Thread(target=self._create_venv_thread, args=(name,))
        thread.start()
        return {"success": True, "message": "创建任务已开始..."}

    def list_venv_packages(self, venv_name):
        """列出指定虚拟环境中的包"""
        return self.venv_manager.list_packages(venv_name)

    def _package_operation_thread(self, operation, venv_name, package_name):
        """在线程中执行包操作并流式传输输出"""
        command = []
        if operation == 'install':
            command = self.venv_manager.install_package(venv_name, package_name)
        else: # uninstall
            command = self.venv_manager.uninstall_package(venv_name, package_name)

        if not command:
            result = {"success": False, "error": "无法构建命令，可能是环境不存在。"}
            if self._window:
                self._window.evaluate_js(f'window.scriptVenvUI.onInstallComplete({json.dumps(result)})')
            return

        try:
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding='utf-8',
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
                bufsize=1
            )

            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output and self._window:
                    self._window.evaluate_js(f'window.scriptVenvUI.updateInstallLog({json.dumps(output)})')
            
            process.stdout.close()
            return_code = process.wait()
            result = {"success": return_code == 0}
            if self._window:
                self._window.evaluate_js(f'window.scriptVenvUI.onInstallComplete({json.dumps(result)}, "{venv_name}")')

        except Exception as e:
            result = {"success": False, "error": str(e)}
            if self._window:
                self._window.evaluate_js(f'window.scriptVenvUI.onInstallComplete({json.dumps(result)}, "{venv_name}")')

    def install_package(self, venv_name, package_spec):
        """在新线程中安装一个包"""
        thread = threading.Thread(
            target=self._package_operation_thread, 
            args=('install', venv_name, package_spec)
        )
        thread.start()
        return {"success": True, "message": "安装任务已开始..."}

    def uninstall_package(self, venv_name, package_name):
        """在新线程中卸载一个包"""
        thread = threading.Thread(
            target=self._package_operation_thread, 
            args=('uninstall', venv_name, package_name)
        )
        thread.start()
        return {"success": True, "message": "卸载任务已开始..."}

    def check_script_dependencies(self, script_id, venv_name):
        """检查脚本在指定环境中的依赖满足状态"""
        script = self.script_manager.get_script_by_id(script_id)
        if not script:
            return {"success": False, "error": "找不到脚本"}
        
        requirements = script.get('dependencies', [])
        if not requirements:
            return {"success": True, "dependencies_status": []} # 没有依赖，直接返回成功
            
        return self.venv_manager.check_dependencies(venv_name, requirements)

    def rename_venv(self, old_name, new_name):
        """重命名虚拟环境"""
        return self.venv_manager.rename_venv(old_name, new_name)

    def delete_venv(self, venv_name):
        """删除虚拟环境"""
        return self.venv_manager.delete_venv(venv_name)

    def show_file_dialog(self, options):
        """显示一个通用的文件/文件夹选择对话框"""
        if not self._window:
            return {"success": False, "error": "窗口对象不可用"}
        
        try:
            # pywebview.OPEN_DIALOG = 10, pywebview.FOLDER_DIALOG = 20, pywebview.SAVE_DIALOG = 30
            result = self._window.create_file_dialog(**options)
            return {"success": True, "files": result}
        except Exception as e:
            return {"success": False, "error": str(e)}
    def save_script_setting(self, script_id, key, value):
        """保存脚本的单个设置项"""
        # 【重要修复】如果设置的是图标路径，则转换为相对路径进行保存
        if key == 'icon' and value and Path(value).is_absolute():
            try:
                absolute_icon_path = Path(value)
                # 只有当图标路径在项目文件夹内时，才转换为相对路径
                relative_icon_path = absolute_icon_path.relative_to(self._base_dir)
                value = str(relative_icon_path).replace('\\', '/') # 统一使用 / 作为路径分隔符
            except ValueError:
                # 如果图标不在项目目录内（例如C:\Windows\...），则保持其绝对路径
                pass
        return self.script_manager.save_script_setting(script_id, key, value)

    def save_parameter_default(self, script_id, param_name, value):
        """保存特定脚本的特定参数的默认值"""
        return self.script_manager.save_parameter_default(script_id, param_name, value)

    def install_script_dependencies(self, script_id, venv_name):
        """安装指定脚本的所有缺失依赖到指定环境"""
        check_result = self.check_script_dependencies(script_id, venv_name)
        if not check_result.get('success'):
            return check_result

        missing_deps = [
            dep['requirement'] for dep in check_result.get('dependencies_status', []) 
            if dep['status'] != '已安装'
        ]

        if not missing_deps:
            return {"success": True, "message": "所有依赖均已满足。"}

        # 对于每个缺失的依赖，启动一个安装线程
        # 注意：为了简单起见，这里是串行启动。在实际应用中可能需要更复杂的任务管理。
        for dep in missing_deps:
            self.install_package(venv_name, dep)
        
        return {"success": True, "message": f"开始为 {len(missing_deps)} 个依赖项执行安装任务..."}

    def set_custom_script_icon(self, script_id, icon_path):
        """为脚本设置自定义图标"""
        from core.icon_manager import IconManager
        from pathlib import Path
        
        # 获取脚本信息
        script = self.script_manager.get_script_by_id(script_id)
        if not script:
            return {"success": False, "error": f"找不到脚本 {script_id}"}
        
        script_file_path = Path(script['file_path'])
        script_folder_path = script_file_path.parent
        
        icon_manager = IconManager(Path(__file__).parent.parent)
        result = icon_manager.set_custom_icon(script_folder_path, icon_path)
        
        if result["success"]:
            # 更新脚本元数据中的图标路径
            metadata_update = {"icon": result["icon_path"]}
            self.script_manager.update_script_metadata(script_id, metadata_update)
        
        return result