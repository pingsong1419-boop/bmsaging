from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QLineEdit, QPushButton, QGroupBox, QDoubleSpinBox, 
                               QGridLayout, QComboBox)
from PySide6.QtCore import Qt

class PowerTab(QWidget):
    def __init__(self, device_manager=None):
        super().__init__()
        self.mgr = device_manager
        self._init_ui()
        
    def _init_ui(self):
        layout = QVBoxLayout(self)
        
        # 1. 串口配置
        config_group = QGroupBox("RS485 电源通讯配置")
        config_layout = QHBoxLayout()
        config_layout.addWidget(QLabel("串口号:"))
        self.combo_port = QComboBox()
        self.combo_port.addItems(["COM1", "COM2", "COM3", "COM4", "COM5"])
        self.combo_port.setCurrentText("COM3")
        config_layout.addWidget(self.combo_port)
        
        config_layout.addWidget(QLabel("从机地址(ID):"))
        self.spin_id = QDoubleSpinBox()
        self.spin_id.setRange(1, 255)
        self.spin_id.setDecimals(0)
        config_layout.addWidget(self.spin_id)
        
        self.btn_connect = QPushButton("连接电源")
        self.btn_connect.setStyleSheet("background-color: #007BFF;")
        self.btn_connect.clicked.connect(self.connect_power)
        config_layout.addWidget(self.btn_connect)

        self.btn_disconnect = QPushButton("断开连接")
        self.btn_disconnect.setStyleSheet("background-color: #6C757D;")
        self.btn_disconnect.clicked.connect(self.disconnect_power)
        self.btn_disconnect.setEnabled(False)
        config_layout.addWidget(self.btn_disconnect)

        config_group.setLayout(config_layout)

        layout.addWidget(config_group)
        
        # 2. 手动控制
        ctrl_group = QGroupBox("手动控制与回读")
        ctrl_layout = QGridLayout()
        
        ctrl_layout.addWidget(QLabel("设定电压 (V):"), 0, 0)
        self.spin_volt = QDoubleSpinBox()
        self.spin_volt.setRange(0, 100)
        self.spin_volt.setValue(12.0)
        ctrl_layout.addWidget(self.spin_volt, 0, 1)
        
        self.btn_set = QPushButton("执行设置")
        self.btn_set.clicked.connect(self.set_power_volt)
        ctrl_layout.addWidget(self.btn_set, 0, 2)
        
        ctrl_layout.addWidget(QLabel("输出控制:"), 1, 0)
        self.btn_on = QPushButton("开启输出 (ON)")
        self.btn_on.setStyleSheet("background-color: #218838;")
        self.btn_on.clicked.connect(lambda: self.control_power_output(True))
        ctrl_layout.addWidget(self.btn_on, 1, 1)

        
        self.btn_off = QPushButton("关闭输出 (OFF)")
        self.btn_off.setStyleSheet("background-color: #C82333;")
        self.btn_off.clicked.connect(lambda: self.control_power_output(False))
        ctrl_layout.addWidget(self.btn_off, 1, 2)

        
        ctrl_layout.addWidget(QLabel("实时回读值:"), 2, 0)
        self.lbl_readback = QLabel("0.00 V")
        self.lbl_readback.setStyleSheet("font-size: 36px; color: #00E5FF; font-weight: bold;")
        ctrl_layout.addWidget(self.lbl_readback, 2, 1, 1, 2)
        
        self.btn_read = QPushButton("立即刷新数据")
        self.btn_read.clicked.connect(self.refresh_data)
        ctrl_layout.addWidget(self.btn_read, 3, 1, 1, 2)
        
        ctrl_group.setLayout(ctrl_layout)
        layout.addWidget(ctrl_group)
        layout.addStretch()

    def connect_power(self):
        if self.mgr:
            self.mgr.power_board.port = self.combo_port.currentText()
            self.mgr.power_board.slave_id = int(self.spin_id.value())
            if self.mgr.power_board.connect():
                self.btn_connect.setText("已连接")
                self.btn_connect.setStyleSheet("background-color: #28A745;")
                self.btn_connect.setEnabled(False)
                self.btn_disconnect.setEnabled(True)

    def disconnect_power(self):
        if self.mgr:
            self.mgr.power_board.disconnect()
            self.btn_connect.setText("连接电源")
            self.btn_connect.setStyleSheet("background-color: #007BFF;")
            self.btn_connect.setEnabled(True)
            self.btn_disconnect.setEnabled(False)


    def set_power_volt(self):
        if self.mgr:
            v = self.spin_volt.value()
            res = self.mgr.power_board.set_voltage(v)
            self._notify_status(f"功能板电源：设置电压 {v}V {'成功' if res else '失败'}")

    def control_power_output(self, state):
        if self.mgr:
            res = self.mgr.power_board.output_control(state)
            action = "开启" if state else "关闭"
            self._notify_status(f"功能板电源：{action}输出 {'成功' if res else '失败'}")

    def _notify_status(self, msg):
        """向上寻址找到主窗口并显示状态"""
        p = self.parent()
        while p:
            if hasattr(p, "show_status"):
                p.show_status(msg)
                break
            p = p.parent()


    def refresh_data(self):
        if self.mgr:
            v = self.mgr.power_board.read_voltage()
            if v >= 0:
                self.lbl_readback.setText(f"{v:.2f} V")
            else:
                self.lbl_readback.setText("读取失败")
