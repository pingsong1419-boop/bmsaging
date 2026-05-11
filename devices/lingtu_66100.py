import socket
import time
import struct

class Lingtu66100:
    """
    领图 66100 多通道电池模拟器驱动 (基于 SCPI 协议)
    适配：SOURce[ch]:VOLTage:AMPLitude 指令格式
    """
    def __init__(self, ip: str, port: int = 5025):
        self.ip = ip
        self.port = port
        self.sock = None
        self.is_connected = False

    def connect(self) -> bool:
        # 如果当前已经是连接状态，先尝试安全断开
        if self.is_connected:
            self.disconnect()

        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # 设置 LINGER 选项，确保关闭时立即发送 RST 报文释放端口
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, struct.pack('ii', 1, 0))
            self.sock.settimeout(3.0)
            self.sock.connect((self.ip, self.port))
            self.is_connected = True
            
            # 清除仪器缓冲区并测试通讯
            self.sock.send(b"*CLS\n") # 清除状态寄存器
            time.sleep(0.1)
            self.sock.send(b"*IDN?\n")
            idn = self.sock.recv(1024).decode().strip()
            print(f"[*] 联机成功: {idn}")
            return True
        except Exception as e:
            print(f"[Lingtu66100] 连接失败 ({self.ip}): {e}")
            self.is_connected = False
            return False

    def disconnect(self):
        if self.sock:
            try:
                # 彻底关闭连接
                self.sock.shutdown(socket.SHUT_RDWR)
                self.sock.close()
            except:
                pass
        self.sock = None
        self.is_connected = False


    def set_voltage(self, channel: int, voltage: float) -> bool:
        """设置电压，并等待确认"""
        if not self.is_connected: return False
        try:
            cmd = f"SOUR{channel}:VOLT {voltage}\n"
            self.sock.send(cmd.encode())
            # 等待操作完成
            self.sock.send(b"*OPC?\n")
            res = self.sock.recv(10).decode().strip()
            return "1" in res
        except Exception as e:
            print(f"设置电压失败: {e}")
            return False


    def set_current_limit(self, channel: int, current: float):
        """设置电流限制: SOURce[ch]:CURRent:LIMit <value>"""
        if not self.is_connected: return
        cmd = f"SOUR{channel}:CURR {current}\n"
        self.sock.send(cmd.encode())

    def output_control(self, channel: int, state: bool) -> bool:
        """控制输出开关，并等待确认"""
        if not self.is_connected: return False
        try:
            val = 1 if state else 0
            cmd = f"OUTP{channel}:STAT {val}\n"
            self.sock.send(cmd.encode())
            self.sock.send(b"*OPC?\n")
            res = self.sock.recv(10).decode().strip()
            return "1" in res
        except Exception as e:
            print(f"输出控制失败: {e}")
            return False


    def measure_voltage(self, channel: int) -> float:
        """测量实时电压: MEASure[ch]:VOLTage?"""
        if not self.is_connected: return -1.0
        try:
            cmd = f"MEAS{channel}:VOLT?\n"
            self.sock.send(cmd.encode())
            data = self.sock.recv(1024).decode().strip()
            return float(data)
        except:
            return -1.0

    def measure_current(self, channel: int) -> float:
        """测量实时电流: MEASure[ch]:CURRent?"""
        if not self.is_connected: return -1.0
        try:
            cmd = f"MEAS{channel}:CURR?\n"
            self.sock.send(cmd.encode())
            data = self.sock.recv(1024).decode().strip()
            return float(data)
        except:
            return -1.0
