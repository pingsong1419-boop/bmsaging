from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton
from PySide6.QtCore import Qt, Signal

class ScanDialog(QDialog):
    # 扫码完成信号：通道索引(0-59), 货架码, 主机码, 从机码列表
    scan_completed = Signal(int, str, str, list)

    def __init__(self, parent=None, device_manager=None, slaves_count=3):
        super().__init__(parent)
        self.device_manager = device_manager
        self.expected_slaves = slaves_count
        
        self.setWindowTitle("工位扫码入站 - 等待扫码枪输入")
        self.setFixedSize(500, 300)
        # 使用暗黑工业风样式
        self.setStyleSheet("""
            QDialog { background-color: #1F1F35; }
            QLabel { color: #FFFFFF; font-size: 14px; }
            QLineEdit { background-color: #31314C; color: #00E5FF; border: 2px solid #00E5FF; font-size: 16px; padding: 5px; }
            QPushButton { background-color: #DC3545; color: white; padding: 8px; font-weight: bold; border-radius: 4px; }
        """)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        self.lbl_instruction = QLabel("【第一步】请扫描『货架码』：")
        self.lbl_instruction.setStyleSheet("font-size: 22px; font-weight: bold; color: #00E5FF;")
        self.lbl_instruction.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.lbl_instruction)
        
        self.lbl_status = QLabel("等待焦点捕获...")
        self.lbl_status.setAlignment(Qt.AlignCenter)
        self.lbl_status.setStyleSheet("color: #CCCCCC; font-size: 16px;")
        layout.addWidget(self.lbl_status)
        
        # 隐藏/捕获焦点的输入框，始终捕获扫码枪输入
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText(">> 扫码枪数据将自动录入此处 <<")
        self.input_field.setAlignment(Qt.AlignCenter)
        self.input_field.returnPressed.connect(self.process_scan)
        layout.addWidget(self.input_field)
        
        layout.addStretch()
        
        btn_cancel = QPushButton("取消 / 退出扫码")
        btn_cancel.clicked.connect(self.reject)
        layout.addWidget(btn_cancel)
        
        # 内部状态机
        self.current_step = 0 # 0: 货架, 1: 主机, 2: 从机1...
        self.target_channel = -1
        self.scanned_shelf = ""
        self.scanned_master = ""
        self.scanned_slaves = []
        
        self._trigger_voice("请扫描货架码")
        
    def _trigger_voice(self, text):
        if self.device_manager:
            self.device_manager.play_voice(text)
        else:
            print(f"[UI mock语音播报] {text}")
        
    def showEvent(self, event):
        self.input_field.setFocus()
        super().showEvent(event)
        
    def process_scan(self):
        barcode = self.input_field.text().strip()
        self.input_field.clear()
        if not barcode: return
        
        if self.current_step == 0:
            # 货架码阶段
            # 简单模拟: 假如扫描的是 SHELF-001，那么定位到 CH-01
            if barcode.upper().startswith("SHELF-"):
                try:
                    ch_num = int(barcode.split("-")[1])
                    self.target_channel = ch_num - 1 # 0-indexed
                    self.scanned_shelf = barcode
                    self.lbl_status.setText(f"成功锁定通道 CH-{ch_num:02d}。")
                    self.lbl_instruction.setText("【第二步】请扫描『主机码』：")
                    self._trigger_voice("货架绑定成功，请扫描主机码")
                    self.current_step = 1
                except:
                    self.lbl_status.setText("无效的货架码，请重试。(例如 SHELF-001)")
                    self.lbl_status.setStyleSheet("color: #FF4444;")
                    self._trigger_voice("货架码无效")
            else:
                self.lbl_status.setText("未识别为货架码(需以 SHELF- 开头)")
                self.lbl_status.setStyleSheet("color: #FF4444;")
                self._trigger_voice("条码错误")
                
        elif self.current_step == 1:
            # 主机码阶段
            self.scanned_master = barcode
            self.lbl_status.setText(f"主机码 {barcode} 已录入。")
            self.lbl_status.setStyleSheet("color: #CCCCCC;")
            
            if self.expected_slaves > 0:
                self.lbl_instruction.setText("【第三步】请扫描『从机 1』：")
                self._trigger_voice("主机码扫入成功，请扫描一号从机")
                self.current_step = 2
            else:
                # 0从机，直接完成
                self._trigger_voice("扫码全部完成，准备开始测试")
                self.finish_scan()
                
        elif self.current_step >= 2:
            # 从机阶段
            self.scanned_slaves.append(barcode)
            slave_index = self.current_step - 1
            
            if slave_index < self.expected_slaves:
                self.lbl_instruction.setText(f"【第三步】请扫描『从机 {slave_index + 1}』：")
                self.lbl_status.setText(f"从机 {slave_index} ({barcode}) 已录入。")
                
                # 语音支持到3号从机
                voice_dict = {1: "二", 2: "三"}
                next_slave_str = voice_dict.get(slave_index, str(slave_index + 1))
                self._trigger_voice(f"请扫描{next_slave_str}号从机")
                
                self.current_step += 1
            else:
                self._trigger_voice("扫码全部完成，通道即将开始测试")
                self.finish_scan()
                
    def finish_scan(self):
        self.lbl_instruction.setText("入站完成！")
        self.lbl_status.setText("扫码流结束，正在下发配置...")
        self.scan_completed.emit(self.target_channel, self.scanned_shelf, self.scanned_master, self.scanned_slaves)
        self.accept()
