import socket
import time
import struct

class NGIN3618:
    """
    NGI N3618 高压直流电源驱动 (通过 SYST:ERR? 判定成功)
    """
    def __init__(self, ip: str, port: int = 5025):
        self.ip = ip
        self.port = port
        self.sock = None
        self.is_connected = False
        self.TERMINATOR = "\n" # 恢复使用 \n 尝试

    def connect(self) -> bool:
        if self.is_connected:
            self.disconnect()
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, struct.pack('ii', 1, 0))
            self.sock.settimeout(1.5)
            self.sock.connect((self.ip, self.port))
            
            # 初始化
            self.send_cmd("*CLS")
            time.sleep(0.1)
            self.send_cmd("*IDN?")
            idn = self.sock.recv(1024).decode().strip()
            
            print(f"[NGI N3618] 联机成功: {idn}")
            self.is_connected = True
            return True
        except Exception as e:
            print(f"[NGI N3618] 连接失败: {e}")
            self.is_connected = False
            return False

    def disconnect(self):
        if self.sock:
            try:
                self.sock.shutdown(socket.SHUT_RDWR)
                self.sock.close()
            except:
                pass
        self.sock = None
        self.is_connected = False

    def send_cmd(self, cmd: str):
        if self.sock:
            # 发送前清空缓冲区（可选，防止粘包）
            self.sock.setblocking(False)
            try:
                self.sock.recv(1024)
            except:
                pass
            self.sock.setblocking(True)
            
            full_cmd = f"{cmd}{self.TERMINATOR}"
            self.sock.send(full_cmd.encode())

    def check_success(self) -> bool:
        """通过查询错误队列判定上一条指令是否执行成功"""
        try:
            self.send_cmd("SYST:ERR?")
            res = self.sock.recv(1024).decode().strip()
            # 标准响应是 '0,"No error"' 或 '+0,"No error"'
            return "0," in res or "No error" in res
        except:
            return False

    def set_voltage(self, voltage: float) -> bool:
        if not self.is_connected: return False
        try:
            self.send_cmd(f"VOLT {voltage:.3f}")
            return self.check_success()
        except:
            return False

    def set_current(self, current: float) -> bool:
        if not self.is_connected: return False
        try:
            self.send_cmd(f"CURR {current:.3f}")
            return self.check_success()
        except:
            return False

    def output_control(self, state: bool) -> bool:
        if not self.is_connected: return False
        try:
            cmd = "OUTP ON" if state else "OUTP OFF"
            self.send_cmd(cmd)
            return self.check_success()
        except:
            return False

    def measure_voltage(self) -> float:
        if not self.is_connected: return -1.0
        try:
            self.send_cmd("MEAS:VOLT?")
            data = self.sock.recv(1024).decode().strip()
            # 兼容科学计数法
            clean_data = "".join(c for c in data if c in "0123456789.eE-+")
            return float(clean_data)
        except:
            return -1.0

    def measure_current(self) -> float:
        if not self.is_connected: return -1.0
        try:
            self.send_cmd("MEAS:CURR?")
            data = self.sock.recv(1024).decode().strip()
            clean_data = "".join(c for c in data if c in "0123456789.eE-+")
            return float(clean_data)
        except:
            return -1.0
