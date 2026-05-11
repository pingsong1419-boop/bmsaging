from pymodbus.client import ModbusTcpClient
from pymodbus.framer import FramerType
from pymodbus.exceptions import ModbusException
import logging
import threading

# 配置日志
import logging
logging.basicConfig()
log = logging.getLogger()
log.setLevel(logging.INFO)

class AFEPowerRU36:
    """
    万瑞达电气 (YunXingHe) RU36/RU60 电源驱动
    完美对齐 V1.4 协议手册 + 实际倍率反馈
    """
    def __init__(self, ip: str, port: int = 2000):
        self.ip = ip
        self.port = port
        self.unit_id = 1
        # 协议明确为 Modbus TCP 结构，使用 SOCKET Framer
        self.client = ModbusTcpClient(
            self.ip, 
            port=self.port, 
            framer=FramerType.SOCKET,
            timeout=2,
            retries=1
        )
        self.lock = threading.Lock()
        self.is_connected = False

    def connect(self) -> bool:
        with self.lock:
            try:
                if self.client.comm_params.host != self.ip or self.client.comm_params.port != self.port:
                    try: self.client.close()
                    except: pass
                    self.client = ModbusTcpClient(
                        self.ip, 
                        port=self.port, 
                        framer=FramerType.SOCKET,
                        timeout=2,
                        retries=1
                    )
                if self.client.connect():
                    self.is_connected = True
                    return True
                return False
            except Exception:
                return False

    def disconnect(self):
        with self.lock:
            self.client.close()
            self.is_connected = False

    def set_voltage(self, voltage: float) -> bool:
        """设置电压 (十进制地址 149, 倍率 10)"""
        with self.lock:
            if not self.is_connected: return False
            try:
                # 根据反馈: 设置 8V 得到 80V (发送了 800), 说明实际倍率是 10
                val = int(round(voltage * 10))
                result = self.client.write_register(149, val, device_id=self.unit_id)
                return not result.isError()
            except Exception:
                return False

    def set_current(self, current: float) -> bool:
        """设置电流 (十进制地址 150, 倍率 10)"""
        with self.lock:
            if not self.is_connected: return False
            try:
                val = int(round(current * 10))
                result = self.client.write_register(150, val, device_id=self.unit_id)
                return not result.isError()
            except Exception:
                return False

    def output_control(self, state: bool) -> bool:
        """输出控制 (十进制线圈地址 133)"""
        with self.lock:
            if not self.is_connected: return False
            try:
                result = self.client.write_coil(133, state, device_id=self.unit_id)
                return not result.isError()
            except Exception:
                return False

    def measure_voltage(self) -> float:
        """测量电压 (十进制输入寄存器地址 100, 倍率 10)"""
        with self.lock:
            if not self.is_connected: return -1.0
            try:
                # 协议 0x04 功能码
                result = self.client.read_input_registers(100, count=1, device_id=self.unit_id)
                if not result or result.isError():
                    return -1.0
                return result.registers[0] / 10.0
            except Exception:
                return -1.0

    def measure_current(self) -> float:
        """测量电流 (十进制输入寄存器地址 101, 倍率 10)"""
        with self.lock:
            if not self.is_connected: return -1.0
            try:
                result = self.client.read_input_registers(101, count=1, device_id=self.unit_id)
                if not result or result.isError():
                    return -1.0
                return result.registers[0] / 10.0
            except Exception:
                return -1.0
