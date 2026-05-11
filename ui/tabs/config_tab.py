from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                               QLabel, QPushButton, QTreeWidget, QTreeWidgetItem, QComboBox)

class ConfigTab(QWidget):
    def __init__(self):
        super().__init__()
        self._init_ui()
        
    def _init_ui(self):
        layout = QHBoxLayout(self)
        
        # 左侧：用例配方列表
        left_panel = QVBoxLayout()
        left_panel.addWidget(QLabel("测试用例列表 (配方)"))
        self.recipe_tree = QTreeWidget()
        self.recipe_tree.setHeaderLabel("配方名称")
        # 添加一个示例配方
        item = QTreeWidgetItem(["常规老化配方A (1主3从)"])
        self.recipe_tree.addTopLevelItem(item)
        left_panel.addWidget(self.recipe_tree)
        
        self.btn_add_recipe = QPushButton("新建配方")
        self.btn_add_recipe.clicked.connect(self.add_new_recipe)
        left_panel.addWidget(self.btn_add_recipe)
        
        layout.addLayout(left_panel, 1)
        
        # 右侧：配方基础属性及工步编辑
        right_panel = QVBoxLayout()
        
        # 配方基础属性：主从拓扑配置
        prop_layout = QHBoxLayout()
        prop_layout.addWidget(QLabel("当前配方的【主从拓扑模式】:"))
        self.topology_combo = QComboBox()
        self.topology_combo.addItems(["1主0从", "1主1从", "1主2从", "1主3从"])
        self.topology_combo.setCurrentText("1主3从") # 默认选项
        prop_layout.addWidget(self.topology_combo)
        prop_layout.addStretch()
        right_panel.addLayout(prop_layout)
        
        right_panel.addWidget(QLabel("测试项目与工步流 (树状结构):"))
        self.step_tree = QTreeWidget()
        self.step_tree.setHeaderLabels(["名称/工步", "模式/范围", "目标值/下限", "截止时间/上限", "NG 策略"])
        self.step_tree.setColumnWidth(0, 200)
        
        # 模拟填充一个带层级的示例
        item_node = QTreeWidgetItem(["01-容量测试项", "范围判定", "95.00", "105.00", "任何NG停止"])
        from PySide6.QtGui import QColor, QFont
        item_node.setForeground(0, QColor("#00E5FF"))
        font = QFont()
        font.setBold(True)
        item_node.setFont(0, font)
        
        step1 = QTreeWidgetItem(["  └─ 充电工步", "CC", "50A", "3600", "--"])
        step2 = QTreeWidgetItem(["  └─ 放电工步", "CD", "-50A", "3600", "--"])
        
        item_node.addChild(step1)
        item_node.addChild(step2)
        self.step_tree.addTopLevelItem(item_node)
        self.step_tree.expandAll()
        
        right_panel.addWidget(self.step_tree)
        
        btn_layout = QHBoxLayout()
        btn_add_item = QPushButton("添加测试项")
        btn_add_item.clicked.connect(self.add_test_item)
        btn_add_item.setStyleSheet("background-color: #17A2B8;")
        
        btn_add_step = QPushButton("添加子工步")
        btn_add_step.clicked.connect(self.add_step)
        
        btn_del = QPushButton("删除选中")
        btn_del.clicked.connect(self.delete_node)
        
        btn_save_recipe = QPushButton("保存配方")
        btn_save_recipe.clicked.connect(self.save_recipe)
        
        btn_layout.addWidget(btn_add_item)
        btn_layout.addWidget(btn_add_step)
        btn_layout.addWidget(btn_del)
        btn_layout.addWidget(btn_save_recipe)
        right_panel.addLayout(btn_layout)
        
        layout.addLayout(right_panel, 3)

    def add_test_item(self):
        from ui.dialogs.test_item_dialog import TestItemDialog
        dialog = TestItemDialog(self)
        if dialog.exec():
            data = dialog.get_data()
            item = QTreeWidgetItem([
                data['name'], 
                "范围判定", 
                str(data['min']), 
                str(data['max']), 
                "任何NG停止"
            ])
            from PySide6.QtGui import QColor, QFont
            item.setForeground(0, QColor("#00E5FF"))
            font = QFont()
            font.setBold(True)
            item.setFont(0, font)
            self.step_tree.addTopLevelItem(item)
            self.step_tree.setCurrentItem(item)

    def add_step(self):
        parent = self.step_tree.currentItem()
        if not parent:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "提醒", "请先选择一个『测试项』作为父节点。")
            return
            
        # 如果选中的本身是工步，则找到它的父节点
        if parent.parent():
            parent = parent.parent()

        from ui.dialogs.step_dialog import StepDialog
        dialog = StepDialog(self)
        if dialog.exec():
            data = dialog.get_data()
            item = QTreeWidgetItem([
                f"  └─ {data['name']}", 
                data['action'], 
                data['params'], 
                "--", 
                "--"
            ])
            parent.addChild(item)
            parent.setExpanded(True)

    def delete_node(self):
        item = self.step_tree.currentItem()
        if item:
            parent = item.parent()
            if parent:
                parent.removeChild(item)
            else:
                index = self.step_tree.indexOfTopLevelItem(item)
                self.step_tree.takeTopLevelItem(index)

    def save_recipe(self):
        recipe_item = self.recipe_tree.currentItem()
        if not recipe_item:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "提醒", "请先在左侧选择一个配方。")
            return
            
        # 实际逻辑应将工步存入数据库
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.information(self, "保存成功", f"配方【{recipe_item.text(0)}】已保存。")


    def add_new_recipe(self):
        from PySide6.QtWidgets import QInputDialog
        text, ok = QInputDialog.getText(self, "新建测试配方", "请输入新配方名称:")
        if ok and text:
            # 读取当前用户在下拉框选中的拓扑模式并一并展示
            topology = self.topology_combo.currentText()
            item = QTreeWidgetItem([f"{text} ({topology})"])
            self.recipe_tree.addTopLevelItem(item)
            self.recipe_tree.setCurrentItem(item)
            
    def get_all_recipes(self):
        """提供给外部调用的接口，获取树状列表里的所有配方名字"""
        recipes = []
        for i in range(self.recipe_tree.topLevelItemCount()):
            recipes.append(self.recipe_tree.topLevelItem(i).text(0))
        return recipes
