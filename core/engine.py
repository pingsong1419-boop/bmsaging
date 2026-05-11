from enum import Enum
from typing import List, Dict, Optional
from PySide6.QtCore import QObject, Signal, QThread, QTimer

class NGStrategy(Enum):
    STOP_ON_ANY = "任何NG停止"
    STOP_ON_CRITICAL = "关键NG停止"
    CONTINUE_ON_NG = "NG继续"

class StepType(Enum):
    CHARGE = "充电"
    DISCHARGE = "放电"
    REST = "静置"
    OCV_CHECK = "OCV检查"

class TestStep:
    def __init__(self, name: str, step_type: StepType, target_value: float, duration: int, ng_strategy: NGStrategy):
        self.name = name
        self.step_type = step_type
        self.target_value = target_value
        self.duration = duration
        self.ng_strategy = ng_strategy

class ChannelWorker(QObject):
    """
    单个通道的测试执行器
    """
    step_started = Signal(int, str)  # channel_id, step_name
    progress_updated = Signal(int, float, dict)  # channel_id, progress%, data
    step_finished = Signal(int, str, bool)  # channel_id, step_name, is_pass
    test_finished = Signal(int, bool)  # channel_id, is_total_pass
    log_message = Signal(int, str)

    def __init__(self, channel_id: int, steps: List[TestStep]):
        super().__init__()
        self.channel_id = channel_id
        self.steps = steps
        self.is_running = False
        self.current_step_index = 0

    def start(self):
        self.is_running = True
        self.run_next_step()

    def stop(self):
        self.is_running = False

    def run_next_step(self):
        if not self.is_running or self.current_step_index >= len(self.steps):
            self.test_finished.emit(self.channel_id, True)
            return

        step = self.steps[self.current_step_index]
        self.step_started.emit(self.channel_id, step.name)
        
        # 模拟工步执行过程
        # 实际开发中这里会对接 BMS 协议和老化机协议
        QTimer.singleShot(1000, self.on_step_complete)

    def on_step_complete(self):
        if not self.is_running: return
        
        step = self.steps[self.current_step_index]
        is_pass = True # 模拟逻辑
        
        self.step_finished.emit(self.channel_id, step.name, is_pass)
        
        if not is_pass:
            if step.ng_strategy == NGStrategy.STOP_ON_ANY:
                self.log_message.emit(self.channel_id, f"工步 {step.name} NG, 根据策略停止测试")
                self.test_finished.emit(self.channel_id, False)
                return
            # 其他策略继续...

        self.current_step_index += 1
        self.run_next_step()

class TestEngine(QObject):
    """
    多通道并行测试引擎
    """
    def __init__(self):
        super().__init__()
        self.workers: Dict[int, ChannelWorker] = {}
        self.threads: Dict[int, QThread] = {}

    def start_channel_test(self, channel_id: int, recipe: List[TestStep]):
        if channel_id in self.workers:
            self.stop_channel_test(channel_id)

        thread = QThread()
        worker = ChannelWorker(channel_id, recipe)
        worker.moveToThread(thread)
        
        thread.started.connect(worker.start)
        # 信号连接逻辑...
        
        self.workers[channel_id] = worker
        self.threads[channel_id] = thread
        thread.start()

    def stop_channel_test(self, channel_id: int):
        if channel_id in self.threads:
            self.workers[channel_id].stop()
            self.threads[channel_id].quit()
            self.threads[channel_id].wait()
            del self.workers[channel_id]
            del self.threads[channel_id]
