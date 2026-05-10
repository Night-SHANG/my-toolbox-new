"""
工具箱 CLI 入口 - 供 AI 通过命令行调用工具箱脚本
不修改任何现有工具箱代码，只读取现有配置文件。

用法：
    python cli.py list                    # 列出所有可用脚本
    python cli.py info <脚本文件夹名>      # 查看脚本详情和参数
    python cli.py venvs                   # 列出所有虚拟环境
    python cli.py run <脚本文件夹名> [参数] # 运行脚本
"""
import sys
import os
import json
import ast
import subprocess
import io
from pathlib import Path

# 强制 stdout 使用 UTF-8 编码（Windows CMD 默认 GBK 不支持 emoji）
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


# 工具箱根目录（cli.py 所在目录）
TOOLBOX_DIR = Path(__file__).parent.resolve()
SCRIPTS_DIR = TOOLBOX_DIR / "scripts"
VENVS_DIR = TOOLBOX_DIR / "venvs"
USER_PROFILE = TOOLBOX_DIR / "user_profile.json"
VENVS_CONFIG = VENVS_DIR / "venvs.json"


def load_json(filepath):
    """加载 JSON 文件"""
    if filepath.exists():
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def get_metadata_from_script(script_folder):
    """用 AST 解析脚本的 get_metadata() 返回值（不执行脚本代码）"""
    main_py = SCRIPTS_DIR / script_folder / "main.py"
    if not main_py.exists():
        return None

    try:
        source = main_py.read_text(encoding='utf-8')
        tree = ast.parse(source)

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == 'get_metadata':
                for child in ast.walk(node):
                    if isinstance(child, ast.Return) and child.value:
                        return ast.literal_eval(child.value)
    except Exception:
        return None
    return None


def get_venv_for_script(script_folder):
    """查询脚本使用的虚拟环境名称"""
    profile = load_json(USER_PROFILE)
    id_mappings = profile.get('id_mappings', {})
    scripts_config = profile.get('scripts', {})

    # 通过文件夹名找到脚本ID
    script_id = id_mappings.get(script_folder)
    if script_id and script_id in scripts_config:
        return scripts_config[script_id].get('venv', 'default')
    return 'default'


def get_python_executable(venv_name):
    """获取虚拟环境的 python.exe 路径"""
    venvs_config = load_json(VENVS_CONFIG)
    venvs = venvs_config.get('venvs', {})

    if venv_name in venvs:
        venv_path = Path(venvs[venv_name]['path'])
    else:
        venv_path = VENVS_DIR / venv_name

    python_path = venv_path / "Scripts" / "python.exe"
    if python_path.exists():
        return str(python_path)

    # 回退到默认环境
    default_python = VENVS_DIR / "default" / "Scripts" / "python.exe"
    if default_python.exists():
        return str(default_python)

    return sys.executable


def cmd_list():
    """列出所有可用脚本"""
    if not SCRIPTS_DIR.exists():
        print("❌ scripts 目录不存在")
        return

    scripts = []
    for folder in sorted(SCRIPTS_DIR.iterdir()):
        if not folder.is_dir():
            continue
        if not (folder / "main.py").exists():
            continue

        metadata = get_metadata_from_script(folder.name)
        if metadata:
            venv = get_venv_for_script(folder.name)
            name = metadata.get('name', folder.name)
            desc = metadata.get('description', '无描述')
            deps = metadata.get('dependencies', [])
            scripts.append({
                'folder': folder.name,
                'name': name,
                'description': desc,
                'venv': venv,
                'dependencies': deps
            })

    if not scripts:
        print("📭 没有发现任何脚本")
        return

    print(f"📦 共发现 {len(scripts)} 个脚本：\n")
    for s in scripts:
        print(f"  📌 {s['folder']}")
        print(f"     名称: {s['name']}")
        print(f"     描述: {s['description']}")
        print(f"     环境: {s['venv']}")
        if s['dependencies']:
            print(f"     依赖: {', '.join(s['dependencies'])}")
        print()


def cmd_info(script_folder):
    """查看脚本的详细信息和参数"""
    metadata = get_metadata_from_script(script_folder)
    if not metadata:
        print(f"❌ 未找到脚本: {script_folder}")
        return

    venv = get_venv_for_script(script_folder)
    print(f"📌 脚本: {script_folder}")
    print(f"   名称: {metadata.get('name', script_folder)}")
    print(f"   描述: {metadata.get('description', '无')}")
    print(f"   环境: {venv}")
    print(f"   依赖: {', '.join(metadata.get('dependencies', [])) or '无'}")
    print(f"   分类: {metadata.get('category', '未分类')}")
    print()

    params = metadata.get('parameters', [])
    if params:
        print(f"   参数列表 ({len(params)} 个):")
        for p in params:
            ptype = p.get('type', 'text')
            required = '必填' if p.get('required') else '可选'
            default = p.get('defaultValue', '')
            label = p.get('label', p['name'])
            print(f"     --{p['name']}  [{ptype}] ({required})")
            print(f"       标签: {label}")
            if default != '' and default is not None:
                print(f"       默认值: {default}")
            if ptype == 'choice':
                choices = p.get('choices', [])
                values = [c['value'] for c in choices]
                print(f"       可选值: {', '.join(values)}")
            if p.get('placeholder'):
                print(f"       提示: {p['placeholder']}")
    else:
        print("   无参数")

    # 打印用法示例
    print(f"\n   运行示例:")
    example = f'python cli.py run {script_folder}'
    for p in params:
        if p.get('required'):
            example += f' --{p["name"]} <值>'
    print(f"     {example}")


