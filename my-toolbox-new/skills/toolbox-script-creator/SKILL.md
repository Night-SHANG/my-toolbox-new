---
name: toolbox-script-creator
description: 为 my-toolbox-new 工具箱创建符合规范的 Python 脚本。包含完整的 UI 参数类型规范、文件结构约定、元数据格式要求和 argparse 对应关系。当用户要求"写一个脚本"、"做一个工具"、"添加一个脚本到工具箱"时触发。
---

# 工具箱脚本制作技能

本技能用于为 `my-toolbox-new` 工具箱创建完全符合规范的 Python 脚本。

## 触发条件

当用户要求以下操作时使用本技能：
- "写一个脚本"、"做一个工具"、"添加一个脚本到工具箱"
- "帮我做一个 XXX 功能的脚本"
- 任何涉及在工具箱 `scripts/` 目录下创建新脚本的需求

## ⚠️ 关键约束（必须严格遵守）

### 1. `get_metadata()` 函数的 `return` 字典必须是纯字面量

工具箱使用 Python 的 `ast.literal_eval()` 来解析 `get_metadata()` 的返回值。
这意味着：

- ✅ 字典中**只能包含**：字符串、数字、布尔值、`None`、列表、字典（纯字面量）
- ❌ **绝对不能包含**：变量引用、函数调用、f-string、常量引用、表达式
- ❌ **绝对不能省略 `return` 关键字**

```python
# ✅ 正确
def get_metadata():
    return {
        'name': '我的脚本',
        'description': '这是描述',
        'defaultValue': 85
    }

# ❌ 错误 - 使用了变量
SCRIPT_NAME = '我的脚本'
def get_metadata():
    return {
        'name': SCRIPT_NAME,  # 变量引用，ast.literal_eval 无法解析！
    }

# ❌ 错误 - 缺少 return
def get_metadata():
    {
        'name': '我的脚本',  # 没有 return，工具箱无法发现此脚本！
    }
```

### 2. `get_metadata()` 必须使用多行格式

字典**必须**写成多行缩进格式，**禁止**压缩成一行。

```python
# ✅ 正确 - 多行格式
def get_metadata():
    """获取脚本元数据"""
    return {
        'name': '图片压缩',
        'description': '批量压缩图片文件。',
        'dependencies': ['Pillow'],
        'parameters': [
            {
                'name': 'input_file',
                'type': 'file',
                'label': '选择图片',
                'required': True
            }
        ],
        'category': '图片',
        'icon': ''
    }

# ❌ 禁止 - 一行格式
def get_metadata():
    return {'name': '图片压缩', 'description': '批量压缩图片文件。', ...}
```

---

## 文件结构规范

### 目录结构

每个脚本是 `scripts/` 下的一个**文件夹**，入口文件固定为 `main.py`：

```
my-toolbox-new/                # 工具箱根目录（包含 main.py、core/、gui/ 等）
└── scripts/                   # 所有脚本都在这个目录下
    ├── 我的脚本名/            # 文件夹名 = 脚本在工具箱中显示的名称
    │   ├── main.py            # 【必须】入口文件，包含 get_metadata() 和 main()
    │   ├── utils.py           # 【可选】辅助模块
    │   └── data/              # 【可选】脚本需要的数据文件
```

> **⚠️ 定位规则**：创建脚本前，必须先在用户的工作区中找到工具箱根目录（特征：包含 `core/`、`gui/`、`scripts/` 三个子目录），然后将脚本创建在其 `scripts/` 目录下。不要凭猜测硬编码路径。

**关键规则**：
- 文件夹名就是脚本名（显示在工具箱卡片上）
- 入口文件**必须**命名为 `main.py`
- 脚本可以包含多个 `.py` 文件，`main.py` 可以 `from xxx import yyy` 导入同目录下的其他模块
- 如果脚本需要外部可执行文件（如 `yt-dlp.exe`、`ffmpeg.exe`），放在脚本文件夹内，通过 `Path(__file__).parent` 定位

### main.py 必须包含的两个函数

