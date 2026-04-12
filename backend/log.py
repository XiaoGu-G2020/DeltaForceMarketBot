# -*- coding: utf-8 -*-

import os
import traceback
from datetime import datetime


# 全局变量：缓存当前日志文件路径和日期
_current_log_file = None
_current_log_date = None
_max_file_size = 10 * 1024 * 1024  # 10MB

# 日志级别配置
_LOG_LEVELS = {
    'DEBUG': 0,
    'INFO': 1,
    'WARNING': 2,
    'ERROR': 3,
    'CRITICAL': 4
}
_current_log_level = 'INFO'  # 默认级别，可以通过 set_log_level() 修改


def set_log_level(level):
    """设置日志级别
    
    Args:
        level (str): 日志级别，可选值: 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'
    
    Example:
        set_log_level('DEBUG')  # 显示所有日志
        set_log_level('ERROR')  # 只显示错误及以上
    """
    global _current_log_level
    if level in _LOG_LEVELS:
        _current_log_level = level
    else:
        raise ValueError(f"无效的日志级别: {level}，可选值: {list(_LOG_LEVELS.keys())}")


def get_log_level():
    """获取当前日志级别
    
    Returns:
        str: 当前日志级别
    """
    return _current_log_level


def _get_log_dir():
    """获取日志目录路径"""
    log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'logs')
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    return log_dir


def _get_log_file_path():
    """获取当前应该使用的日志文件路径
    
    策略：
    1. 同一天内使用同一个日志文件
    2. 跨天后自动切换到新文件
    3. 如果文件超过大小限制，创建带序号的新文件
    
    Returns:
        str: 日志文件完整路径
    """
    global _current_log_file, _current_log_date
    
    current_date = datetime.now().strftime('%Y%m%d')
    log_dir = _get_log_dir()
    
    # 如果日期变化，切换新文件
    if _current_log_date != current_date:
        _current_log_date = current_date
        base_filename = f"market_bot_{current_date}.log"
        _current_log_file = os.path.join(log_dir, base_filename)
    
    # 检查文件大小，如果超过限制则创建新文件
    if _current_log_file and os.path.exists(_current_log_file):
        file_size = os.path.getsize(_current_log_file)
        if file_size >= _max_file_size:
            # 生成带时间戳的备份文件名
            timestamp = datetime.now().strftime('%H%M%S')
            backup_name = f"market_bot_{current_date}_{timestamp}.log"
            _current_log_file = os.path.join(log_dir, backup_name)
    
    return _current_log_file


def _write_log(level, message):
    """内部方法:写入日志到文件
    
    Args:
        level (str): 日志级别 ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')
        message (str): 日志消息内容
    """
    # 检查日志级别，低于当前级别的日志不记录
    if _LOG_LEVELS.get(level, 0) < _LOG_LEVELS.get(_current_log_level, 1):
        return
    
    log_path = _get_log_file_path()
    
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]  # 精确到毫秒
    log_entry = f"{timestamp} [{level.upper()}] {message}\n"
    
    with open(log_path, 'a', encoding='utf-8') as f:
        f.write(log_entry)


def log_debug(message):
    """追加写入debug级别日志（仅在DEBUG模式下记录）
    
    Args:
        message (str): 日志消息内容
    
    Example:
        log_debug(f"截图保存路径: {image_path}")
        log_debug(f"OCR识别结果: {text}")
    """
    _write_log('DEBUG', message)


def log_info(message):
    """追加写入info级别日志
    
    Args:
        message (str): 日志消息内容
    """
    _write_log('INFO', message)


def log_warning(message):
    """追加写入warning级别日志
    
    Args:
        message (str): 日志消息内容
    """
    _write_log('WARNING', message)


def log_error(message):
    """追加写入error级别日志
    
    Args:
        message (str): 日志消息内容
    """
    _write_log('ERROR', message)


def log_critical(message):
    """追加写入critical级别日志（严重错误，可能导致程序崩溃）
    
    Args:
        message (str): 日志消息内容
    
    Example:
        log_critical("数据库连接失败，程序无法继续运行")
        log_critical("关键配置文件丢失")
    """
    _write_log('CRITICAL', message)


def log_exception(message=None, exc_info=None):
    """记录异常信息,包含完整的堆栈跟踪
    
    Args:
        message (str, optional): 自定义错误消息
        exc_info: 异常信息,默认为当前异常
    """
    if message:
        error_msg = f"{message}\n{traceback.format_exc()}"
    else:
        error_msg = traceback.format_exc()
    
    _write_log('ERROR', error_msg)


def get_current_log_file():
    """获取当前正在使用的日志文件路径
    
    Returns:
        str: 当前日志文件的完整路径
    """
    return _get_log_file_path()


def cleanup_old_logs(days_to_keep=30):
    """清理指定天数之前的日志文件
    
    Args:
        days_to_keep (int): 保留最近多少天的日志，默认30天
    
    Returns:
        int: 删除的文件数量
    """
    import time
    
    log_dir = _get_log_dir()
    if not os.path.exists(log_dir):
        return 0
    
    deleted_count = 0
    current_time = time.time()
    cutoff_time = current_time - (days_to_keep * 24 * 3600)
    
    for filename in os.listdir(log_dir):
        if filename.endswith('.log'):
            filepath = os.path.join(log_dir, filename)
            file_mtime = os.path.getmtime(filepath)
            
            if file_mtime < cutoff_time:
                try:
                    os.remove(filepath)
                    deleted_count += 1
                except Exception as e:
                    print(f"删除日志文件失败 {filename}: {str(e)}")
    
    return deleted_count
