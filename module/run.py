import time
import send2trash
from PySide6.QtWidgets import QApplication, QMainWindow, QTableWidgetItem
from PySide6.QtCore import Signal, Qt
from qfluentwidgets import MessageBox, InfoBar, InfoBarPosition

from module.gui import Ui_MainWindow
from module.function import *


class MyMainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self, parent=None):
        super(MyMainWindow, self).__init__(parent)
        self.setupUI(self)
        self.initUI()
        self.initList()

    def initUI(self):
        self.clearButton.clicked.connect(self.initList)
        self.renameButton.clicked.connect(self.startRename)

    def initList(self):
        self.file_list = []
        self.video_list = []
        self.sc_list = []
        self.tc_list = []
        self.trash_list = []
        self.table.clearContents()
        self.table.setRowCount(0)
        self.messageLabel.setText("")

    def dragEnterEvent(self, event):
        event.acceptProposedAction()

    def dropEvent(self, event):
        # 计时
        start_time = time.time()

        # 获取并格式化本地路径
        raw_file_list = event.mimeData().urls()
        self.file_list = formatRawFileList(raw_file_list, self.file_list)

        # 分类视频与简繁字幕
        self.split_list = splitList(self.file_list)
        self.video_list = self.split_list[0]
        self.sc_list = self.split_list[1]
        self.tc_list = self.split_list[2]
        self.showInTable()

        # 计时
        end_time = time.time()
        execution_time = end_time - start_time
        execution_ms = execution_time * 1000
        if execution_ms > 1000:
            execution_time = "{:.2f}".format(execution_time)  # 取 2 位小数
            self.showInfo("success", "添加成功", f"耗时{execution_time}s")
        else:
            execution_ms = "{:.0f}".format(execution_ms)  # 舍弃小数
            self.showInfo("success", "添加成功", f"耗时{execution_ms}ms")

    def showInTable(self):
        # 计算列表行数
        max_len = max(len(self.video_list), len(self.sc_list), len(self.tc_list))
        self.table.setRowCount(max_len)

        video_id = 0
        for video_name in self.video_list:
            video_name_lonely = os.path.basename(video_name)
            self.table.setItem(video_id, 0, QTableWidgetItem(video_name_lonely))
            self.table.resizeColumnsToContents()  # 自动匹配列宽
            video_id += 1

        sc_id = 0
        for sc_name in self.sc_list:
            sc_name_lonely = os.path.basename(sc_name)
            self.table.setItem(sc_id, 1, QTableWidgetItem(sc_name_lonely))
            self.table.resizeColumnsToContents()  # 自动匹配列宽
            sc_id += 1

        tc_id = 0
        for tc_name in self.tc_list:
            tc_name_lonely = os.path.basename(tc_name)
            self.table.setItem(tc_id, 2, QTableWidgetItem(tc_name_lonely))
            self.table.resizeColumnsToContents()  # 自动匹配列宽
            tc_id += 1

    def startRename(self):
        # 是否有视频与字幕文件
        if not self.video_list:
            self.showInfo("warning", "", "请添加视频文件")
            return

        if not self.sc_list and not self.tc_list:
            self.showInfo("warning", "", "请添加字幕文件")
            return

        # 勾选的语言下必须存在字幕文件
        if self.allowSc.isChecked() and not self.sc_list \
                or self.allowTc.isChecked() and not self.tc_list:
            if not self.sc_list:
                self.showInfo("error", "", "未发现待命名的简体字幕文件，请确认勾选情况")
                return
            elif not self.tc_list:
                self.showInfo("error", "", "未发现待命名的繁体字幕文件，请确认勾选情况")
                return

        # 必须勾选简体或繁体
        if not self.allowSc.isChecked() and not self.allowTc.isChecked():
            self.showInfo("error", "", "请勾选需要重命名的字幕格式：简体或繁体")
            return

        # 简体繁体的扩展名不可相同
        if self.allowSc.isChecked() and self.allowTc.isChecked() \
                and self.tcFormat.currentText() == self.scFormat.currentText():
            self.showInfo("error", "", "简体扩展名与繁体扩展名不可相同")
            return

        # 视频与字幕个数需相等
        if len(self.sc_list) != 0 and len(self.video_list) != len(self.sc_list) \
                or len(self.tc_list) != 0 and len(self.video_list) != len(self.tc_list):
            self.showInfo("error", "", "视频与字幕的数量不相等")
            return

        # 未勾选的语言加入 delete_list
        delete_list = []
        if not self.allowSc.isChecked():
            delete_list.extend(self.sc_list)
        if not self.allowTc.isChecked():
            delete_list.extend(self.tc_list)

        # 删除未勾选的语言
        if self.deleteSub.isChecked() and delete_list:
            # 获得 delete_list 文件名
            delete_name_list = []
            for item in delete_list:
                item_lonely = os.path.basename(item)
                delete_name_list.append(item_lonely)

            # 弹窗提醒待删除文件
            delete_file = "<br>".join(delete_name_list)  # 转为字符串形式
            notice = MessageBox("下列文件将被删除", delete_file, self)
            if notice.exec():
                send2trash.send2trash(delete_list)
            else:
                return

        # 字幕重命名
        if self.allowSc.isChecked():
            state_sc = renameAction(self.scFormat.currentText(), self.video_list, self.sc_list)
            if state_sc == 516:
                self.showInfo("error", "重命名失败", "目标文件夹存在同名的简体字幕")
                return

        if self.allowTc.isChecked():
            state_tc = renameAction(self.tcFormat.currentText(), self.video_list, self.tc_list)
            if state_tc == 516:
                self.showInfo("error", "重命名失败", "目标文件夹存在同名的繁体字幕")
                return

        self.initList()
        self.showInfo("success", "", "重命名成功")

    def showInfo(self, state, title, content):
        if state == "success":
            InfoBar.success(
                title=title, content=content,
                orient=Qt.Horizontal, isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000, parent=self
            )
        elif state == "warning":
            InfoBar.warning(
                title=title, content=content,
                orient=Qt.Horizontal, isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000, parent=self
            )
        elif state == "error":
            InfoBar.error(
                title=title, content=content,
                orient=Qt.Horizontal, isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000, parent=self
            )
