from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                               QLabel, QTableWidget, QTableWidgetItem, 
                               QHeaderView, QGroupBox, QLineEdit, QPushButton)
from PySide6.QtCore import Qt

class HardwareTab(QWidget):
    def __init__(self):
        super().__init__()
        self._init_ui()
        
    def _init_ui(self):
        layout = QHBoxLayout(self)
        
        # 左侧：通讯参数等全局配置
        left_panel = QVBoxLayout()
        group_com = QGroupBox("外设与通讯参数配置")
        com_layout = QVBoxLayout()
        com_layout.addWidget(QLabel("语音播报模块 COM 口:"))
        com_layout.addWidget(QLineEdit("COM3"))
        com_layout.addWidget(QLabel("波特率:"))
        com_layout.addWidget(QLineEdit("9600"))
        com_layout.addWidget(QLabel("老化测试机 IP 地址:"))
        com_layout.addWidget(QLineEdit("192.168.1.100"))
        
        btn_save_com = QPushButton("保存通讯配置")
        com_layout.addWidget(btn_save_com)
        com_layout.addStretch()
        group_com.setLayout(com_layout)
        left_panel.addWidget(group_com)
        layout.addLayout(left_panel, 1)
        
        # 右侧：货架码与测试通道映射配置
        right_panel = QVBoxLayout()
        group_map = QGroupBox("货架码与测试通道匹配表 (用于扫码入站自动定位)")
        map_layout = QVBoxLayout()
        
        self.map_table = QTableWidget()
        self.map_table.setColumnCount(2)
        self.map_table.setHorizontalHeaderLabels(["软件测试通道号", "绑定的货架码 (扫描用)"])
        self.map_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        
        # 初始化 60 个通道的配置表格
        self.map_table.setRowCount(60)
        for i in range(60):
            ch_item = QTableWidgetItem(f"CH-{i+1:02d}")
            # 设置通道号列为不可编辑
            ch_item.setFlags(ch_item.flags() & ~Qt.ItemIsEditable if hasattr(Qt, 'ItemIsEditable') else ch_item.flags())
            self.map_table.setItem(i, 0, ch_item)
            
            # 预设货架码
            self.map_table.setItem(i, 1, QTableWidgetItem(f"SHELF-{i+1:03d}"))
            
        map_layout.addWidget(self.map_table)
        
        btn_layout = QHBoxLayout()
        btn_layout.addWidget(QPushButton("导入 Excel 配置"))
        btn_layout.addWidget(QPushButton("保存匹配映射表"))
        map_layout.addLayout(btn_layout)
        
        group_map.setLayout(map_layout)
        right_panel.addWidget(group_map)
        
        layout.addLayout(right_panel, 2)
