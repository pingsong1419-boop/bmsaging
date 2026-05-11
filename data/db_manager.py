import sqlite3
import os
import datetime
from typing import List, Dict, Any

class DBManager:
    """
    数据存储管理类
    支持 SQLite 数据库持久化存储和 XTML/XML 格式的本地文本备份
    """
    def __init__(self, db_path: str = "bms_test_data.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """初始化数据库表结构"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 测试主表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS test_main (
                test_id INTEGER PRIMARY KEY AUTOINCREMENT,
                channel_id INTEGER,
                shelf_code TEXT,
                master_code TEXT,
                slave_codes TEXT,
                recipe_name TEXT,
                start_time DATETIME,
                end_time DATETIME,
                result TEXT
            )
        ''')
        
        # 测试数据详细记录表 (采样数据)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS test_details (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                test_id INTEGER,
                step_name TEXT,
                voltage REAL,
                current REAL,
                temp TEXT,
                timestamp DATETIME,
                FOREIGN KEY (test_id) REFERENCES test_main(test_id)
            )
        ''')

        # 测试项判定结果表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS test_items_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                test_id INTEGER,
                item_name TEXT,
                lower_limit REAL,
                upper_limit REAL,
                measured_value REAL,
                result TEXT,
                timestamp DATETIME,
                FOREIGN KEY (test_id) REFERENCES test_main(test_id)
            )
        ''')
        
        conn.commit()
        conn.close()

    def start_new_test(self, channel_id: int, shelf: str, master: str, slaves: List[str], recipe: str) -> int:
        """记录测试开始并返回测试 ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute('''
            INSERT INTO test_main (channel_id, shelf_code, master_code, slave_codes, recipe_name, start_time, result)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (channel_id, shelf, master, ",".join(slaves), recipe, now, "RUNNING"))
        test_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return test_id

    def log_detail(self, test_id: int, step_name: str, voltage: float, current: float, temp: str):
        """记录实时采样数据"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        now = datetime.datetime.now().strftime("%H:%M:%S")
        cursor.execute('''
            INSERT INTO test_details (test_id, step_name, voltage, current, temp, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (test_id, step_name, voltage, current, temp, now))
        conn.commit()
        conn.close()

    def log_item_result(self, test_id: int, name: str, low: float, high: float, val: float, res: str):
        """记录某个测试项目的最终判定结果"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute('''
            INSERT INTO test_items_results (test_id, item_name, lower_limit, upper_limit, measured_value, result, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (test_id, name, low, high, val, res, now))
        conn.commit()
        conn.close()

    def finish_test(self, test_id: int, result: str):
        """记录测试结束"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute('UPDATE test_main SET end_time = ?, result = ? WHERE test_id = ?', (now, result, test_id))
        conn.commit()
        conn.close()
        
        # 测试结束后生成本地备份文件 (模拟 XTML 格式)
        self.export_to_xtml(test_id)

    def export_to_xtml(self, test_id: int):
        """导出单个测试记录为 XTML (XML 风格) 文本文件，包含详细判定结果"""
        file_path = f"logs/test_{test_id}_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.xtml"
        os.makedirs("logs", exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 获取主表信息
        cursor.execute("SELECT * FROM test_main WHERE test_id = ?", (test_id,))
        main_info = cursor.fetchone()
        
        # 获取判定项结果
        cursor.execute("SELECT * FROM test_items_results WHERE test_id = ?", (test_id,))
        items = cursor.fetchall()
        
        conn.close()

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(f"<TestReport id='{test_id}'>\n")
            if main_info:
                f.write(f"  <BasicInfo>\n")
                f.write(f"    <Channel>{main_info[1]}</Channel>\n")
                f.write(f"    <Recipe>{main_info[5]}</Recipe>\n")
                f.write(f"    <StartTime>{main_info[6]}</StartTime>\n")
                f.write(f"    <EndTime>{main_info[7]}</EndTime>\n")
                f.write(f"    <TotalResult>{main_info[8]}</TotalResult>\n")
                f.write(f"  </BasicInfo>\n")
            
            f.write("  <ItemsResults>\n")
            for item in items:
                f.write(f"    <Item name='{item[2]}'>\n")
                f.write(f"      <Limit>{item[3]} ~ {item[4]}</Limit>\n")
                f.write(f"      <Measured>{item[5]}</Measured>\n")
                f.write(f"      <Result>{item[6]}</Result>\n")
                f.write(f"    </Item>\n")
            f.write("  </ItemsResults>\n")
            f.write("</TestReport>")
            
        print(f"✅ 测试数据(含判定项)已导出备份: {file_path}")
