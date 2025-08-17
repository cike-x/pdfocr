import os
import sys
import subprocess
import importlib

# ================== 配置区域 ==================
OFFLINE_DIR = "offline_packages"  # 本地包存放文件夹
ENABLE_ONLINE_FALLBACK = True    # 是否允许在线回退（可设为 False 实现纯离线）
# =============================================

def find_wheel_file(directory, package_name):
    """在指定目录中查找匹配的 .whl 文件（忽略大小写和 '-'）"""
    if not os.path.exists(directory):
        return None
    target = package_name.replace("-", "").lower()
    for file in os.listdir(directory):
        if file.endswith(".whl") and target in file.replace("-", "").lower():
            return file
    return None

def install_from_local(package_name):
    """尝试从本地目录安装包"""
    wheel_file = find_wheel_file(OFFLINE_DIR, package_name)
    if not wheel_file:
        return False

    wheel_path = os.path.join(OFFLINE_DIR, wheel_file)
    print(f"📦 正在从本地安装: {wheel_file}")
    try:
        subprocess.check_call([
            sys.executable, '-m', 'pip', 'install', wheel_path,
            '--find-links', OFFLINE_DIR,
            '--no-index',  # 禁用在线索引，强制离线
            '--no-cache-dir'
        ])
        print(f"✅ {package_name} 从本地安装成功。")
        return True
    except Exception as e:
        print(f"❌ 本地安装失败 {package_name}: {e}")
        return False

def install_and_import(package, pip_name=None):
    """检查并安装指定的包：优先本地，失败后可回退在线"""
    try:
        importlib.import_module(package)
        print(f"✅ {package} 已安装，跳过。")
        return
    except ImportError:
        pass  # 继续安装流程

    print(f"🔍 未检测到 {package}，正在尝试安装...")

    # 1. 尝试从本地安装
    if install_from_local(pip_name or package):
        # 安装成功后再次尝试导入
        try:
            importlib.import_module(package)
            return
        except ImportError:
            print(f"⚠️ 本地安装了但无法导入 {package}，可能是平台不兼容。")
            if not ENABLE_ONLINE_FALLBACK:
                sys.exit(1)

    # 2. 本地失败，尝试在线安装（如果启用）
    if ENABLE_ONLINE_FALLBACK:
        print(f"🌐 本地未找到，正在尝试在线安装 {pip_name or package} ...")
        try:
            subprocess.check_call([
                sys.executable, '-m', 'pip', 'install',
                pip_name or package
            ], stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
            print(f"✅ 在线安装成功。")
            return
        except Exception as e:
            print(f"❌ 在线安装也失败: {e}")
    else:
        print(f"❌ 离线安装失败，且已禁用在线回退，请检查本地包是否完整。")
        print(f"请确保 {OFFLINE_DIR}/ 中包含 {pip_name or package} 的兼容 .whl 文件。")

    # 所有方式都失败
    print(f"❌ 安装 {pip_name or package} 失败，请手动安装。")
    sys.exit(1)


# === 开始检查依赖 ===
print("🔍 正在检查运行环境依赖...")

# 安装 setuptools（通常不需要，但保留）
install_and_import('setuptools')

# 安装 paddleocr
install_and_import('paddleocr', 'paddleocr')

# 检查 paddlepaddle（注意：不能用 cv2 这种别名方式判断）
try:
    import paddle
    print("✅ paddlepaddle 已安装。")
except ImportError:
    print("🔍 未检测到 paddlepaddle，正在尝试安装...")
    if install_from_local('paddlepaddle'):
        try:
            import paddle
            print("✅ paddlepaddle 加载成功。")
        except:
            print("⚠️ 本地安装成功但导入失败，可能 wheel 不兼容。")
            if not ENABLE_ONLINE_FALLBACK:
                sys.exit(1)
    else:
        if ENABLE_ONLINE_FALLBACK:
            print("🌐 正在在线安装 paddlepaddle（CPU 版）...")
            try:
                subprocess.check_call([
                    sys.executable, '-m', 'pip', 'install', 'paddlepaddle'
                ], stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
                print("✅ paddlepaddle 在线安装成功。")
            except Exception as e:
                print("❌ paddlepaddle 安装失败，请手动运行：pip install paddlepaddle")
                print(f"错误信息: {e}")
                sys.exit(1)
        else:
            print("❌ 本地未找到 paddlepaddle，且禁用在线安装，请手动放入 .whl 文件。")
            sys.exit(1)

# 安装 OpenCV
install_and_import('cv2', 'opencv-python')

print("✅ 所有依赖已准备就绪，开始执行 OCR 任务...\n")

from paddleocr import PaddleOCR
import os

# 初始化 OCR 引擎
ocr = PaddleOCR(
    use_textline_orientation=True,
    lang='ch'
)

# 图片文件夹路径（只修改这里）
img_folder = './images'
output_file = 'result.txt'
print("图片文件夹路径:", img_folder)

# 支持的图片扩展名
image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.gif'}

# 获取文件夹中所有图片文件
image_files = [
    os.path.join(img_folder, fname)
    for fname in os.listdir(img_folder)
    if os.path.isfile(os.path.join(img_folder, fname)) and os.path.splitext(fname)[1].lower() in image_extensions
]

# 按文件名排序，保证顺序一致
image_files.sort()

# 打开输出文件
with open(output_file, 'w', encoding='utf-8') as f:
    for img_path in image_files:
        print("图片路径:", img_path)

        # 执行预测（原样保留你的 predict 调用）
        results = ocr.predict(img_path)
        print("【识别结果】")
        result = results[0]

        # 获取识别出的文字、置信度、坐标框（完全不变）
        texts = result['rec_texts']
        scores = result['rec_scores']
        boxes = result['rec_polys']

        # 筛选手写体（完全不变）
        handwritten_results = []
        for i in range(len(texts)):
            text = texts[i]
            score = scores[i]
            box = boxes[i].tolist()

            if score < 0.98:  # 假设置信度低于 0.85 为手写
                handwritten_results.append({
                    'text': text,
                    'score': float(score),
                    'box': box
                })

        # 写入结果文件
        f.write(f"{os.path.basename(img_path)}:\n")
        if handwritten_results:
            for item in handwritten_results:
                f.write(f"文字: {item['text']}\n")
        else:
            f.write("无手写体识别结果\n")
        f.write("\n")  # 每张图空一行分隔

print(f"【完成】所有图片处理完毕，结果已保存至 {output_file}")