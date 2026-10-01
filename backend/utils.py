# -*- coding: utf-8 -*-

import pyautogui
import mss
from PIL import Image

def is_windowized(window_title:str):
    '''
    判断目标是否窗口化
    '''
    # 获取当前所有窗口的标题
    window_titles = [window.title for window in pyautogui.getAllWindows()]
    
    # 检查是否存在deltaforce窗口
    if window_title in window_titles:
        return True
    else:
        return False

def get_window_postion(target_app:str):
    '''
    获取目标窗口的坐标
    '''
    window_info = pyautogui.getWindowsWithTitle(target_app)[0]
    return [window_info.left, window_info.top, window_info.right, window_info.bottom]

def get_screenshot(debug_mode = False):
    '''
    全屏截图函数
    '''
    # 对整个屏幕进行截图
    with mss.mss() as sct:
        monitor = sct.monitors[0]
        sct_img = sct.grab(monitor)
        # 转换为 PIL Image 对象以保持与原接口一致
        screenshot = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
        
    if debug_mode:
        screenshot.save('screenshot.png')
    return screenshot

def get_windowshot(range:list, debug_mode = False):
    '''
    范围截图函数

    range：截图范围，[left, top, right, bottom]
    '''
    # 对范围内截图
    if range[0] < 1:
        screen_size = pyautogui.size()
        range = [int(screen_size.width * range[0]), 
                 int(screen_size.height * range[1]), 
                 int(screen_size.width * range[2]), 
                 int(screen_size.height * range[3])]
    
    with mss.mss() as sct:
        # mss 的 grab 使用的是 monitor 格式：{'top': y, 'left': x, 'width': w, 'height': h}
        monitor = {"top": range[1], "left": range[0], "width": range[2] - range[0], "height": range[3] - range[1]}
        sct_img = sct.grab(monitor)
        # 转换为 PIL Image 对象
        screenshot = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")

    if debug_mode:
        screenshot.save('screenshot.png')
    return screenshot

def mouse_move(positon:list):
    '''
    postion：鼠标移动位置，[x, y]
    '''
    x = positon[0]
    y = positon[1]
    if x < 1:
        screen_size = pyautogui.size()
        x = int(screen_size.width * x)
        y = int(screen_size.height * y)
    pyautogui.moveTo(x, y)

def mouse_click(positon:list, num:int = 1):
    '''
    postion：鼠标点击位置，[x, y]

    num：点击次数，默认点击一次
    '''
    x = positon[0]
    y = positon[1]
    if x < 1:
        screen_size = pyautogui.size()
        x = int(screen_size.width * x)
        y = int(screen_size.height * y)
    for i in range(num):
        pyautogui.moveTo(x, y)
        pyautogui.mouseDown()
        pyautogui.mouseUp()

def get_mouse_position():
    '''
    获取鼠标当前位置
    '''
    return list(pyautogui.position())

def main():
    mouse_move([2218/2560, 72/1440])

if __name__ == "__main__":
    main()