def cmd_venvs():
    """列出所有虚拟环境"""
    venvs_config = load_json(VENVS_CONFIG)
    venvs = venvs_config.get('venvs', {})

    if not venvs:
        print("📭 没有虚拟环境")
        return

    print(f"🐍 共 {len(venvs)} 个虚拟环境：\n")
    for name, info in venvs.items():
        path = info.get('path', '未知')
        editable = '可编辑' if info.get('editable') else '系统默认'
        python_path = Path(path) / "Scripts" / "python.exe"
        status = '✅' if python_path.exists() else '❌'
        print(f"  {status} {name} ({editable})")
        print(f"     路径: {path}")
        print()


def cmd_run(script_folder, extra_args):
    """运行脚本"""
    main_py = SCRIPTS_DIR / script_folder / "main.py"
    if not main_py.exists():
        print(f"❌ 未找到脚本: {script_folder}/main.py")
        sys.exit(1)

    venv_name = get_venv_for_script(script_folder)
    python_exe = get_python_executable(venv_name)

    print(f"🚀 运行脚本: {script_folder}")
    print(f"   虚拟环境: {venv_name}")
    print(f"   Python: {python_exe}")
    print(f"   参数: {' '.join(extra_args) if extra_args else '无'}")
    print(f"{'─' * 50}")

    cmd = [python_exe, str(main_py)] + extra_args
    result = subprocess.run(cmd, cwd=str(SCRIPTS_DIR / script_folder))
    sys.exit(result.returncode)


def cmd_snapshot(output_path):
    """生成脚本目录快照文件 (scripts_catalog.md)"""
    if not SCRIPTS_DIR.exists():
        print("❌ scripts 目录不存在")
        return

    lines = []
    lines.append("# 工具箱脚本目录\n")
    lines.append(f"> 工具箱路径: `{TOOLBOX_DIR}`\n")
    lines.append(f"> 生成时间: 请在脚本变更后重新运行 `python cli.py snapshot` 更新此文件\n")
    lines.append("---\n")

    script_count = 0
    for folder in sorted(SCRIPTS_DIR.iterdir()):
        if not folder.is_dir():
            continue
        if not (folder / "main.py").exists():
            continue

        metadata = get_metadata_from_script(folder.name)
        if not metadata:
            continue

        script_count += 1
        venv = get_venv_for_script(folder.name)
        name = metadata.get('name', folder.name)
        desc = metadata.get('description', '无描述')
        deps = metadata.get('dependencies', [])
        category = metadata.get('category', '未分类')
        params = metadata.get('parameters', [])

        lines.append(f"## {name}\n")
        lines.append(f"- **文件夹名**: `{folder.name}`")
        lines.append(f"- **描述**: {desc}")
        lines.append(f"- **虚拟环境**: `{venv}`")
        lines.append(f"- **分类**: {category}")
        if deps:
            lines.append(f"- **依赖**: {', '.join(deps)}")
        lines.append("")

        if params:
            lines.append("### 参数\n")
            lines.append("| 参数名 | 类型 | 必填 | 默认值 | 说明 |")
            lines.append("|:--|:--|:--|:--|:--|")
            for p in params:
                pname = p.get('name', '')
                ptype = p.get('type', 'text')
                required = '是' if p.get('required') else '否'
                default = p.get('defaultValue', '')
                if default == '' or default is None:
                    default = '-'
                label = p.get('label', pname)

                # choice 类型附加可选值
                extra = ''
                if ptype == 'choice':
                    choices = p.get('choices', [])
                    values = [c['value'] for c in choices]
                    extra = f" 可选: {', '.join(values)}"

                lines.append(f"| `--{pname}` | {ptype} | {required} | {default} | {label}{extra} |")
            lines.append("")

        # 运行示例（使用完整路径，确保任意目录下都能执行）
        cli_path = str(TOOLBOX_DIR / "cli.py")
        example = f'python "{cli_path}" run {folder.name}'
        for p in params:
            if p.get('required'):
                example += f' --{p["name"]} <值>'
        lines.append(f"**运行示例**: `{example}`\n")
        lines.append("---\n")

    # 写入文件
    content = '\n'.join(lines)
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"✅ 快照已生成: {output_file}")
    print(f"   包含 {script_count} 个脚本")

# 默认快照输出路径（工具箱根目录）
SNAPSHOT_DEFAULT_PATH = TOOLBOX_DIR / "scripts_catalog.md"


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return

    command = sys.argv[1].lower()

    if command == 'list':
        cmd_list()
    elif command == 'info':
        if len(sys.argv) < 3:
            print("用法: python cli.py info <脚本文件夹名>")
            return
        cmd_info(sys.argv[2])
    elif command == 'venvs':
        cmd_venvs()
    elif command == 'run':
        if len(sys.argv) < 3:
            print("用法: python cli.py run <脚本文件夹名> [--参数名 值 ...]")
            return
        cmd_run(sys.argv[2], sys.argv[3:])
    elif command == 'snapshot':
        output = sys.argv[2] if len(sys.argv) >= 3 else str(SNAPSHOT_DEFAULT_PATH)
        cmd_snapshot(output)
    else:
        print(f"❌ 未知命令: {command}")
        print(__doc__)


if __name__ == '__main__':
    main()

