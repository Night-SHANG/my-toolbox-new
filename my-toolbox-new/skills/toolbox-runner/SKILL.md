---
name: toolbox-runner
description: 通过命令行调用 my-toolbox-new 工具箱中的 Python 脚本。支持 PDF 处理、视频下载、图片转换、二维码生成等功能。当用户要求"运行脚本"、"用工具箱"、"下载视频"、"转换PDF"、"转换图片"等操作时触发。
---

# 工具箱 CLI 技能

通过命令行调用用户的 `my-toolbox-new` 工具箱脚本，自动使用正确的虚拟环境。

## 首次使用引导

如果同目录下的 `config.json` 中 `toolbox_path` 为空或路径不存在，执行以下引导流程：

1. **询问用户**：「请提供你的工具箱路径（包含 cli.py 的目录）」
2. **验证路径**：检查该路径下是否存在 `cli.py` 和 `scripts/` 目录
3. **写入 config.json**：将路径写入 `toolbox_path` 字段
4. **生成脚本目录**：运行 `python "<toolbox_path>\cli.py" snapshot`
5. **构建索引**：读取工具箱目录下生成的 `scripts_catalog.md`，提取每个脚本的标题行号，更新 `config.json` 的 `script_index`
6. **展示说明**：

```
✅ 工具箱已配置完成！

📦 共发现 X 个脚本可用。

📌 使用提示：
- 直接告诉我你想做什么（如"下载这个视频"、"把PDF转成图片"），我会自动调用对应的脚本
- 如果工具箱新增了脚本，请告诉我"更新工具箱脚本目录"
- 脚本的虚拟环境和依赖请在工具箱 GUI 中配置
- 搭配 toolbox-script-creator 技能可以创建新脚本

⚙️ 管理命令（输入数字）：
  1 - 设置/更改工具箱路径
  2 - 更新脚本目录
  3 - 查看/修改脚本默认参数
```

## 日常使用流程

### 1. 读取配置

启动技能时，读取同目录下的 `config.json`，获取：
- `toolbox_path`：工具箱绝对路径
- `script_index`：所有脚本的索引
- `script_defaults`：各脚本的默认参数
- `default_output`：默认输出目录规则（`workspace` = 当前工作目录）

#### config.json 格式规范

```json
{
  "toolbox_path": "C:\\完整\\路径\\my-toolbox-new",
  "default_output": "workspace",
  "script_index": [
    {
      "folder": "脚本文件夹名",
      "name": "脚本显示名称",
      "desc": "简短描述",
      "line": 9
    }
  ],
  "script_defaults": {
    "video_downloader": {
      "quality": "best_mp4",
      "subtitles": true
    }
  }
}
```

字段说明：
- `script_index[].folder`：脚本在 `scripts/` 下的文件夹名，也是 `run` 命令的参数
- `script_index[].name`：脚本在 `scripts_catalog.md` 中 `##` 标题后的显示名称
- `script_index[].desc`：脚本描述（取自 catalog 中 `**描述**:` 行，精简为一句话）
- `script_index[].line`：该脚本的 `##` 标题在 `scripts_catalog.md` 中的**行号**
- `script_defaults`：key 是文件夹名，value 是参数名→值的字典。只保存配置类参数，不保存输入类参数（url、input_file 等）

### 2. 匹配脚本

根据用户需求，从 `script_index` 中匹配目标脚本。如果不确定用哪个，列出相关脚本让用户选择。

### 3. 获取参数详情（必须步骤，禁止跳过）

确定目标脚本后，**必须**用 `script_index` 中的 `line` 字段定位 `scripts_catalog.md` 中的对应段落，读取完整参数表、虚拟环境、依赖等信息。

> **⚠️ 读取规则**：从该脚本的 `line` 行开始，读到下一个脚本的 `line` 行之前（即读取到 `---` 分隔线）。确保不遗漏任何参数。

> **🚫 禁止**：不可仅凭 `config.json` 中的简要索引直接组装命令。`config.json` 只用于匹配脚本，完整参数和环境信息**必须从 `scripts_catalog.md` 获取**。

### 4. 参数处理

