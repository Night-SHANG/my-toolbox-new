"""
脚本元数据管理器 - 负责脚本元数据处理
"""
import sys
from typing import Dict, Any


class ScriptMetadata:
    def __init__(self):
        pass

    def build_command(self, script: Dict[str, Any], params: Dict[str, Any]) -> list[str]:
        """构建执行命令的参数列表（不含python解释器）"""
        script_path = script['file_path']
        command_parts = [script_path]
        
        for param_def in script.get('parameters', []):
            param_name = param_def['name']
            if param_name in params:
                value = params[param_name]
                if param_def.get('type') == 'boolean':
                    if value:
                        command_parts.append(f"--{param_name}")
                else:
                    command_parts.append(f"--{param_name}")
                    command_parts.append(str(value))
        
        return command_parts