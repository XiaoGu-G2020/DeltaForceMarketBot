import sys
import ctypes
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import QObject, pyqtSignal, Qt, QThread
from GUI.AppGUI import Ui_MainWindow
from backend.BuyBot import BuyBot
from backend.utils import *
from GUI.formatter import format_price_input, get_plain_number
import keyboard

def is_admin():
    """
    检查当前是否以管理员权限运行
    """
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except:
        return False

class KeyMonitor(QObject):
    key_pressed = pyqtSignal(int)

    def __init__(self):
        super().__init__()
        keyboard.on_press(self.handle_key)

    def handle_key(self, event):
        if event.name == 'f8':
            self.key_pressed.emit(0)
            print('开始循环')
        elif event.name == 'f9':
            self.key_pressed.emit(1)
            print('停止循环')

class Worker(QThread):
    update_signal = pyqtSignal(int)
    param_update = pyqtSignal(int)  # 新增参数更新信号

    def __init__(self, buybot):
        super().__init__()
        self.buybot = buybot
        self._is_running = False
        self.lock = QtCore.QMutex()
        self.ideal_price = 0
        self.unacceptable_price = 0
        self.loop_gap = 0
        self.target_buy_number = 1
        self.is_convertible = True
        self.is_key_mode = False
        self.is_half_coin_mode = False
        self.mouse_position = []
        self.mouse_position_lock = QtCore.QMutex()
        self.param_lock = QtCore.QMutex()  # 参数专用锁

    def record_mouse_position(self):
        """记录鼠标位置"""
        self.mouse_position_lock.lock()
        self.mouse_position = get_mouse_position()
        self.mouse_position_lock.unlock()

    def run(self):
        first_loop = True
        buy_number = 0
        while True:
            # 获取运行状态
            self.lock.lock()
            running = self._is_running
            self.lock.unlock()
            if first_loop == False:
                first_loop == True
            else:
                current_target_buy_number = self.target_buy_number
            if running:
                try:
                    # 获取当前参数值
                    self.param_lock.lock()
                    current_ideal = self.ideal_price
                    current_unacceptable = self.unacceptable_price
                    current_convertible = self.is_convertible
                    current_key_mode = self.is_key_mode
                    current_half_coin_mode = self.is_half_coin_mode
                    self.param_lock.unlock()
                    
                    # 进入商品页面
                    mouse_click(self.mouse_position, num = 1)
                    
                    # 获取商品价格
                    if current_half_coin_mode and (not first_loop) and (buy_number != 0):
                        # 使用哈夫币余额差值计算价格
                        try:
                            previous_balance_half_coin = self.buybot.balance_half_coin
                            current_balance_half_coin = self.buybot.detect_balance_half_coin()
                            lowest_price = (previous_balance_half_coin - current_balance_half_coin)/buy_number
                            if lowest_price == 0:
                                # 直接看市场底价
                                lowest_price = self.buybot.detect_price(is_convertible=current_convertible, debug_mode=False)
                                print("上一次购买失败，直接看市场底价:", lowest_price, end=" ")
                            else:
                                print("哈夫币余额差值计算价格:", lowest_price, end=" ")
                        except:
                            # 直接看市场底价
                            lowest_price = self.buybot.detect_price(is_convertible=current_convertible, debug_mode=False)
                            print("余额计算出现异常，直接看市场底价:", lowest_price, end=" ")
                    else:
                        # 直接看市场底价
                        lowest_price = self.buybot.detect_price(is_convertible=current_convertible, debug_mode=False)
                        print("直接看市场底价:", lowest_price, end=" ")
                    
                    if current_key_mode:
                        # 钥匙卡模式
                        if lowest_price > current_ideal:
                            print('当前价格：', lowest_price, '高于理想价格', current_ideal, ' 免费刷新价格')
                            self.buybot.freerefresh(good_postion=self.mouse_position)
                        else:
                            print('当前价格：', lowest_price, '低于理想价格', current_ideal, ' 购买1次', end='')
                            self.buybot.buy_new(is_convertible = self.is_convertible, target_buy_number = 1)
                            current_target_buy_number -= 1
                            if current_target_buy_number == 0: # 购买结束
                                self.set_running(False)
                                print(',达到购买数量，购买结束')
                            else:
                                print(',剩余购买次数{0}'.format(current_target_buy_number))
                    else:
                        # 正常模式
                        if lowest_price > current_unacceptable:
                            print('高于最高价格', current_unacceptable, ' 免费刷新价格')
                            self.buybot.freerefresh(good_postion=self.mouse_position)
                            buy_number = 0
                        elif lowest_price > current_ideal:
                            print('高于理想价格', current_ideal, ' 刷新价格')
                            self.buybot.refresh(is_convertible=current_convertible)
                            buy_number = 31 #原始值为 购买子弹价格/1 ，修改为 购买子弹价格/31
                        else:
                            print('低于理想价格', current_ideal, ' 开始购买')
                            self.buybot.buy(is_convertible=current_convertible)
                            buy_number = 200

                    # 标记为非第一次循环
                    if first_loop == True:
                        first_loop = False
                except Exception as e:
                    if str(e) == '识别失败':  # 识别失败, 建议检查物品是否可兑换
                        self.msleep(self.loop_gap)
                        self.buybot.freerefresh(good_postion=self.mouse_position)
                    else:
                        print(f"操作失败: {str(e)}")
                self.msleep(self.loop_gap)
            else:
                self.msleep(100)
                # 标记为第一次循环
                if first_loop == False:
                    first_loop = True
                    buy_number = 0

    def update_params(self, ideal, unacceptable, convertible, key_mode, half_coin_mode, loop_gap, target_buy_number):
        """线程安全更新参数"""
        self.param_lock.lock()
        self.ideal_price = ideal
        self.unacceptable_price = unacceptable
        self.loop_gap = loop_gap
        self.target_buy_number = target_buy_number
        self.is_convertible = convertible
        self.is_key_mode = key_mode
        self.is_half_coin_mode = half_coin_mode
        self.param_lock.unlock()
    def set_running(self, state):
        """线程安全更新运行状态"""
        self.lock.lock()
        self._is_running = state
        self.lock.unlock()

