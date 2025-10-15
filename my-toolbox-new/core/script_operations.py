"""
脚本操作管理器 - 负责脚本元数据更新和文件夹重命名等操作
"""
import ast
import os
from pathlib import Path
from typing import Dict, Any


class ScriptOperations:
    def __init__(self, user_preferences):
        self.user_preferences = user_preferences

    def update_script_metadata(self, script_id, metadata_changes, get_script_by_id_func):
        """使用 AST 安全地更新脚本文件中的元数据"""
        try:
            script = get_script_by_id_func(script_id)
            if not script:
                return {"success": False, "error": f"找不到脚本 {script_id}"}

            file_path = Path(script['file_path'])
            
            with open(file_path, 'r', encoding='utf-8') as f:
                source_code = f.read()

            tree = ast.parse(source_code)

            modifier = MetadataModifier(metadata_changes)
            new_tree = modifier.visit(tree)

            if not modifier.updated:
                # 如果不需要更新，可以提前返回或记录日志
                return {"success": True, "message": "元数据无需更新。"}

            new_source_code = ast.unparse(new_tree)

            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_source_code)

            return {"success": True, "message": "脚本元数据已更新。"}
        except Exception as e:
            return {"success": False, "error": f"更新脚本文件时出错: {e}"}

    def rename_script_folder(self, script_id, new_name, get_script_by_id_func):
        """
        重命名脚本文件夹,并正确更新ID映射表,保持脚本的稳定ID不变。
        """
        from pathlib import Path

        try:
            # 1. 使用稳定ID找到脚本对象
            script = get_script_by_id_func(script_id)
            if not script:
                return {"success": False, "error": f"找不到ID为 {script_id} 的脚本"}

            # 2. 获取当前的文件夹路径和名称
            current_folder_path = Path(script['file_path']).parent
            current_folder_name = current_folder_path.name

            # 3. 校验新名称
            clean_new_name = new_name.strip()
            if not clean_new_name:
                return {"success": False, "error": "新名称不能为空"}
            if clean_new_name == current_folder_name:
                return {"success": True, "message": "新旧名称相同，无需更改。"}

            invalid_chars = '<>:"/\\|?*'
            if any(char in clean_new_name for char in invalid_chars):
                return {"success": False, "error": f"名称不能包含非法字符: {invalid_chars}"}

            new_folder_path = current_folder_path.parent / clean_new_name
            if new_folder_path.exists():
                return {"success": False, "error": f"文件夹 '{clean_new_name}' 已存在"}

            # 4. 重命名文件系统中的文件夹
            current_folder_path.rename(new_folder_path)

            # 5. 更新 user_preferences 中的 id_mappings
            id_mappings = self.user_preferences.setdefault('id_mappings', {})
            # 删除旧的映射（如果存在）
            if current_folder_name in id_mappings:
                del id_mappings[current_folder_name]
            # 添加新的映射
            id_mappings[clean_new_name] = script_id

            # 6. 返回成功
            return {
                "success": True, 
                "message": f"脚本已重命名为 '{clean_new_name}'",
                "script_id": script_id,
                "new_name": clean_new_name
            }
        except Exception as e:
            # 简单的回滚尝试
            if 'new_folder_path' in locals() and 'current_folder_path' in locals():
                if new_folder_path.exists() and not current_folder_path.exists():
                    new_folder_path.rename(current_folder_path)
            return {"success": False, "error": f"重命名失败: {str(e)}"}

    def delete_script_folder(self, script_id, get_script_by_id_func):
        """永久删除脚本的整个文件夹"""
        import shutil
        try:
            script = get_script_by_id_func(script_id)
            if not script:
                return {"success": False, "error": f"找不到ID为 {script_id} 的脚本"}

            folder_path = Path(script['file_path']).parent
            if not folder_path.is_dir() or not folder_path.exists():
                return {"success": False, "error": f"脚本文件夹路径不存在: {folder_path}"}

            # 执行递归删除
            shutil.rmtree(folder_path)

            return {"success": True, "folder_path": str(folder_path)}
        except Exception as e:
            return {"success": False, "error": f"删除脚本文件夹时出错: {e}"}


class MetadataModifier(ast.NodeTransformer):
    """一个AST节点转换器，用于查找并修改get_metadata函数中的返回字典"""
    def __init__(self, changes):
        self.changes = changes
        self.updated = False

    def visit_FunctionDef(self, node):
        # 只关心名为 get_metadata 的函数
        if node.name == 'get_metadata':
            # 遍历函数体，寻找 return 语句
            for i, body_item in enumerate(node.body):
                if isinstance(body_item, ast.Return) and isinstance(body_item.value, ast.Dict):
                    self._modify_dict_node(body_item.value)
                    self.updated = True
                    break # 假设只有一个 return dict
        return self.generic_visit(node)

    def _modify_dict_node(self, dict_node):
        existing_keys = {key.value for key in dict_node.keys if isinstance(key, ast.Constant)}

        # 更新或添加键值对
        for change_key, change_value in self.changes.items():
            if change_key in existing_keys:
                # 更新现有键的值
                for i, key_node in enumerate(dict_node.keys):
                    if isinstance(key_node, ast.Constant) and key_node.value == change_key:
                        dict_node.values[i] = ast.Constant(value=change_value)
                        break
            else:
                # 添加新键值对
                dict_node.keys.append(ast.Constant(value=change_key))
                dict_node.values.append(ast.Constant(value=change_value))