import serial
import struct

class PowerSupply485:
    """
    功能板供电电源驱动 (RS485 - Modbus RTU 协议)
    不依赖第三方库，直接使用 pyserial 实现 Modbus 核心逻辑
    """
    def __init__(self, port: str, baudrate: int = 9600, slave_id: int = 1):
        self.port = port
        self.baudrate = baudrate
        self.slave_id = slave_id
        self.ser = None

    def connect(self) -> bool:
        try:
            self.ser = serial.Serial(self.port, self.baudrate, timeout=0.5)
            return self.ser.is_open
        except Exception as e:
            print(f"[PowerSupply] 串口连接失败: {e}")
            return False

    def disconnect(self):
        """关闭串口连接"""
        if self.ser and self.ser.is_open:
            self.ser.close()
        self.ser = None


    def _calculate_crc(self, data):
        """Modbus CRC16 计算"""
        crc = 0xFFFF
        for pos in data:
            crc ^= pos
            for i in range(8):
                if (crc & 1) != 0:
                    crc >>= 1
                    crc ^= 0xA001
                else:
                    crc >>= 1
        return crc

    def _notify_status(self, success: bool, action: str):
        if not success:
            print(f"[PowerSupply] {action} 失败")

    def set_voltage(self, voltage: float) -> bool:
        """设置电压 (地址 0x0001)"""
        if not self.ser: return False
        val = int(voltage * 100)
        cmd = struct.pack('>BBHH', self.slave_id, 0x06, 0x0001, val)
        crc = self._calculate_crc(cmd)
        cmd += struct.pack('<H', crc)
        self.ser.write(cmd)
        # 读取回报确认 (Modbus 06 码通常原样返回)
        resp = self.ser.read(8)
        success = len(resp) == 8
        self._notify_status(success, "设置电压")
        return success

    def output_control(self, state: bool) -> bool:
        """控制输出 (地址 0x0000)"""
        if not self.ser: return False
        val = 0x0001 if state else 0x0000
        cmd = struct.pack('>BBHH', self.slave_id, 0x06, 0x0000, val)
        crc = self._calculate_crc(cmd)
        cmd += struct.pack('<H', crc)
        self.ser.write(cmd)
        resp = self.ser.read(8)
        success = len(resp) == 8
        self._notify_status(success, "控制输出")
        return success

    def read_voltage(self) -> float:
        """读取电压回读值 (0x0064) - 功能码 0x04 (Read Input Registers)"""
        if not self.ser: return -1.0
        msg = struct.pack(">BBHH", self.slave_id, 0x04, 0x0064, 0x0001)
        msg += struct.pack('<H', self._calculate_crc(msg))
        self.ser.write(msg)
        
        response = self.ser.read(7) # ID(1) + Func(1) + Len(1) + Data(2) + CRC(2)
        if len(response) == 7 and response[1] == 0x04:
            val = struct.unpack(">H", response[3:5])[0]
            return val / 100.0 # 假设 100 倍率
        return -1.0
