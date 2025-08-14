from PyQt5 import QtWidgets


def format_price_input(textEdit: QtWidgets.QTextEdit):
    """
    自动格式化输入为带逗号的千位格式
    """
    cursor = textEdit.textCursor()
    pos = cursor.position()
    old_text = textEdit.toPlainText()
    raw_text = old_text.replace(',', '')
    if not raw_text.isdigit():
        return
    formatted = "{:,}".format(int(raw_text))
    if formatted == old_text:
        return
    old_commas_before_cursor = old_text[:pos].count(',')
    new_commas_before_cursor = formatted[:pos].count(',')
    delta = new_commas_before_cursor - old_commas_before_cursor
    textEdit.blockSignals(True)
    textEdit.setPlainText(formatted)
    textEdit.blockSignals(False)
    new_pos = pos + delta
    new_pos = max(0, min(len(formatted), new_pos))  # 限制范围
    cursor.setPosition(new_pos)
    textEdit.setTextCursor(cursor)


def get_plain_number(textEdit: QtWidgets.QTextEdit) -> int:
    """
    外部调用读取值时使用，自动去除逗号
    """
    text = textEdit.toPlainText().replace(",", "")
    return int(text) if text else 0