```python
def get_metadata():
    """获取脚本元数据"""
    return { ... }  # 纯字面量字典

def main():
    """主执行函数"""
    ...  # 脚本逻辑

if __name__ == '__main__':
    main()
```

---

## `get_metadata()` 完整字段规范

```python
def get_metadata():
    """获取脚本元数据"""
    return {
        # 【可选】脚本显示名称。不写则使用文件夹名
        'name': '我的脚本',

        # 【必须】脚本功能描述，显示在卡片上
        'description': '这个脚本的功能描述。',

        # 【必须】第三方依赖列表。无依赖写空列表 []
        'dependencies': ['requests', 'Pillow'],

        # 【必须】参数列表。无参数写空列表 []
        'parameters': [ ... ],

        # 【可选】初始分类。不写则归入"未分类"
        # 注意：分类后续由 user_profile.json 管理，此处仅作首次发现时的默认值
        'category': '工具',

        # 【可选】图标路径。留空则使用默认图标
        'icon': ''
    }
```

---

## 条件显示参数（`showWhen`）

当脚本有多种操作模式时，可以用 `showWhen` 让参数根据下拉框的选择动态显示/隐藏，避免 UI 上堆满不相关的参数。

### 用法

在参数定义中添加 `showWhen` 字段，值为一个字典，键是触发参数的 `name`，值是允许显示的 `value` 列表：

```python
{
    'name': 'scale',
    'type': 'number',
    'label': '放大倍数',
    'defaultValue': 2,
    'showWhen': {'mode': ['pdf_to_img']}  # 仅当 mode 选择了 pdf_to_img 时显示
}
```

### 规则

- `showWhen` 是**可选**字段。不写则始终显示。
- 键必须是**同一脚本中另一个参数的 `name`**（通常是 `choice` 类型）。
- 值是一个列表，包含该触发参数的哪些 `value` 值时应该显示此参数。
- 没有被任何值匹配时，参数会被隐藏（`display: none`），但**不影响命令行传参**——隐藏的参数仍会以默认值或空值传递。

---

## UI 参数类型完整规范

工具箱支持 7 种参数类型。每种类型在 UI 上渲染为不同的控件，在命令行传参时有不同的行为。

### 1. `text` — 单行文本输入框

```python
{
    'name': 'username',           # 【必须】参数名，用于 argparse 的 --username
    'type': 'text',               # 【必须】类型标识
    'label': 'GitHub 用户名',      # 【必须】显示在 UI 上的标签
    'required': True,             # 【可选】是否必填，默认 False
    'defaultValue': 'torvalds',   # 【可选】默认值
    'placeholder': '请输入用户名'   # 【可选】占位提示文本
}
```

**UI 渲染**：`<input type="text">`
**传参方式**：`--username torvalds`
**argparse 对应**：
```python
parser.add_argument('--username', type=str, required=True)
```

---

### 2. `number` — 数字输入框

```python
{
    'name': 'quality',
    'type': 'number',
    'label': '图片质量 (1-100)',
    'defaultValue': 85,           # 数字默认值
    'placeholder': '仅对JPEG/WEBP有效'
}
```

**UI 渲染**：`<input type="number">`
**传参方式**：`--quality 85`
**argparse 对应**：
```python
parser.add_argument('--quality', type=int, default=85)
```

---

### 3. `boolean` — 复选框（开关）

```python
{
    'name': 'keep_original',
    'type': 'boolean',
    'label': '保留原始文件',
    'defaultValue': True          # True = 默认勾选
}
```

**UI 渲染**：`<input type="checkbox">`
**传参方式**：勾选时传 `--keep_original`，不勾选时**不传任何内容**
**argparse 对应**（⚠️ 特殊）：
```python
# 必须用 action='store_true'，不能用 type=bool
parser.add_argument('--keep_original', action='store_true')
```

> **⚠️ boolean 类型是最容易写错的。** `action='store_true'` 表示"出现这个参数就是 True，不出现就是 False"。**绝对不能**写成 `type=bool`。

---

### 4. `choice` — 下拉选择框

