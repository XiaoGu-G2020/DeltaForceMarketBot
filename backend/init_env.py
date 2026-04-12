# -*- coding: utf-8 -*-
"""
后端环境初始化模块
解决 Windows 下 DLL 加载冲突问题
"""
import os
import sys
import glob


def find_torch_lib_path():
    """动态查找 PyTorch lib 目录路径
    
    支持多种虚拟环境命名方式和 Python 版本,按优先级搜索:
    1. 当前 Python 环境的 site-packages (最高优先级)
    2. 常见虚拟环境目录名 (.venv*, venv*, env*, virtualenv*)
    
    Returns:
        str: PyTorch lib 目录的绝对路径,如果未找到则返回 None
    """
    try:
        # 方法1: 直接从当前 Python 环境获取 (最可靠)
        import importlib.util
        torch_spec = importlib.util.find_spec('torch')
        if torch_spec and torch_spec.origin:
            torch_root = os.path.dirname(torch_spec.origin)
            torch_lib = os.path.join(torch_root, 'lib')
            if os.path.exists(torch_lib):
                return torch_lib
        
        # 方法2: 使用 sys.prefix 定位当前环境
        potential_paths = [
            os.path.join(sys.prefix, 'Lib', 'site-packages', 'torch', 'lib'),
            os.path.join(sys.base_prefix, 'Lib', 'site-packages', 'torch', 'lib'),
        ]
        
        for path in potential_paths:
            if os.path.exists(path):
                return path
        
        # 方法3: 搜索项目根目录下的常见虚拟环境目录
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # 使用 glob 模式匹配各种虚拟环境命名
        venv_patterns = [
            '.venv*',      # .venv, .venv312, .venv39 等
            'venv*',       # venv, venv312 等
            'env*',        # env, env312 等
            'virtualenv*', # virtualenv, virtualenv312 等
        ]
        
        for pattern in venv_patterns:
            matches = glob.glob(os.path.join(base_dir, pattern))
            for match in matches:
                if os.path.isdir(match):
                    torch_lib = os.path.join(match, 'Lib', 'site-packages', 'torch', 'lib')
                    if os.path.exists(torch_lib):
                        return torch_lib
        
        return None
        
    except Exception as e:
        print(f"警告: 查找 PyTorch lib 路径时出错: {str(e)}")
        return None


def init_dll_environment():
    """初始化 DLL 环境变量,避免加载冲突
    
    该函数应在导入 PyQt5 和 backend 模块之前调用,用于解决
    Windows 环境下 PyQt5 与 EasyOCR/PyTorch 之间的 DLL 加载冲突。
    
    主要操作:
    1. 将 PyTorch 的 lib 目录添加到 PATH 环境变量最前面
    2. 确保 Qt 平台插件路径正确
    """
    if sys.platform != 'win32':
        return
    
    try:
        # 动态查找 PyTorch lib 路径
        torch_lib_path = find_torch_lib_path()
        
        if torch_lib_path:
            current_path = os.environ.get('PATH', '')
            # 避免重复添加
            if torch_lib_path not in current_path:
                os.environ['PATH'] = torch_lib_path + ';' + current_path
                print(f"✓ 已添加 PyTorch lib 路径到 PATH: {torch_lib_path}")
            else:
                print(f"ℹ PyTorch lib 路径已在 PATH 中")
        else:
            print("⚠ 警告: 未找到 PyTorch lib 目录")
            print("  提示: 请确认是否正确安装了 torch 库")
            print("  可通过以下命令安装: pip install torch")
        
        # 设置其他 Qt 相关环境变量
        os.environ.setdefault('QT_AUTO_SCREEN_SCALE_FACTOR', '1')
        
    except Exception as e:
        # 记录但不中断程序 - 此时 log 模块可能还未初始化
        print(f"⚠ 警告: DLL 环境初始化失败: {str(e)}")
