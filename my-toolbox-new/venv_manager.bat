
@echo off
:: 虚拟环境管理脚本
echo -------------------------------
echo 虚拟环境管理工具
echo 功能：1. 创建虚拟环境（如不存在） 2. 激活虚拟环境
echo -------------------------------

:: 1. 检查并创建虚拟环境
if not exist "venv\" (
    echo [1/2] 正在创建虚拟环境...
    python -m venv venv
    echo 虚拟环境创建完成！
) else (
    echo 虚拟环境已存在，跳过创建步骤。
)

:: 2. 激活虚拟环境
echo [2/2] 激活虚拟环境...
call venv\Scripts\activate
if errorlevel 1 (
    echo 错误：虚拟环境激活失败！
    pause
    exit /b
)

:: 提示用户手动操作
echo -------------------------------
echo 虚拟环境已激活！请手动执行：
echo   pip install -r requirements.txt
echo 或直接安装所需依赖。
echo -------------------------------
cmd /k