```python
{
    'name': 'output_format',
    'type': 'choice',
    'label': '目标格式',
    'choices': [                   # 【必须】选项列表
        {'value': 'JPEG', 'label': 'JPEG'},
        {'value': 'PNG', 'label': 'PNG'},
        {'value': 'WEBP', 'label': 'WEBP'}
    ],
    'defaultValue': 'JPEG'         # 默认选中项的 value
}
```

**UI 渲染**：`<select>` 下拉框
**传参方式**：`--output_format JPEG`（传的是 `value` 值）
**argparse 对应**：
```python
parser.add_argument('--output_format', type=str, required=True)
# 可选：在代码中用 choices 参数限制可选值
parser.add_argument('--output_format', type=str, choices=['JPEG', 'PNG', 'WEBP'], default='JPEG')
```

---

### 5. `textarea` — 多行文本输入框

```python
{
    'name': 'notes',
    'type': 'textarea',
    'label': '备注',
    'placeholder': '记录一下今天发生的事吧...',
    'defaultValue': ''
}
```

**UI 渲染**：`<textarea>`
**传参方式**：`--notes "用户输入的多行文本"`
**argparse 对应**：
```python
parser.add_argument('--notes', type=str, default='')
```

---

### 6. `file` — 文件选择器（带浏览按钮 + 保存按钮）

```python
{
    'name': 'input_file',
    'type': 'file',
    'label': '源图片文件',
    'required': True,
    'placeholder': '选择一个文件'
}
```

**UI 渲染**：文本框 + "浏览..." 按钮（弹出系统文件选择对话框）+ "保存" 按钮（持久化路径）
**传参方式**：`--input_file "C:\Users\xxx\图片.jpg"`
**argparse 对应**：
```python
parser.add_argument('--input_file', type=str, required=True)
```

> **💡 提示**：`file` 和 `folder` 类型自带 "保存" 按钮，用户点击后路径会被持久化到 `user_profile.json`，下次打开脚本时自动填入。对于经常使用固定路径的场景非常方便。

---

### 7. `folder` — 文件夹选择器（带浏览按钮 + 保存按钮）

```python
{
    'name': 'output_path',
    'type': 'folder',
    'label': '保存位置',
    'required': True,
    'placeholder': '选择目标文件夹'
}
```

**UI 渲染**：文本框 + "浏览..." 按钮（弹出系统文件夹选择对话框）+ "保存" 按钮
**传参方式**：`--output_path "C:\Users\xxx\Downloads"`
**argparse 对应**：
```python
parser.add_argument('--output_path', type=str, required=True)
```

> **💡 最佳实践**：当脚本需要输出文件时，**优先使用 `folder` 类型**让用户选择保存文件夹，而不是让用户手动输入路径。这样用户可以用"保存"按钮持久化路径，避免每次都重新选择。

---

## `main()` 函数与 argparse 的对应规则

工具箱通过命令行参数 `--参数名 值` 的方式将 UI 上的值传给脚本。因此 `main()` 必须用 `argparse` 接收参数。

### 对应关系速查表

| `get_metadata` 中的 type | argparse 写法 | 说明 |
|:--|:--|:--|
| `text` | `add_argument('--name', type=str)` | 字符串 |
| `number` | `add_argument('--name', type=int)` 或 `type=float` | 数字 |
| `boolean` | `add_argument('--name', action='store_true')` | ⚠️ 必须用 action |
| `choice` | `add_argument('--name', type=str)` | 传的是 value 值 |
| `textarea` | `add_argument('--name', type=str)` | 长文本也是字符串 |
| `file` | `add_argument('--name', type=str)` | 文件路径字符串 |
| `folder` | `add_argument('--name', type=str)` | 文件夹路径字符串 |

### 参数名对应规则

`get_metadata()` 中参数的 `name` 字段 **必须** 与 `argparse` 中的参数名完全一致：

```python
# get_metadata 中
{'name': 'output_path', 'type': 'folder', ...}

# main 中 —— 必须对应
parser.add_argument('--output_path', ...)  # ✅ 一致
parser.add_argument('--save_path', ...)    # ❌ 不一致，收不到值！
```

