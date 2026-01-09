# -*- coding: utf-8 -*-

if __name__ == '__main__':
    from utils import *
else:
    from backend.utils import *
import time
import easyocr
import numpy as np
from copy import deepcopy

class BuyBot:
    def __init__(self):
        self.reader = easyocr.Reader(['en'], gpu=True)
        # 这里以后不再使用小数，使用像素数/屏幕分辨率来尽量提高精度
        self.range_isconvertible_lowest_price = [2179/2560, 1078/1440, 2308/2560, 1102/1440]
        self.range_notconvertible_lowest_price = [2179/2560, 1156/1440, 2308/2560, 1178/1440]
        # 下面两个值为不可兑换商品的相关坐标，可兑换商品的相关坐标用offset_isconvertible进行计算
        self.postion_max_shopping_number = [2324/2560, 1112/1440]
        self.postion_min_shopping_number = [2028/2560, 1112/1440]
        self.postion_buy_button = [2186/2560, 1225/1440]
        self.offset_isconvertible = (1038 - 1112) / 1440
        self.postion_balance = [2200/2560, 70/1440]
        self.postion_balance_half_coin = [1930/2560, 363/1440, 2324/2560, 387/1440]
        self.lowest_price = None
        self.balance_half_coin = None
        print('初始化完成')
    
    def identify_number(self, img, debug_mode = False):
        try:
            text = self.reader.readtext(np.array(img))
            text = text[-1][1]
            text = text.replace(',', '')
            text = text.replace('.', '')
            text = text.replace(' ', '')
            text = text.replace('g', '9')
        except:
            text = None
        if debug_mode == True:
            print(text)
        return int(text) if text else None

    def detect_price(self, is_convertible, debug_mode = False):
        if is_convertible:
            self._screenshot = get_windowshot(self.range_isconvertible_lowest_price, debug_mode=debug_mode)
        else:
            self._screenshot = get_windowshot(self.range_notconvertible_lowest_price, debug_mode=debug_mode)
        # 识别最低价格
        self.lowest_price = self.identify_number(self._screenshot)

        if self.lowest_price == None:
            print('识别失败, 建议检查物品是否可兑换')
            raise Exception('识别失败')
        return int(self.lowest_price)

    def detect_balance_half_coin(self, debug_mode = False):
        # 先把鼠标移到余额位置
        mouse_move(self.postion_balance)
        # 对哈夫币余额范围进行截图然后识别
        self._screenshot = get_windowshot(self.postion_balance_half_coin, debug_mode=debug_mode)
        self.balance_half_coin = self.identify_number(self._screenshot)

        if self.balance_half_coin == None:
            print('哈夫币余额检测识别失败或不稳定，建议关闭余额识别相关功能')
        return self.balance_half_coin
    
    def get_half_coin_diff(self):
        previous_balance_half_coin = self.balance_half_coin
        self.detect_balance_half_coin()
        return self.balance_half_coin - previous_balance_half_coin

    def buy(self, is_convertible):
        self.buy_new(is_convertible, 200)
            
    def refresh(self, is_convertible):
        self.buy_new(is_convertible, 31)

    def buy_new(self, is_convertible:bool, target_buy_number:int) -> None:
        '''
        重构后的购买函数，可以执行1-200之间任意数量的购买
        '''
        # 计算购买数量position
        pos = [(target_buy_number - 1) / 200 * (self.postion_max_shopping_number[0] - self.postion_min_shopping_number[0]) + self.postion_min_shopping_number[0], self.postion_min_shopping_number[1]]
        if is_convertible:
            pos[1] = pos[1] + self.offset_isconvertible
        mouse_click(pos)
        # 计算购买按钮position
        pos = deepcopy(self.postion_buy_button)
        if is_convertible:
            pos[1] = pos[1] + self.offset_isconvertible
        mouse_click(pos)

    def freerefresh(self, good_postion):
        # esc回到商店页面
        pyautogui.press('esc')
        # 点击回到商品页面
        mouse_click(good_postion)

def main():
    bot = BuyBot()
    time.sleep(5)
    print(bot.buy_new(is_convertible = True, target_buy_number = 155))

if __name__ == '__main__':
    main()