#### 有默认参数时（`script_defaults` 中存在该脚本）

向用户展示当前默认参数，让用户确认：

```
📋 使用以下默认参数运行 [脚本名]：
  1. 画质: 1080p_mp4
  2. 字幕: 是
  3. 输出目录: 当前工作目录

确认使用？（输入"是"直接运行，或告诉我要修改哪项）
```

#### 无默认参数时

列出所有参数（带编号），标注必填/可选和默认值：

```
📋 [脚本名] 参数设置：
  1. 画质 [必填]: best_mp4 / best_webm / 1080p_mp4 / 720p_mp4 / audio_mp3
  2. 字幕 [可选，默认: 是]
  3. Cookies [可选，默认: 无]
  4. 输出目录 [必填]: 默认为当前工作目录

请告诉我需要的参数，或直接说"用默认的"。
```

#### 参数规则

- **输入类参数**（url、input_file、input_folder）：根据上下文自动填写，不记录到默认参数
- **输出目录**：默认使用当前工作目录，用户指定其他路径也可以
- **配置类参数**（quality、scale、subtitles 等）：适合保存为默认参数

### 5. 执行脚本

```bash
python "<toolbox_path>\cli.py" run <脚本文件夹名> --参数1 值1 --参数2 值2
```

### 6. 执行后处理

- **运行成功 + 用户修改过参数** → 询问：「是否将本次参数保存为默认？」
  - 用户同意 → 写入 `config.json` 的 `script_defaults`
- **运行成功 + 使用默认参数** → 不询问
- **运行失败** → 先排查错误，解决后再询问参数保存

## 管理命令

用户输入数字触发：

### 1 - 设置/更改工具箱路径

询问新路径 → 验证 → 更新 `config.json` 的 `toolbox_path` → 运行 `snapshot` → 更新 `script_index`

### 2 - 更新脚本目录

执行以下步骤：
1. 运行 `python "<toolbox_path>\cli.py" snapshot`
2. 读取工具箱目录下的 `scripts_catalog.md`
3. 提取每个脚本的标题（`## 脚本名`）所在行号、文件夹名、描述
4. **无条件重写** `config.json` 的 `script_index`（不做"是否有变化"的判断，每次都必须执行覆盖写入）
5. 告知用户更新结果

### 3 - 查看/修改脚本默认参数

1. 从 `config.json` 读取 `script_defaults`
2. 如果为空 → 回复「暂未设定任何脚本的默认参数」
3. 如果有内容 → 列出已设默认参数的脚本，让用户选择要修改哪个
4. 展示该脚本当前默认参数，让用户修改
5. 写回 `config.json`

## 参数传递规则

| 参数类型 | 传递方式 | 示例 |
|:--|:--|:--|
| text | `--name "文本值"` | `--url "https://example.com"` |
| number | `--name 数字` | `--scale 2` |
| boolean | `--name`（出现即为 True） | `--subtitles` |
| choice | `--name 选项值` | `--mode pdf_to_img` |
| file | `--name "文件路径"` | `--input_file "D:\test.pdf"` |
| folder | `--name "文件夹路径"` | `--output_folder "D:\输出"` |

> **⚠️ 路径中有空格时必须用双引号包裹。**

## CLI 命令参考

```bash
python "<toolbox_path>\cli.py" list                  # 列出所有脚本
python "<toolbox_path>\cli.py" info <文件夹名>        # 查看单个脚本详情
python "<toolbox_path>\cli.py" venvs                  # 列出虚拟环境
python "<toolbox_path>\cli.py" run <文件夹名> [参数]   # 运行脚本
python "<toolbox_path>\cli.py" snapshot               # 更新脚本目录文件
```

## 注意事项

- 虚拟环境的创建和依赖安装由用户在工具箱 GUI 中操作
- 如需创建新脚本，请使用 `toolbox-script-creator` 技能，创建后运行管理命令 2 更新目录
- `scripts_catalog.md` 位于工具箱根目录下，由 `snapshot` 命令自动生成
- `config.json` 位于技能文件夹下，由 AI 维护，不会被 `snapshot` 覆盖
