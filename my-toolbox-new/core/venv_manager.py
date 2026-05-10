"""
虚拟环境管理器 - 负责所有虚拟环境的创建、管理和依赖操作
"""
import os
import sys
import subprocess
from pathlib import Path
import json
import shutil
from typing import Optional
from packaging.requirements import Requirement
from packaging.version import parse as parse_version


class VenvManager:
    def __init__(self, base_dir):
        self._venvs_dir = base_dir / "venvs"
        self._venvs_dir.mkdir(exist_ok=True)
        self._config_file = self._venvs_dir / "venvs.json"
        self.venvs_config = self._load_config()
        self._ensure_default_venv()

    def _load_config(self):
        """加载或创建虚拟环境配置文件"""
        if self._config_file.exists():
            try:
                with open(self._config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    # 【重要修复】动态重映射所有虚拟环境的路径，确保它们始终相对于当前项目位置
                    if 'venvs' in config:
                        for venv_name, venv_info in config['venvs'].items():
                            correct_path = self._venvs_dir / venv_name
                            venv_info['path'] = str(correct_path)
                    return config
            except (json.JSONDecodeError, IOError):
                # 如果文件损坏或无法读取，则创建备份并重新生成
                self._config_file.rename(self._config_file.with_suffix('.json.bak'))
        
        # 默认配置结构
        config = {
            "venvs": {
                "default": {"path": str(self._venvs_dir / "default"), "editable": False}
            }
        }
        self._save_config(config)
        return config

    def _save_config(self, config):
        """保存配置文件"""
        with open(self._config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4)

    def _ensure_default_venv(self):
        """确保默认虚拟环境存在，如果不存在或损坏则创建它"""
        default_venv_info = self.venvs_config['venvs']['default']
        default_venv_path = Path(default_venv_info['path'])
        python_executable = self._get_python_executable_path(default_venv_path)
        pip_executable = self._get_pip_executable_path(default_venv_path)

        if not python_executable.exists() or not pip_executable.exists():
            print(f"默认虚拟环境不存在或已损坏，正在重新创建于: {default_venv_path}")
            try:
                # 使用 --clear 标志可以安全地覆盖不完整的环境
                subprocess.run(
                    [sys.executable, "-m", "venv", "--clear", str(default_venv_path)],
                    capture_output=True, text=True, check=True, encoding='utf-8'
                )
                # 确保 pip 被安装和更新
                subprocess.run(
                    [str(python_executable), "-m", "ensurepip", "--upgrade"],
                    capture_output=True, text=True, check=True, encoding='utf-8'
                )
                print("默认虚拟环境创建/修复成功。")
            except (subprocess.CalledProcessError, FileNotFoundError) as e:
                print(f"创建默认虚拟环境时出错: {e}")
                if isinstance(e, subprocess.CalledProcessError):
                    print(f"错误详情: {e.stderr}")

    def _get_python_executable_path(self, venv_path: Path) -> Path:
        """获取虚拟环境中 Python 解释器的路径"""
        if sys.platform == "win32":
            return venv_path / "Scripts" / "python.exe"
        else:
            return venv_path / "bin" / "python"

    def _get_pip_executable_path(self, venv_path: Path) -> Path:
        """获取虚拟环境中 pip 的路径"""
        if sys.platform == "win32":
            return venv_path / "Scripts" / "pip.exe"
        else:
            return venv_path / "bin" / "pip"

    def list_packages(self, venv_name: str):
        """列出指定虚拟环境中已安装的包"""
        if venv_name not in self.venvs_config['venvs']:
            return {"success": False, "error": "虚拟环境不存在。"}

        venv_path = Path(self.venvs_config['venvs'][venv_name]['path'])
        pip_executable = self._get_pip_executable_path(venv_path)

        if not pip_executable.exists():
            return {"success": False, "error": "未在该虚拟环境中找到 pip。"}

        try:
            # 使用 python -m pip 可以避免直接调用 pip.exe 可能遇到的路径问题
            python_executable = self._get_python_executable_path(venv_path)
            result = subprocess.run(
                [str(python_executable), "-m", "pip", "list", "--format=json"],
                capture_output=True, text=True, check=True, encoding='utf-8'
            )
            packages = json.loads(result.stdout)
            return {"success": True, "packages": packages}
        except (subprocess.CalledProcessError, FileNotFoundError, json.JSONDecodeError) as e:
            error_message = f"列出包时出错: {e}"
            if isinstance(e, subprocess.CalledProcessError):
                error_message += f"\n错误详情: {e.stderr}"
            return {"success": False, "error": error_message}

    def install_package(self, venv_name: str, package_spec: str):
        """构建用于安装包的命令列表"""
        if venv_name not in self.venvs_config['venvs']:
            return None
        python_executable = self.get_python_executable_for_venv(venv_name)
        if not python_executable:
            return None
        return [str(python_executable), "-m", "pip", "install", "--upgrade", package_spec]

    def uninstall_package(self, venv_name: str, package_name: str):
        """构建用于卸载包的命令列表"""
        if venv_name not in self.venvs_config['venvs']:
            return None
        python_executable = self.get_python_executable_for_venv(venv_name)
        if not python_executable:
            return None
        return [str(python_executable), "-m", "pip", "uninstall", package_name, "-y"]

    def check_dependencies(self, venv_name: str, requirements: list[str]):
        """检查指定环境是否满足依赖需求"""
        list_result = self.list_packages(venv_name)
        if not list_result['success']:
            return list_result

        installed_packages = {pkg['name'].lower().replace('_', '-'): pkg['version'] for pkg in list_result['packages']}
        
        status_list = []
        for req_str in requirements:
            try:
                req = Requirement(req_str)
                # 标准化名称以进行比较 (小写并用连字符)
                normalized_req_name = req.name.lower().replace('_', '-')
                
                status = {
                    "requirement": req_str,
                    "name": req.name,
                    "status": "未安装",
                    "installed_version": None
                }

                if normalized_req_name in installed_packages:
                    installed_version_str = installed_packages[normalized_req_name]
                    installed_version = parse_version(installed_version_str)
                    status["installed_version"] = installed_version_str

                    if installed_version in req.specifier:
                        status["status"] = "已安装"
                    else:
                        status["status"] = "版本不匹配"
                
                status_list.append(status)

            except Exception as e:
                status_list.append({
                    "requirement": req_str,
                    "name": req_str, 
                    "status": "无效需求",
                    "error": str(e)
                })
        
        return {"success": True, "dependencies_status": status_list}

    def get_python_executable_for_venv(self, venv_name: str) -> Optional[str]:
        """获取指定虚拟环境的Python解释器路径"""
        venv_info = self.get_venvs().get(venv_name)
        if not venv_info:
            return None
        
        venv_path = Path(venv_info['path'])
        python_path = self._get_python_executable_path(venv_path)
        
        return str(python_path) if python_path.exists() else None

    def rename_venv(self, old_name: str, new_name: str):
        """重命名一个虚拟环境"""
        if old_name not in self.venvs_config['venvs'] or not self.venvs_config['venvs'][old_name].get('editable'):
            return {"success": False, "error": "该环境不存在或不可重命名。"}
        
        if not new_name or not new_name.isidentifier():
            return {"success": False, "error": "新名称无效。请使用有效的标识符。"}

        if new_name in self.venvs_config['venvs']:
            return {"success": False, "error": "该名称已存在。"}

        old_path = Path(self.venvs_config['venvs'][old_name]['path'])
        new_path = old_path.parent / new_name

        try:
            old_path.rename(new_path)
            venv_info = self.venvs_config['venvs'].pop(old_name)
            venv_info['path'] = str(new_path)
            self.venvs_config['venvs'][new_name] = venv_info
            self._save_config(self.venvs_config)
            return {"success": True}
        except OSError as e:
            return {"success": False, "error": f"重命名文件夹失败: {e}"}

    def delete_venv(self, venv_name: str):
        """删除一个虚拟环境"""
        if venv_name not in self.venvs_config['venvs'] or not self.venvs_config['venvs'][venv_name].get('editable'):
            return {"success": False, "error": "该环境不存在或不可删除。"}

        venv_path = Path(self.venvs_config['venvs'][venv_name]['path'])

        try:
            if venv_path.exists():
                shutil.rmtree(venv_path)
            
            del self.venvs_config['venvs'][venv_name]
            self._save_config(self.venvs_config)
            return {"success": True}
        except OSError as e:
            return {"success": False, "error": f"删除文件夹失败: {e}"}

    def get_venvs(self):
        """返回所有受管虚拟环境的信息，并清理无效条目"""
        config_changed = False
        # 创建一个副本进行迭代，因为我们可能会在循环中修改原始字典
        venvs_in_config = list(self.venvs_config.get('venvs', {}).items())

        for venv_name, venv_info in venvs_in_config:
            venv_path = Path(venv_info.get('path', ''))
            
            # 对于非默认环境，检查其路径是否有效
            if venv_name != 'default' and not venv_path.is_dir():
                print(f"检测到虚拟环境 '{venv_name}' 的文件夹不存在，将从配置中移除。")
                del self.venvs_config['venvs'][venv_name]
                config_changed = True

        if config_changed:
            self._save_config(self.venvs_config)

        return self.venvs_config.get('venvs', {})

    def create_venv(self, name: str):
        """构建用于创建新虚拟环境的系列命令"""
        if not name or not name.isidentifier():
            return {"success": False, "error": "名称无效。请使用有效的标识符（字母、数字、下划线），且不以数字开头。"}
        
        if name in self.venvs_config['venvs']:
            return {"success": False, "error": "该名称的虚拟环境已存在。"}

        venv_path = self._venvs_dir / name
        python_executable = self._get_python_executable_path(venv_path)

        commands = {
            "create": [sys.executable, "-m", "venv", str(venv_path)],
            "upgrade_pip": [str(python_executable), "-m", "ensurepip", "--upgrade"]
        }
        
        return {"success": True, "commands": commands, "path": str(venv_path)}
