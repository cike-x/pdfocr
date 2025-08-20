@echo off
:: 设置代码页为 UTF-8
chcp 65001 > nul
:: 设置变量
set EXE_PATH=%CURRENT_DIR%pdf_to_images.exe
set PYTHON_SCRIPT=%CURRENT_DIR%test.py
set IMAGES_FOLDER=%CURRENT_DIR%images

:: Step 1: 运行exe程序
echo 正在运行PDF转换工具...
start /wait %EXE_PATH%
echo 转换完成！
:: 检查是否成功生成图片
if not exist "%IMAGES_FOLDER%\*.jpg" (
    echo 错误：未检测到图片生成，请检查PDF转换工具是否正常运行。
    pause
    exit /b 1
)

:: Step 2: 运行Python脚本处理图片
echo 正在运行图片处理脚本...
py -3.13 "%PYTHON_SCRIPT%"

:: 检查Python脚本是否成功运行
if %ERRORLEVEL% neq 0 (
    echo 错误：图片处理脚本运行失败，请检查脚本内容。
    pause
    exit /b 1
)

echo 所有操作已完成！
pause
