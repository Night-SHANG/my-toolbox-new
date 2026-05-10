"""
脚本操作管理器 - 负责脚本元数据更新和文件夹重命名等操作
"""
import ast
import os
import pprint
from pathlib import Path
from typing import Dict, Any


class ScriptOperations:
    def __init__(self, user_preferences):
        self.user_preferences = user_preferences

    def update_script_metadata(self, script_id, metadata_changes, get_script_by_id_func):
        """
        精准替换脚本文件中 get_metadata() 返回字典的指定键值。
        只修改字典中需要变更的部分，完美保留文件中所有注释、空行和代码格式。
        """
        try:
            script = get_script_by_id_func(script_id)
            if not script:
                return {"success": False, "error": f"找不到脚本 {script_id}"}

            file_path = Path(script['file_path'])

            with open(file_path, 'r', encoding='utf-8') as f:
                source_code = f.read()

            # 第一步：用 AST 定位 get_metadata 函数中 return 字典的行号范围
            tree = ast.parse(source_code)
            dict_node = None
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name == 'get_metadata':
                    for body_item in node.body:
                        if isinstance(body_item, ast.Return) and isinstance(body_item.value, ast.Dict):
                            dict_node = body_item.value
                            break
                    break

            if dict_node is None:
                return {"success": True, "message": "未找到 get_metadata 的 return 字典，无需更新。"}

            # 第二步：从 AST 字典节点中读取当前的键值对
            current_metadata = ast.literal_eval(dict_node)
            if not isinstance(current_metadata, dict):
                return {"success": False, "error": "get_metadata 返回值不是字典类型。"}

            # 检查是否真的需要修改
            needs_update = False
            for key, value in metadata_changes.items():
                if current_metadata.get(key) != value:
                    needs_update = True
                    break

            if not needs_update:
                return {"success": True, "message": "元数据无需更新。"}

            # 第三步：应用变更，生成新的字典字符串
            current_metadata.update(metadata_changes)
            new_dict_str = pprint.pformat(current_metadata, width=120)

            # 第四步：精准替换 - 只替换 return 字典所在的行，保留文件其余所有内容
            lines = source_code.splitlines(True)  # 保留换行符
            start_line = dict_node.lineno - 1       # AST 行号是 1-indexed
            end_line = dict_node.end_lineno - 1

            # 获取 return 字典前的缩进（保持原始缩进）
            original_line = lines[start_line]
            indent = original_line[:len(original_line) - len(original_line.lstrip())]

            # 构建替换内容：保持原始缩进 + 新字典 + 换行符
            # 确定换行符风格
            line_ending = '\r\n' if '\r\n' in source_code else '\n'
            
            # pprint.pformat 输出多行时，需要给每行都加上函数体缩进
            dict_lines = new_dict_str.split('\n')
            indented_lines = [indent + 'return ' + dict_lines[0]]
            for extra_line in dict_lines[1:]:
                indented_lines.append(indent + extra_line)
            new_dict_block = line_ending.join(indented_lines) + line_ending

            # 执行替换：删除旧行，插入新行
            new_lines = lines[:start_line] + [new_dict_block] + lines[end_line + 1:]
            new_source_code = ''.join(new_lines)

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