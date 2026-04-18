import sys
import os
import sqlite3
import threading
from pathlib import Path

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QGroupBox, QTextEdit, QSplitter, QProgressBar,
    QAbstractItemView, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QObject
from PyQt6.QtGui import QColor, QFont

from find_by_hash import hash_string_id, find_string_by_hash


def _resource_path(relative_path):
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)


DB_PATH = _resource_path("content.db")

STYLE_SHEET = """
QMainWindow {
    background-color: #1a1a2e;
}
QWidget {
    background-color: #1a1a2e;
    color: #e0e0e0;
    font-family: "Microsoft YaHei", "Segoe UI", sans-serif;
    font-size: 13px;
}
QGroupBox {
    border: 1px solid #3a3a5c;
    border-radius: 8px;
    margin-top: 12px;
    padding: 16px 12px 12px 12px;
    font-weight: bold;
    font-size: 14px;
    color: #7f8cff;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 16px;
    padding: 0 6px;
}
QLineEdit {
    background-color: #16213e;
    border: 1px solid #3a3a5c;
    border-radius: 6px;
    padding: 8px 12px;
    color: #e0e0e0;
    selection-background-color: #7f8cff;
}
QLineEdit:focus {
    border: 1px solid #7f8cff;
}
QPushButton {
    background-color: #7f8cff;
    color: #1a1a2e;
    border: none;
    border-radius: 6px;
    padding: 8px 20px;
    font-weight: bold;
    font-size: 13px;
}
QPushButton:hover {
    background-color: #9aa5ff;
}
QPushButton:pressed {
    background-color: #5c6bc0;
}
QPushButton:disabled {
    background-color: #3a3a5c;
    color: #666;
}
QPushButton#applyBtn {
    background-color: #00c9a7;
    color: #1a1a2e;
}
QPushButton#applyBtn:hover {
    background-color: #2ee8c5;
}
QPushButton#findBtn {
    background-color: #ff6b6b;
    color: #fff;
}
QPushButton#findBtn:hover {
    background-color: #ff8787;
}
QTableWidget {
    background-color: #16213e;
    border: 1px solid #3a3a5c;
    border-radius: 6px;
    gridline-color: #2a2a4a;
    selection-background-color: #3a3a6c;
    selection-color: #fff;
}
QTableWidget::item {
    padding: 6px 10px;
}
QTableWidget::item:hover {
    background-color: #2a2a5c;
}
QHeaderView::section {
    background-color: #0f3460;
    color: #7f8cff;
    border: none;
    padding: 8px 10px;
    font-weight: bold;
    font-size: 12px;
}
QTextEdit {
    background-color: #16213e;
    border: 1px solid #3a3a5c;
    border-radius: 6px;
    padding: 8px 12px;
    color: #e0e0e0;
    selection-background-color: #7f8cff;
}
QProgressBar {
    background-color: #16213e;
    border: 1px solid #3a3a5c;
    border-radius: 6px;
    text-align: center;
    color: #e0e0e0;
    height: 20px;
}
QProgressBar::chunk {
    background-color: #7f8cff;
    border-radius: 5px;
}
QLabel#titleLabel {
    font-size: 22px;
    font-weight: bold;
    color: #7f8cff;
}
QLabel#subtitleLabel {
    font-size: 12px;
    color: #666;
}
QSplitter::handle {
    background-color: #3a3a5c;
    width: 2px;
}
QScrollBar:vertical {
    background-color: #16213e;
    width: 10px;
    border-radius: 5px;
}
QScrollBar::handle:vertical {
    background-color: #3a3a5c;
    border-radius: 5px;
    min-height: 30px;
}
QScrollBar::handle:vertical:hover {
    background-color: #5a5a8c;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}
"""


class WorkerSignals(QObject):
    finished = pyqtSignal(list)
    error = pyqtSignal(str)
    progress = pyqtSignal(str)


class SearchWorker(QObject):
    def __init__(self, keyword, db_path):
        super().__init__()
        self.keyword = keyword
        self.db_path = db_path
        self.signals = WorkerSignals()

    def run(self):
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            cursor.execute(
                "SELECT hash, content FROM content_table WHERE content LIKE ? LIMIT 200",
                (f"%{self.keyword}%",)
            )
            rows = cursor.fetchall()
            conn.close()
            self.signals.finished.emit(rows)
        except Exception as e:
            self.signals.error.emit(str(e))


class FindWorker(QObject):
    def __init__(self, prefix, target_hash, max_suffix_len):
        super().__init__()
        self.prefix = prefix
        self.target_hash = target_hash
        self.max_suffix_len = max_suffix_len
        self.signals = WorkerSignals()

    def run(self):
        try:
            self.signals.progress.emit("正在查找中，请稍候...")
            results = find_string_by_hash(self.prefix, self.target_hash)
            self.signals.finished.emit(results)
        except Exception as e:
            self.signals.error.emit(str(e))


class HashFinderGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("BF1 哈希查找工具")
        self.setMinimumSize(900, 700)
        self.resize(1100, 780)
        self.search_thread = None
        self.find_thread = None
        self._setup_ui()

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(20, 16, 20, 20)
        main_layout.setSpacing(12)

        title = QLabel("BF1 哈希查找工具")
        title.setObjectName("titleLabel")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title)

        subtitle = QLabel("通过 content.db 查询哈希值，并逆向查找原始字符串")
        subtitle.setObjectName("subtitleLabel")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(subtitle)

        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.setHandleWidth(2)
        main_layout.addWidget(splitter, stretch=1)

        top_widget = QWidget()
        top_layout = QVBoxLayout(top_widget)
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(10)

        search_group = QGroupBox("数据库查询")
        search_layout = QVBoxLayout(search_group)
        search_input_row = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("输入关键词搜索 content.db 中的内容...")
        self.search_input.returnPressed.connect(self._on_search)
        search_input_row.addWidget(self.search_input, stretch=1)
        self.search_btn = QPushButton("搜 索")
        self.search_btn.setFixedWidth(100)
        self.search_btn.setStyleSheet(
            "QPushButton { background-color: #7f8cff; color: #1a1a2e; border: none; "
            "border-radius: 6px; padding: 8px 20px; font-weight: bold; }"
            "QPushButton:hover { background-color: #9aa5ff; }"
            "QPushButton:disabled { background-color: #3a3a5c; color: #666; }"
        )
        self.search_btn.clicked.connect(self._on_search)
        search_input_row.addWidget(self.search_btn)
        search_layout.addLayout(search_input_row)

        self.result_table = QTableWidget(0, 3)
        self.result_table.setHorizontalHeaderLabels(["哈希值", "内容", "操作"])
        self.result_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.result_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.result_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.result_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.result_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.result_table.verticalHeader().setVisible(False)
        self.result_table.setAlternatingRowColors(True)
        search_layout.addWidget(self.result_table)

        self.result_count_label = QLabel("")
        self.result_count_label.setStyleSheet("color: #666; font-size: 12px;")
        search_layout.addWidget(self.result_count_label)

        top_layout.addWidget(search_group)
        splitter.addWidget(top_widget)

        bottom_widget = QWidget()
        bottom_layout = QVBoxLayout(bottom_widget)
        bottom_layout.setContentsMargins(0, 0, 0, 0)
        bottom_layout.setSpacing(10)

        find_group = QGroupBox("哈希逆向查找")
        find_layout = QVBoxLayout(find_group)

        param_row = QHBoxLayout()
        param_row.addWidget(QLabel("前缀 (Prefix):"))
        self.prefix_input = QLineEdit()
        self.prefix_input.setPlaceholderText("例如: daizhu")
        self.prefix_input.setFixedWidth(200)
        param_row.addWidget(self.prefix_input)

        param_row.addSpacing(20)

        param_row.addWidget(QLabel("目标哈希:"))
        self.target_hash_input = QLineEdit()
        self.target_hash_input.setPlaceholderText("例如: 7D543A64")
        self.target_hash_input.setFixedWidth(200)
        param_row.addWidget(self.target_hash_input)

        param_row.addSpacing(20)

        param_row.addWidget(QLabel("最大后缀长度:"))
        self.max_suffix_input = QLineEdit("8")
        self.max_suffix_input.setFixedWidth(60)
        param_row.addWidget(self.max_suffix_input)

        param_row.addStretch()

        self.find_btn = QPushButton("开 始 查 找")
        self.find_btn.setObjectName("findBtn")
        self.find_btn.setFixedWidth(130)
        self.find_btn.setStyleSheet(
            "QPushButton { background-color: #ff6b6b; color: #fff; border: none; "
            "border-radius: 6px; padding: 8px 20px; font-weight: bold; }"
            "QPushButton:hover { background-color: #ff8787; }"
            "QPushButton:disabled { background-color: #3a3a5c; color: #666; }"
        )
        self.find_btn.clicked.connect(self._on_find)
        param_row.addWidget(self.find_btn)

        find_layout.addLayout(param_row)

        self.progress_label = QLabel("")
        self.progress_label.setStyleSheet("color: #7f8cff; font-size: 12px;")
        find_layout.addWidget(self.progress_label)

        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        self.result_text.setMaximumHeight(180)
        self.result_text.setPlaceholderText("查找结果将显示在这里...")
        find_layout.addWidget(self.result_text)

        bottom_layout.addWidget(find_group)
        splitter.addWidget(bottom_widget)

        splitter.setSizes([400, 300])

    def _on_search(self):
        keyword = self.search_input.text().strip()
        if not keyword:
            QMessageBox.warning(self, "提示", "请输入搜索关键词")
            return

        self.search_btn.setEnabled(False)
        self.search_btn.setText("搜索中...")
        self.result_table.setRowCount(0)
        self.result_count_label.setText("正在查询...")

        self._search_worker = SearchWorker(keyword, DB_PATH)
        self._search_thread = threading.Thread(target=self._search_worker.run, daemon=True)
        self._search_worker.signals.finished.connect(self._on_search_done)
        self._search_worker.signals.error.connect(self._on_search_error)
        self._search_thread.start()

    def _on_search_done(self, rows):
        self.search_btn.setEnabled(True)
        self.search_btn.setText("搜 索")
        self.result_table.setRowCount(len(rows))

        for i, (hash_val, content) in enumerate(rows):
            hash_item = QTableWidgetItem(hash_val)
            hash_item.setForeground(QColor("#7f8cff"))
            self.result_table.setItem(i, 0, hash_item)

            content_item = QTableWidgetItem(content)
            self.result_table.setItem(i, 1, content_item)

            apply_btn = QPushButton("应用")
            apply_btn.setObjectName("applyBtn")
            apply_btn.setFixedSize(60, 28)
            apply_btn.setStyleSheet(
                "QPushButton { background-color: #00c9a7; color: #1a1a2e; border: none; "
                "border-radius: 4px; font-weight: bold; font-size: 12px; }"
                "QPushButton:hover { background-color: #2ee8c5; }"
                "QPushButton:pressed { background-color: #00a88a; }"
            )
            apply_btn.clicked.connect(lambda checked, h=hash_val: self._apply_hash(h))
            self.result_table.setCellWidget(i, 2, apply_btn)

        self.result_count_label.setText(f"共找到 {len(rows)} 条结果" + ("（已限制最多200条）" if len(rows) >= 200 else ""))

    def _on_search_error(self, err):
        self.search_btn.setEnabled(True)
        self.search_btn.setText("搜 索")
        self.result_count_label.setText(f"查询出错: {err}")

    def _apply_hash(self, hash_val):
        self.target_hash_input.setText(hash_val)
        self.target_hash_input.setFocus()
        self.progress_label.setText(f"已填入哈希值: {hash_val}")

    def _on_find(self):
        prefix = self.prefix_input.text().strip()
        target_hash = self.target_hash_input.text().strip()

        if not prefix:
            QMessageBox.warning(self, "提示", "请输入前缀")
            return
        if not target_hash:
            QMessageBox.warning(self, "提示", "请输入目标哈希值")
            return

        try:
            max_suffix_len = int(self.max_suffix_input.text().strip())
        except ValueError:
            QMessageBox.warning(self, "提示", "最大后缀长度必须为整数")
            return

        self.find_btn.setEnabled(False)
        self.find_btn.setText("查找中...")
        self.result_text.clear()
        self.progress_label.setText("正在查找中，请稍候...")

        self._find_worker = FindWorker(prefix, target_hash, max_suffix_len)
        self._find_thread = threading.Thread(target=self._find_worker.run, daemon=True)
        self._find_worker.signals.finished.connect(self._on_find_done)
        self._find_worker.signals.error.connect(self._on_find_error)
        self._find_worker.signals.progress.connect(self._on_find_progress)
        self._find_thread.start()

    def _on_find_progress(self, msg):
        self.progress_label.setText(msg)

    def _on_find_done(self, results):
        self.find_btn.setEnabled(True)
        self.find_btn.setText("开 始 查 找")

        if not results:
            self.result_text.setHtml('<span style="color: #ff6b6b;">未找到匹配的字符串</span>')
            self.progress_label.setText("查找完成 - 无匹配结果")
            return

        html_parts = [
            f'<span style="color: #00c9a7; font-weight: bold;">共找到 {len(results)} 个匹配:</span><br><br>'
        ]
        for i, s in enumerate(results):
            verified_hash = hex(hash_string_id(s))[2:].upper()
            suffix_len = len(s) - len(self.prefix_input.text().strip())
            html_parts.append(
                f'<span style="color: #7f8cff;">[{i + 1}]</span> '
                f'<span style="color: #e0e0e0; font-size: 15px; font-weight: bold;">{s}</span><br>'
                f'&nbsp;&nbsp;&nbsp;&nbsp;哈希验证: <span style="color: #00c9a7;">{verified_hash}</span> '
                f'后缀长度: <span style="color: #ff6b6b;">{suffix_len}</span><br><br>'
            )

        self.result_text.setHtml("".join(html_parts))
        self.progress_label.setText(f"查找完成 - 找到 {len(results)} 个匹配")

    def _on_find_error(self, err):
        self.find_btn.setEnabled(True)
        self.find_btn.setText("开 始 查 找")
        self.result_text.setHtml(f'<span style="color: #ff6b6b;">查找出错: {err}</span>')
        self.progress_label.setText("查找出错")


def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(STYLE_SHEET)
    window = HashFinderGUI()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
