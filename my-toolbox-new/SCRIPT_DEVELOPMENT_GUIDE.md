# 脚本开发指南 (Script Development Guide)

本文档旨在为“脚本工具箱”项目提供清晰、标准的脚本开发规范，以确保所有第三方脚本都能被工具箱正确识别、加载和执行。

## 1. 基本原则

- **独立性**: 每个脚本应被视为一个独立的单元，放置在自己的专属文件夹中。
- **声明式元数据**: 脚本必须通过一个固定的函数 `get_metadata()` 来“声明”自己的信息，而不是让工具箱去猜测。
- **标准输入输出**: 脚本通过标准命令行参数接收输入，并通过 `print()` 函数输出日志信息到工具箱的终端界面。

## 2. 文件夹与文件结构

工具箱只会在根目录下的 `scripts` 文件夹内寻找脚本。每一个脚本都**必须**遵循以下结构：

```
scripts/
└── my_awesome_script/      # 脚本的根文件夹，文件夹名将作为脚本的默认显示名称
    ├── main.py             # 必须！这是脚本的唯一入口文件
    ├── icon.png            # 可选。如果存在，将作为脚本的默认图标
    ├── helper.py           # 可选。其他的辅助模块
    └── some_data.txt       # 可选。脚本依赖的其他资源文件
```

- **脚本根文件夹**: 文件夹名应具有描述性，例如 `video_downloader`。
- **`main.py`**: 这是工具箱唯一会识别和执行的文件，所有核心逻辑都应从这里开始。

## 3. `get_metadata()` 函数详解

每个 `main.py` 文件都**必须**包含一个名为 `get_metadata()` 的函数。此函数不接受任何参数，且必须返回一个包含脚本元数据的**字典**。

工具箱会安全地解析这个函数，读取其返回值，但**不会**执行函数中的其他代码。

### 3.1. 元数据字典结构

一个完整的元数据字典示例如下：

```python
def get_metadata():
    return {
        'name': 'My Awesome Script',
        'description': '这是一个功能强大的脚本，能完成...',
        'author': 'Your Name',
        'version': '1.0.0',
        'dependencies': ['requests', 'pillow==9.0.0'],
        'parameters': [
            {
                'name': 'input_file',
                'label': '输入文件路径',
                'type': 'file',
                'required': True,
                'placeholder': '请选择一个要处理的文件'
            },
            {
                'name': 'quality',
                'label': '压缩质量',
                'type': 'number',
                'defaultValue': 80
            }
        ]
    }
```

### 3.2. 字段详细说明

| 键 (Key)       | 类型 (Type)          | 是否必须 | 描述                                                                                                                             |
|----------------|----------------------|----------|----------------------------------------------------------------------------------------------------------------------------------|
 | `name`         | `str`                | **是**   |                                             │                   │
 │       |
| `description`  | `str`                | 否       | 脚本功能的简短描述，会显示在UI上。                                                                                               |
| `dependencies` | `list[str]`          | 否       | 脚本运行所需的Python第三方库列表。工具箱可以根据此列表，在指定的虚拟环境中自动安装依赖。格式遵循 `pip` 要求，可指定版本。 |
| `parameters`   | `list[dict]`         | 否       | 脚本执行所需的参数列表。每个参数是一个字典，详见下文。                                                                           |
。

### 3.3. `parameters` 字段结构

`parameters` 列表中的每个字典用于在UI上生成一个输入控件。

| 键 (Key)         | 类型 (Type) | 是否必须 | 描述                                                                                                                               |
|------------------|-------------|----------|------------------------------------------------------------------------------------------------------------------------------------|
| `name`           | `str`       | **是**   | 参数的内部名称，将作为命令行参数的名称（例如 `name='input_file'` 会被转换为 `--input_file`）。必须是合法的变量名。             |
| `label`          | `str`       | 否       | 在UI上显示的参数标签。如果缺失，将自动使用 `name` 的值作为标签。                                                                 |
| `type`           | `str`       | **是**   | UI输入控件的类型。支持的值包括：<br> - `'text'` (单行文本)<br> - `'number'` (数字)<br> - `'file'` (文件选择)<br> - `'folder'` (文件夹选择)<br> - `'boolean'` (复选框)<br> - `'textarea'` (多行文本)<br> - `'choice'` (下拉选择框)。使用此类型时，需额外提供一个 `choices` 字段，例如 `'choices': [{'value': 'val1', 'label': '选项1'}, ...]` |                                                                                                |
| `required`       | `bool`      | 否       | 此参数是否为必填项。默认为 `False`。                                                                                               |
| `defaultValue`   | `any`       | 否       | 参数的默认值。                                                                                                                     |
| `placeholder`    | `str`       | 否       | 当输入框为空时显示的提示性文本。                                                                                                   |

## 4. 接收与解析参数

工具箱会根据 `parameters` 的定义，将用户输入的值通过标准命令行参数传递给 `main.py`。

脚本内部需要有解析这些命令行参数的机制。**标准做法是**使用Python内置的 `argparse` 库，它也是我们推荐的方式。请确保 `argparse` 中定义的参数名与 `get_metadata()` 中定义的 `name` 完全一致。

```python
import argparse

def main():
    parser = argparse.ArgumentParser(description='脚本的描述.')
    
    # 这里的 'input_file' 和 'quality' 必须与 get_metadata 中定义的 name 对应
    parser.add_argument('--input_file', type=str, required=True)
    parser.add_argument('--quality', type=int, default=80)
    
    args = parser.parse_args()
    
    # 使用参数
    print(f"输入文件是: {args.input_file}")
    print(f"压缩质量是: {args.quality}")

if __name__ == '__main__':
    main()
```

**重要提示**：`main()` 函数是脚本的执行入口，但 `get_metadata()` 函数的解析是在执行之外独立进行的。请确保 `get_metadata()` 函数本身不依赖任何需要在 `main()` 中初始化的状态。
