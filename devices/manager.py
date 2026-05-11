from .lingtu_66100 import Lingtu66100
from .power_supply import PowerSupply485
from .ngi_n3618 import NGIN3618
from .afe_power_ru36 import AFEPowerRU36
from .mainboard_power_ru60 import MainboardPowerRU60


class DeviceManager:
    """
    设备驱动统一管理类 (单例模式)
    负责解耦和管理所有的硬件仪器：电池模拟器、RS485电源、扫码枪、语音模块等。
    """
    def __init__(self):
        # 1. 领图 66100 电池模拟器 (三台设备)
        self.simulators = [
            Lingtu66100(ip="192.168.1.210"), # Unit 1 (CH 1-18)
            Lingtu66100(ip="192.168.1.211"), # Unit 2 (CH 19-36)
            Lingtu66100(ip="192.168.1.212"), # Unit 3 (CH 37-54)
            Lingtu66100(ip="192.168.1.213")  # Unit 4
        ]
        
        # 2. 功能板供电电源 (默认串口)
        self.power_board = PowerSupply485(port="COM3")
        
        # 3. NGI N3618 高压直流电源
        self.hv_source = NGIN3618(ip="192.168.1.190", port=7000)
        
        # 4. 1#AFE 供电电源 (RU36-100V36A)
        self.afe_power_1 = AFEPowerRU36(ip="192.168.1.200", port=2000)
        
        # 5. 主机供电电源 (RU60-30V200A)
        self.mainboard_power = MainboardPowerRU60(ip="192.168.1.201", port=2000)



        
        # 3. 语音模块状态
        self.voice_enabled = True

    def _get_sim_and_ch(self, global_ch: int):
        """
        根据全局通道号 (1-60) 自动路由到具体的物理设备和物理通道
        """
        unit_index = (global_ch - 1) // 18
        local_ch = (global_ch - 1) % 18 + 1
        
        if unit_index < len(self.simulators):
            return self.simulators[unit_index], local_ch
        return None, None

    def set_voltage(self, global_ch: int, voltage: float):
        sim, ch = self._get_sim_and_ch(global_ch)
        if sim: sim.set_voltage(ch, voltage)

    def output_control(self, global_ch: int, state: bool):
        sim, ch = self._get_sim_and_ch(global_ch)
        if sim: sim.output_control(ch, state)

    def measure_voltage(self, global_ch: int) -> float:
        sim, ch = self._get_sim_and_ch(global_ch)
        if sim: return sim.measure_voltage(ch)
        return -1.0

    def broadcast_voltage(self, voltage: float) -> bool:
        """
        全系统广播设置电压：对所有连接的模拟器发送 0 号通道指令
        """
        print(f"[*] 全系统同步设置电压: {voltage}V")
        success = True
        for sim in self.simulators:
            if sim.is_connected:
                if not sim.set_voltage(0, voltage):
                    success = False
        return success

    def broadcast_output(self, state: bool) -> bool:
        """
        全系统广播输出控制：开启/关闭所有模拟器输出
        """
        print(f"[*] 全系统同步输出控制: {state}")
        success = True
        for sim in self.simulators:
            if sim.is_connected:
                if not sim.output_control(0, state):
                    success = False
        return success



    def init_all_devices(self):
        """初始化连接所有硬件"""
        results = [sim.connect() for sim in self.simulators]
        results.append(self.power_board.connect())
        return all(results)

    def disconnect_all(self):
        """安全断开所有硬件连接"""
        print("正在断开所有硬件设备连接...")
        for sim in self.simulators:
            sim.disconnect()
        self.power_board.disconnect()
        self.hv_source.disconnect()
        self.afe_power_1.disconnect()
        self.mainboard_power.disconnect()




    def play_voice(self, text: str):
        if self.voice_enabled:
            print(f"[语音模块] 🔊 正在播报: {text}")

    def emergency_stop(self):
        """紧急停止：关闭所有电源和负载输出"""
        print("!!! 触发紧急停止 !!!")
        for i in range(1, 61):
            self.output_control(i, False)
        self.power_board.set_output(False)