---

## 第三方依赖处理

如果脚本使用了非标准库的第三方包：

1. 在 `get_metadata()` 的 `dependencies` 列表中声明
2. 在文件头部用 `try/except ImportError` 做优雅降级

```python
import argparse
try:
    import requests
    from PIL import Image
except ImportError as e:
    print(f'错误：缺少必要的依赖包 -> {e.name}')
    print('请在工具箱中为此脚本配置虚拟环境，并安装依赖。')
    exit(1)

def get_metadata():
    return {
        ...
        'dependencies': ['requests', 'Pillow'],
        ...
    }
```

---

## 输出规范

脚本通过 `print()` 输出信息到工具箱的终端面板。建议使用 emoji 前缀增强可读性：

```python
print('🚀 开始处理...')
print('✅ 任务完成！')
print('❌ 发生错误: ...')
print('⚠️ 警告: ...')
print('ℹ️ 提示: ...')
```

---

## 完整脚本模板

### 模板 A：有参数的脚本

```python
import argparse
import sys
import os
from pathlib import Path

def get_metadata():
    """获取脚本元数据"""
    return {
        'name': '脚本显示名',
        'description': '这个脚本做什么的一句话描述。',
        'dependencies': [],
        'parameters': [
            {
                'name': 'input_file',
                'type': 'file',
                'label': '输入文件',
                'required': True
            },
            {
                'name': 'output_path',
                'type': 'folder',
                'label': '保存位置',
                'required': True,
                'placeholder': '选择目标文件夹'
            },
            {
                'name': 'quality',
                'type': 'number',
                'label': '质量 (1-100)',
                'defaultValue': 85
            },
            {
                'name': 'verbose',
                'type': 'boolean',
                'label': '显示详细日志',
                'defaultValue': False
            }
        ],
        'category': '工具',
        'icon': ''
    }

def main():
    # Windows 终端编码兼容（防止 emoji 输出报错）
    sys.stdout.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(description='脚本描述')
    parser.add_argument('--input_file', type=str, required=True)
    parser.add_argument('--output_path', type=str, required=True)
    parser.add_argument('--quality', type=int, default=85)
    parser.add_argument('--verbose', action='store_true')
    args = parser.parse_args()

    print('🚀 开始处理...')

    # === 在此编写脚本逻辑 ===

    print('✅ 任务完成！')

if __name__ == '__main__':
    main()
```

### 模板 B：无参数的脚本

```python
def get_metadata():
    """获取脚本元数据"""
    return {
        'name': '系统信息',
        'description': '显示当前系统的基本信息。',
        'dependencies': [],
        'parameters': [],
        'category': '工具',
        'icon': ''
    }

def main():
    import sys
    import platform
    # Windows 终端编码兼容（防止 emoji 输出报错）
    sys.stdout.reconfigure(encoding='utf-8')
    print('🖥️ 系统信息')
    print(f'操作系统: {platform.system()} {platform.version()}')
    print(f'Python 版本: {platform.python_version()}')
    print(f'处理器: {platform.processor()}')
    print('✅ 完成')

if __name__ == '__main__':
    main()
```

---

## 自检清单

创建脚本后，务必逐项检查：

- [ ] `get_metadata()` 有 `return` 关键字
- [ ] `return` 的字典是纯字面量（无变量、无函数调用、无 f-string）
- [ ] 字典使用多行格式，不是一行
- [ ] 每个参数的 `name` 与 `argparse` 中的 `--参数名` 完全一致
- [ ] `boolean` 类型在 argparse 中使用 `action='store_true'`
- [ ] `choice` 类型有 `choices` 列表，每项包含 `value` 和 `label`
- [ ] 文件保存到 `scripts/脚本文件夹名/main.py`
- [ ] 文件头部对第三方依赖做了 `try/except ImportError` 处理
- [ ] `main()` 开头包含 `sys.stdout.reconfigure(encoding='utf-8')`（Windows 编码兼容）
- [ ] `if __name__ == '__main__': main()` 存在于文件末尾
