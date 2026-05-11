from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                               QLineEdit, QComboBox, QPushButton, QDoubleSpinBox, QSpinBox, QStackedWidget, QWidget)
from PySide6.QtCore import Qt

class StepDialog(QDialog):
    def __init__(self, parent=None, step_data=None):
        super().__init__(parent)
        self.setWindowTitle("编辑工步指令 (设备控制)")
        self.setFixedSize(450, 500)
        self.setStyleSheet("background-color: #1F1F35; color: white;")
        
        layout = QVBoxLayout(self)
        
        # 1. 选择控制设备
        layout.addWidget(QLabel("控制设备:"))
        self.device_combo = QComboBox()
        self.device_combo.addItems(["程控电源 (DC Source)", "电子负载 (E-Load)", "BMS 控制", "系统指令 (System)"])
        layout.addWidget(self.device_combo)
        
        # 2. 选择功能/动作 (根据设备动态切换)
        layout.addWidget(QLabel("功能动作:"))
        self.action_combo = QComboBox()
        layout.addWidget(self.action_combo)
        
        # 3. 参数配置区
        self.param_stack = QStackedWidget()
        
        # --- 页面 0: 电源参数 ---
        self.page_power = QWidget()
        p_layout = QVBoxLayout(self.page_power)
        p_layout.addWidget(QLabel("设置电压 (V):"))
        self.p_volt = QDoubleSpinBox()
        self.p_volt.setRange(0, 1000)
        p_layout.addWidget(self.p_volt)
        p_layout.addWidget(QLabel("限制电流 (A):"))
        self.p_curr = QDoubleSpinBox()
        self.p_curr.setRange(0, 500)
        p_layout.addWidget(self.p_curr)
        p_layout.addStretch()
        
        # --- 页面 1: 负载参数 ---
        self.page_load = QWidget()
        l_layout = QVBoxLayout(self.page_load)
        l_layout.addWidget(QLabel("放电电流 (A):"))
        self.l_curr = QDoubleSpinBox()
        self.l_curr.setRange(0, 500)
        l_layout.addWidget(self.l_curr)
        l_layout.addWidget(QLabel("截止电压 (V):"))
        self.l_volt = QDoubleSpinBox()
        self.l_volt.setRange(0, 1000)
        l_layout.addWidget(self.l_volt)
        l_layout.addStretch()

        # --- 页面 2: 系统参数 (延时) ---
        self.page_sys = QWidget()
        s_layout = QVBoxLayout(self.page_sys)
        s_layout.addWidget(QLabel("延时/执行时间 (秒):"))
        self.s_time = QSpinBox()
        self.s_time.setRange(0, 86400)
        s_layout.addWidget(self.s_time)
        s_layout.addStretch()

        self.param_stack.addWidget(self.page_power)
        self.param_stack.addWidget(self.page_load)
        self.param_stack.addWidget(self.page_sys)
        layout.addWidget(self.param_stack)
        
        # 信号连接
        self.device_combo.currentIndexChanged.connect(self.on_device_changed)
        
        # 初始化界面
        self.on_device_changed(0)
        
        layout.addStretch()
        
        # 按钮
        btn_layout = QHBoxLayout()
        self.btn_ok = QPushButton("确认指令")
        self.btn_ok.setStyleSheet("background-color: #28A745; font-weight: bold;")
        self.btn_ok.clicked.connect(self.accept)
        
        self.btn_cancel = QPushButton("取消")
        self.btn_cancel.clicked.connect(self.reject)
        
        btn_layout.addWidget(self.btn_ok)
        btn_layout.addWidget(self.btn_cancel)
        layout.addLayout(btn_layout)

    def on_device_changed(self, index):
        self.action_combo.clear()
        if index == 0: # 电源
            self.action_combo.addItems(["CV 输出", "CC 输出", "关闭输出"])
            self.param_stack.setCurrentIndex(0)
        elif index == 1: # 负载
            self.action_combo.addItems(["CC 放电", "CP 放电", "关闭负载"])
            self.param_stack.setCurrentIndex(1)
        elif index == 2: # BMS
            self.action_combo.addItems(["读取实时数据", "闭合继电器", "断开继电器", "清除故障"])
            self.param_stack.setCurrentIndex(2) # 暂时用系统页面
        elif index == 3: # 系统
            self.action_combo.addItems(["等待/延时", "人工确认", "跳转至工步"])
            self.param_stack.setCurrentIndex(2)

    def get_data(self):
        device = self.device_combo.currentText()
        action = self.action_combo.currentText()
        
        # 简单拼接一个描述字符串作为工步名称
        params = ""
        if self.param_stack.currentIndex() == 0:
            params = f"{self.p_volt.value()}V/{self.p_curr.value()}A"
        elif self.param_stack.currentIndex() == 1:
            params = f"{self.l_curr.value()}A (截止{self.l_volt.value()}V)"
        elif self.param_stack.currentIndex() == 2:
            params = f"{self.s_time.value()}s"
            
        return {
            'device': device,
            'action': action,
            'params': params,
            'name': f"{device}-{action} ({params})"
        }