def runApp():
    app = QtWidgets.QApplication([])
    window = QtWidgets.QMainWindow()
    mainWindow = Ui_MainWindow()
    mainWindow.setupUi(window)

    # 初始化输入部分
    mainWindow.textEdit_ideal_price.setText('0')
    mainWindow.textEdit_unacceptable_price.setText('0')
    mainWindow.textEdit_loop_gap.setText('150')
    mainWindow.textEdit_key_mode_buy_number.setText('1')
    mainWindow.is_convertiable.setChecked(True)
    mainWindow.is_key_mode.setChecked(False)
    mainWindow.is_half_coin_mode.setChecked(False)
    
    # 根据初始状态设置控件启用状态
    mainWindow.textEdit_unacceptable_price.setEnabled(not mainWindow.is_key_mode.isChecked())
    mainWindow.textEdit_key_mode_buy_number.setEnabled(mainWindow.is_key_mode.isChecked())

    # 添加千位分隔监听器
    mainWindow.textEdit_ideal_price.textChanged.connect(lambda: format_price_input(mainWindow.textEdit_ideal_price))
    mainWindow.textEdit_unacceptable_price.textChanged.connect(lambda: format_price_input(mainWindow.textEdit_unacceptable_price))

    # 创建监控线程
    key_monitor = KeyMonitor()
    worker = Worker(BuyBot())
    
    # 信号连接
    def handle_key_event(x):
        if x == 0:
            worker.record_mouse_position()
        worker.set_running(x == 0)

    key_monitor.key_pressed.connect(handle_key_event)
    
    def handle_key_mode_change():
        """处理钥匙卡模式状态变更"""
        is_key_mode = mainWindow.is_key_mode.isChecked()
        # 根据钥匙卡模式状态启用/禁用相应控件
        mainWindow.textEdit_unacceptable_price.setEnabled(not is_key_mode)
        mainWindow.textEdit_key_mode_buy_number.setEnabled(is_key_mode)
        # 触发文本变更事件以更新worker参数
        handle_text_change()

    def handle_text_change():
        ideal = int(get_plain_number(mainWindow.textEdit_ideal_price))
        unaccept = int(get_plain_number(mainWindow.textEdit_unacceptable_price))
        loop_gap = int(mainWindow.textEdit_loop_gap.toPlainText())
        target_buy_number = int(get_plain_number(mainWindow.textEdit_key_mode_buy_number))
        is_convertible = mainWindow.is_convertiable.isChecked()
        is_key_mode = mainWindow.is_key_mode.isChecked()
        is_half_coin_mode = mainWindow.is_half_coin_mode.isChecked()
        worker.update_params(ideal, unaccept, is_convertible, is_key_mode, is_half_coin_mode, loop_gap, target_buy_number)

    # 确保所有相关控件都连接了变更处理函数
    mainWindow.textEdit_ideal_price.textChanged.connect(handle_text_change)
    mainWindow.textEdit_unacceptable_price.textChanged.connect(handle_text_change)
    mainWindow.textEdit_loop_gap.textChanged.connect(handle_text_change)
    mainWindow.textEdit_key_mode_buy_number.textChanged.connect(handle_text_change)
    mainWindow.is_convertiable.stateChanged.connect(handle_text_change)
    mainWindow.is_key_mode.stateChanged.connect(handle_key_mode_change)
    mainWindow.is_half_coin_mode.stateChanged.connect(handle_text_change)

    window.show()
    worker.start()
    app.exec_()

def main():
    return runApp()

if __name__ == "__main__":
    if not is_admin():
        # 尝试重新以管理员身份启动
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, " ".join(sys.argv), None, 1)
        sys.exit(0)
    print("正在初始化")
    sys.exit(main())
