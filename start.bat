@echo off
chcp 65001
echo ================================
echo 餐厅点餐系统启动脚本
echo ================================

REM 检查Python版本
python --version

REM 检查虚拟环境
if not exist venv (
    echo 创建虚拟环境...
    python -m venv venv
)

REM 激活虚拟环境
echo 激活虚拟环境...
call venv\Scripts\activate.bat

REM 安装依赖
echo 安装依赖包...
pip install -r requirements.txt

REM 设置环境变量
set FLASK_APP=app.py
set FLASK_ENV=development

REM 启动应用
echo ================================
echo 启动Flask应用...
echo 访问地址: http://localhost:5000
echo 按 Ctrl+C 停止服务
echo ================================

python app.py

pause
