# -*- coding: utf-8 -*-
"""
后端环境初始化模块
解决 Windows 下 DLL 加载冲突问题
"""
import os
import sys


def init_dll_environment():
    """初始化 DLL 环境变量,避免加载冲突
    
    该函数应在导入 PyQt5 和 backend 模块之前调用,用于解决
    Windows 环境下 PyQt5 与 EasyOCR/PyTorch 之间的 DLL 加载冲突。
    
    主要操作:
    1. 将 PyTorch 的 lib 目录添加到 PATH 环境变量最前面
    2. 设置 Qt 相关环境变量以避免插件加载问题
    """
    if sys.platform != 'win32':
        return
    
    try:
        # 获取项目根目录
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # 查找 torch lib 目录的可能路径
        torch_lib_paths = [
            os.path.join(base_dir, 'venv', 'Lib', 'site-packages', 'torch', 'lib'),
            os.path.join(base_dir, '.venv', 'Lib', 'site-packages', 'torch', 'lib'),
            os.path.join(base_dir, 'env', 'Lib', 'site-packages', 'torch', 'lib'),
            os.path.join(base_dir, 'virtualenv', 'Lib', 'site-packages', 'torch', 'lib'),
        ]
        
        # 尝试找到并添加 torch lib 路径
        for path in torch_lib_paths:
            if os.path.exists(path):
                current_path = os.environ.get('PATH', '')
                # 避免重复添加
                if path not in current_path:
                    os.environ['PATH'] = path + ';' + current_path
                break
        
        # 设置 Qt 相关环境变量,避免插件加载冲突
        os.environ.setdefault('QT_QPA_PLATFORM_PLUGIN_PATH', '')
        os.environ.setdefault('QT_AUTO_SCREEN_SCALE_FACTOR', '1')
        
    except Exception as e:
        # 记录但不中断程序 - 此时 log 模块可能还未初始化
        print(f"警告: DLL 环境初始化失败: {str(e)}")
