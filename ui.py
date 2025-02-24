import threading
import logging
import tkinter as tk
from tkinter import ttk
from tkinter import scrolledtext
from xlink_vehicle import XlinkVehicle
from vehicle_payload import PayloadData
from logger_config import get_logger, TextHandler

VERSION = 1.5

BROKER = {
    "DEV6": {"host": "cantonrlmudp.globetools.com", "port": 1883,
             "product_id": "163e82bac7ca1f41163e82bac7ca9001",
             "product_key": "78348f781e99ced28bbbbfa73fc3c3ec"},
    "DEV9": {"host": "dev9-xlink-mqtt.globe-groups.com", "port": 1883,
             "product_id": "163e82ca81421f41163e82ca81427001",
             "product_key": "3709185dfdf50d9563eedceadbccb3d3"},
    "DEV7": {"host": "dev7mqtt.globe-groups.com", "port": 1883,
             "product_id": "163e82bac7ca1f41163e82bac7ca9001",
             "product_key": "78348f781e99ced28bbbbfa73fc3c3ec"},
}

DATA_TYPES = ('Byte', 'Boolean', 'Int16', 'Unsigned Int16', 'Int32', 'Unsigned Int32', 'Unsigned Int64', 'Float', 'String')


def init_position(window, parent):
    """初始定位逻辑"""

    # 计算安全坐标
    base_x = parent.winfo_x()
    base_y = parent.winfo_y()
    target_x = base_x + 10
    target_y = base_y + 10

    # 应用坐标
    window.geometry(f"+{target_x}+{target_y}")


def find_keys_by_value(d, target_value):
    return [key for key, value in d.items() if value == target_value][0]


class MyApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.log_handler = None
        self.xlink_vehicle = None
        self.logger = get_logger()
        self.logger.setLevel(logging.DEBUG)
        self.connect_active_button = []
        self.mqtt_connect_status = False
        self.ui_connect_status = False
        self.running_mock_cutting = False
        self.switches_statue = False
        self.dp_list = []

        # 初始化样式引擎
        self.style = ttk.Style()
        self._configure_styles()

        def async_call(func, *args, **kwargs):
            t = threading.Thread(target=func, args=args, kwargs=kwargs)
            t.daemon = True
            t.start()

        def create_label_entry_pair(root, label_text, default, row, column):
            label = tk.Label(root, text=label_text)
            label.grid(row=row, column=column, padx=2, pady=2, sticky='e')

            entry = tk.Entry(root, width=20)
            entry.config(textvariable=tk.StringVar(value=default))
            entry.grid(row=row, column=column + 2, padx=2, pady=2, sticky='w')

            return entry

        def set_error(key, value, is_hex):
            if self.xlink_vehicle is not None and self.xlink_vehicle.is_connected():
                self.xlink_vehicle.publish_error_to_xlink(key, value, is_hex)

        def create_separator(root, row, columnspan):
            separator = ttk.Separator(root, orient='horizontal')
            separator.grid(row=row, column=0, columnspan=columnspan, sticky='ew', pady=2)

        # 创建主窗口
        self.title(f"GLOBE Vehicle DP Sender V{VERSION}")
        # self.geometry("400x200")

        left_frame = tk.Frame(self)
        left_frame.grid(row=0, column=0, sticky="nsew")

        right_frame = tk.Frame(self)
        right_frame.grid(row=0, column=1, sticky="nsew")

        # 配置行和列，使其随窗口大小调整
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=0)  # 左框架不自适应大小
        self.grid_columnconfigure(1, weight=1)

        i = 0
        # 创建包含连接状态和环境标签的frame
        frame1 = tk.Frame(left_frame)
        frame1.grid(row=i, column=0, sticky="e")

        # 创建环境下拉框
        label = tk.Label(frame1, text="Environment")
        label.grid(row=0, column=1, padx=2, pady=2, sticky='e')
        self.env_combo = ttk.Combobox(left_frame, state="readonly")
        keys_tuple = tuple(BROKER.keys())
        self.env_combo['values'] = keys_tuple
        self.env_combo.current(0)
        self.env_combo.grid(row=i, column=2, padx=2, pady=2, sticky='w')

        connect_row = i

        def connect():
            if self.xlink_vehicle is None:
                try:
                    env_id = self.env_combo.get()
                    self.xlink_vehicle = XlinkVehicle(BROKER[env_id]["host"], BROKER[env_id]["port"],
                                                      BROKER[env_id]["product_id"], BROKER[env_id]["product_key"],
                                                      entries1["Device ID"].get(), entries1["Model"].get(), self.logger)
                    self.xlink_vehicle.connect_to_xlink()
                except Exception as e:
                    self.xlink_vehicle = None
                    self.connect_button.grid(row=connect_row, column=4, padx=2, sticky='w')
                    self.disconnect_button.grid_remove()
                else:
                    self.connect_button.grid_remove()
                    self.disconnect_button.grid(row=connect_row, column=4, padx=2, sticky='w')

        def disconnect():
            if self.xlink_vehicle is not None and self.xlink_vehicle.is_connected():
                self.xlink_vehicle.disconnect_to_xlink()
                self.xlink_vehicle = None
                self.connect_button.grid(row=connect_row, column=4, padx=2, sticky='w')
                self.disconnect_button.grid_remove()

        self.connect_button = ttk.Button(left_frame, text="Connect", style="green.TButton", width=10, command=connect)
        self.connect_button.grid(row=i, column=4, padx=2, sticky='w')

        self.disconnect_button = ttk.Button(left_frame, text="Disconnect", style="red.TButton", width=10,
                                           command=lambda: async_call(disconnect))
        self.connect_active_button.append(self.disconnect_button)

        i += 1

        # 连接状态标签
        self.status_label = tk.Label(left_frame, text="Disconnected", bg="pink", fg="white", font=('Arial', 8))
        self.status_label.grid(row=i, column=4, padx=2)

        # 创建前两个输入框
        entries1 = dict()
        for k, v in {"Device ID": {"default": "1144502349"}, "Model": {"default": "CZ60R24X"}}.items():
            entries1[k] = create_label_entry_pair(left_frame, k, v["default"], i, 0)
            i += 1

        # 创建分割线
        create_separator(left_frame, i, 5)
        i += 1

        # 创建表头
        label = tk.Label(left_frame, text="Description", fg="blue")
        label.grid(row=i, column=0, padx=2, pady=2, sticky='w')
        label = tk.Label(left_frame, text="Index", fg="blue")
        label.grid(row=i, column=1, padx=2, pady=2, sticky='w')
        label = tk.Label(left_frame, text="Value", fg="blue")
        label.grid(row=i, column=2, padx=2, pady=2, sticky='w')
        label = tk.Label(left_frame, text="HEX", fg="blue")
        label.grid(row=i, column=3, padx=2, pady=2, sticky='w')
        i += 1

        # 创建error输入框
        def create_label_entry_button(root, index_text, label_text, default, row, column, key):
            label = tk.Label(root, text=label_text)
            label.grid(row=row, column=column, padx=2, pady=2, sticky='w')

            label = tk.Label(root, text=index_text)
            label.grid(row=row, column=column + 1, padx=2, pady=2, sticky='w')

            entry = tk.Entry(root)
            entry.config(textvariable=tk.StringVar(value=default))
            entry.grid(row=row, column=column + 2, padx=2, pady=2, sticky='w')

            checkbox_var = tk.BooleanVar(value=True)
            checkbox = tk.Checkbutton(root, text="", variable=checkbox_var)
            checkbox.grid(row=row, column=column + 3, padx=2, pady=2, sticky='w')

            button = ttk.Button(root, text="Set", command=lambda: async_call(set_error, key=key, value=entry.get(), is_hex=checkbox_var.get()), width=10)
            button.grid(row=row, column=column + 4, padx=2, sticky='w')

            return entry, checkbox_var, button

        entries2 = dict()
        error_map = {
            1: {"code": "TR", "name": "Right wheel motor controller"},
            2: {"code": "TL", "name": "Left wheel motor controller"},
            3: {"code": "ML", "name": "Left blade motor controller"},
            4: {"code": "MM", "name": "Middle blade motor controller"},
            5: {"code": "MR", "name": "Right blade motor controller"},
            104: {"code": "BMS", "name": "Battery"},
            137: {"code": "PMU", "name": "6P Battery"},
            174: {"code": "V", "name": "Vehicle"},
            211: {"code": "BC", "name": "Battery charger"},
            215: {"code": "MLS", "name": "Second left blade motor controller"},
            216: {"code": "AT", "name": "Attachment controller"},
            217: {"code": "MRS", "name": "Second right blade motor controller"},
        }
        for k, v in error_map.items():
            entries2[k] = create_label_entry_button(left_frame, k, f"{v['code']} | {v['name']}", 0, i, 0, k)
            i += 1

        for v in entries2.values():
            self.connect_active_button.append(v[2])

        # 自定义DP
        def set_custom_datapoint(key, data_type, value, is_hex):
            try:
                if self.xlink_vehicle is not None and self.xlink_vehicle.is_connected():
                    self.xlink_vehicle.publish_datapoint_to_xlink(key, data_type, value, is_hex)
            except Exception as e:
                self.logger.error(e)

        self.custom_input = None

        def on_combobox_change(row=0, column=0):
            selected_value = self.custom_type_combo.get()
            if selected_value == "Boolean":
                self.custom_input = self.custom_input_combo
                self.custom_input_entry.grid_remove()
                self.custom_input_checkbox.grid_remove()
                self.custom_input_combo.grid(row=row, column=column, padx=2, pady=2, sticky='w')
            else:
                self.custom_input = self.custom_input_entry
                self.custom_input_entry.grid(row=row, column=column, padx=2, pady=2, sticky='w')
                self.custom_input_checkbox.grid(row=row, column=column+1, padx=2, pady=2, sticky='w')
                self.custom_input_combo.grid_remove()

        custom_frame = tk.Frame(left_frame)
        custom_frame.grid(row=i, column=0, sticky='w')

        custom_label = tk.Label(custom_frame, text="Custom Datapoint")
        custom_label.grid(row=0, column=0, padx=2, pady=2, sticky='w')

        self.custom_type_combo = ttk.Combobox(custom_frame, state="readonly", width=15)
        self.custom_type_combo['values'] = DATA_TYPES
        self.custom_type_combo.current(0)
        custom_type_combo_row = i  # 获取当前的i，不受后续i变化影响
        self.custom_type_combo.bind("<<ComboboxSelected>>", lambda event: on_combobox_change(row=custom_type_combo_row, column=2))
        self.custom_type_combo.grid(row=0, column=1, padx=2, pady=2, sticky='e')

        self.custom_index_entry = tk.Entry(left_frame, width=4)
        self.custom_index_entry.config(textvariable=tk.StringVar(value="0"))
        self.custom_index_entry.grid(row=i, column=1, padx=2, pady=2, sticky='w')

        self.custom_input_entry = tk.Entry(left_frame)
        self.custom_input_entry.config(textvariable=tk.StringVar(value="0"))

        self.custom_input_checkbox_var = tk.BooleanVar()
        self.custom_input_checkbox = tk.Checkbutton(left_frame, text="", variable=self.custom_input_checkbox_var)

        self.custom_input_combo = ttk.Combobox(left_frame, state="readonly")
        self.custom_input_combo['values'] = ('True', 'False')
        self.custom_input_combo.current(0)

        on_combobox_change(i, 2)

        self.custom_send_button = ttk.Button(left_frame, text="Set", command=lambda: async_call(
            set_custom_datapoint, key=self.custom_index_entry.get(), data_type=find_keys_by_value(PayloadData.type_map, self.custom_type_combo.get()),
            value=self.custom_input.get(), is_hex=self.custom_input_checkbox_var.get()), width=10)
        self.custom_send_button.grid(row=i, column=4, padx=2, sticky='w')
        self.connect_active_button.append(self.custom_send_button)
        i += 1

        # 创建底部按钮
        def set_all(only_error=False):
            if self.xlink_vehicle is not None and self.xlink_vehicle.is_connected():
                for k, v in entries2.items():
                    value = v[0].get()
                    if v[1].get() is False:
                        value = self.decimal_to_hex(value)
                    self.xlink_vehicle.publish_error_to_xlink(k, value)
                if not only_error:
                    async_call(
                        set_custom_datapoint,
                        key=self.custom_index_entry.get(),
                        data_type=find_keys_by_value(PayloadData.type_map, self.custom_type_combo.get()),
                        value=self.custom_input.get(),
                        is_hex=self.custom_input_checkbox_var.get()
                    )

        def clean_error():
            for k, v in entries2.items():
                v[0].delete(0, tk.END)  # 先清空 Entry 的内容
                v[0].insert(0, "0")
            set_all(only_error=True)

        def mock_cutting():
            if self.xlink_vehicle is not None and self.xlink_vehicle.is_connected():
                self.mock_cutting_button.config(state='disabled')
                self.running_mock_cutting = True
                self.xlink_vehicle.mock_cutting()
                self.running_mock_cutting = False

        def toggle_switch():
            if self.xlink_vehicle is not None and self.xlink_vehicle.is_connected():
                self.xlink_vehicle.toggle_switch(not self.switches_statue)
                self.switches_statue = not self.switches_statue

        def publish_multiple_datapoint():
            PublishMultipleDatapointWindow(self)

        # 在界面底部新增按钮
        left_buttons_frame = tk.Frame(left_frame)
        left_buttons_frame.grid(row=i, column=0, columnspan=4)

        self.clean_error_button = ttk.Button(left_buttons_frame, text="Clean Error", command=lambda: async_call(clean_error))
        self.clean_error_button.grid(row=0, column=0, padx=5)
        self.connect_active_button.append(self.clean_error_button)

        self.set_all_button = ttk.Button(left_buttons_frame, text="Set All", command=lambda: async_call(set_all))
        self.set_all_button.grid(row=0, column=1, padx=5)
        self.connect_active_button.append(self.set_all_button)

        self.mock_cutting_button = ttk.Button(left_buttons_frame, text="Mock Cutting", command=lambda: async_call(mock_cutting))
        self.mock_cutting_button.grid(row=0, column=2, padx=5)

        self.toggle_switch_button = ttk.Button(left_buttons_frame, text="Toggle Switch", command=lambda: async_call(toggle_switch))
        self.toggle_switch_button.grid(row=0, column=3, padx=5)
        self.connect_active_button.append(self.toggle_switch_button)

        self.publish_multiple_datapoint_button = ttk.Button(left_buttons_frame, text="Multiple DP", command=publish_multiple_datapoint)
        self.publish_multiple_datapoint_button.grid(row=0, column=4, padx=5)
        self.connect_active_button.append(self.publish_multiple_datapoint_button)
        i += 1

        # 创建一个 ScrolledText 小部件用于显示日志
        i = 0
        self.log_widget = scrolledtext.ScrolledText(right_frame, state='disabled', wrap='none', font=('Arial', 8))
        self.log_widget.grid(row=i, column=0, padx=2, pady=2, sticky="nsew")
        right_frame.grid_rowconfigure(i, weight=1)
        right_frame.grid_columnconfigure(0, weight=1)

        i += 1
        # 创建并配置水平滚动条
        x_scrollbar = tk.Scrollbar(right_frame, orient=tk.HORIZONTAL, command=self.log_widget.xview)
        x_scrollbar.grid(row=i, column=0, sticky='ew')
        self.log_widget.configure(xscrollcommand=x_scrollbar.set)
        i += 1

        # 创建自定义日志处理器
        self.log_handler = TextHandler(self.log_widget)

        # 设置日志格式
        formatter = logging.Formatter('%(asctime)s - %(levelname)s: %(message)s')
        self.log_handler.setFormatter(formatter)

        # 获取根日志记录器并添加处理器
        logger = get_logger()
        logger.setLevel(logging.DEBUG)
        logger.addHandler(self.log_handler)

        def clear():
            self.log_widget.configure(state='normal')
            self.log_widget.delete(1.0, tk.END)  # 清空内容
            self.log_widget.configure(state='disabled')

        clean_log_button = ttk.Button(right_frame, text="Clear Log", command=clear, width=10)
        clean_log_button.grid(row=i, column=0, padx=2, pady=2)
        i += 1

        # 创建底部按钮
        # buttons_frame = tk.Frame(self)
        # buttons_frame.grid(row=1, column=0, columnspan=5, pady=5)

        self.update_display(on=False)
        self.loop_update_status()

    def _configure_styles(self):
        self.style.configure('red',
                             foreground='red.TButton',  # 文字颜色
                             # font=('Segoe UI', 10),  # 现代字体
                             # padding=6,  # 内边距优化
                             # relief='flat',  # 扁平化设计
                             # anchor='center'  # 文字对齐方式
                             )
        self.style.configure('green',
                             foreground='green.TButton',
                             )

    def update_status(self):
        # 检查 MQTT 客户端是否连接
        if self.xlink_vehicle is not None and self.xlink_vehicle.is_connected():
            self.mqtt_connect_status = True
            if self.mqtt_connect_status != self.ui_connect_status:
                self.update_display(on=True)
        else:
            self.mqtt_connect_status = False
            if self.mqtt_connect_status != self.ui_connect_status:
                self.update_display(on=False)

    def update_display(self, on=False):
        if on:
            self.status_label.config(text="Connected", bg="green")
            self.connect_button.config(state='disabled')
            for button in self.connect_active_button:
                button.config(state='normal')
            if self.running_mock_cutting is False:
                self.mock_cutting_button.config(state='normal')
            self.ui_connect_status = True
        else:
            self.status_label.config(text="Disconnected", bg="pink")
            self.connect_button.config(state='normal')
            for button in self.connect_active_button:
                button.config(state='disabled')
            self.mock_cutting_button.config(state='disabled')
            self.ui_connect_status = False

    def loop_update_status(self):
        self.update_status()
        # 1 秒后再次调用自己
        self.after(1000, self.loop_update_status)

    @classmethod
    def decimal_to_hex(cls, decimal_str):
        # 将十进制字符串转换为整数
        decimal_int = int(decimal_str)
        # 将整数转换为十六进制字符串，并去掉前缀 '0x'
        hex_str = hex(decimal_int)[2:]
        # 返回十六进制字符串
        return hex_str.upper()


class PublishMultipleDatapointWindow(tk.Toplevel):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.logger = parent.logger
        self.rows = []
        self.transient(parent)  # 设置窗口关联关系
        self._setup_modal_control()  # 独占式焦点控制
        # 窗口关闭协议绑定
        self.protocol("WM_DELETE_WINDOW", self.safe_close)

        self.title("Publish Multiple Datapoint")
        self.geometry("800x400")
        init_position(self, self.parent)

        # 初始化行计数器
        self.row_counter = 0

        # 创建界面组件
        self.create_header()
        self.create_table()
        self.create_buttons()

        if self.parent.dp_list:
            for dp in self.parent.dp_list:
                self.add_row(dp)
        else:
            self.add_row()

    def _setup_modal_control(self, init=True):
        """增强型模态控制"""
        self.grab_set()  # 标准独占
        self.focus_force()  # 跨平台强化
        self.attributes('-topmost', 1)  # 窗口置顶
        if init:
            self.wait_visibility()  # 确保窗口可见

    def show_error(self, message):
        """安全错误提示方法"""
        # 创建临时弹窗容器
        error_dialog = tk.Toplevel(self)
        init_position(error_dialog, self)
        error_dialog.transient(self)
        error_dialog.grab_set()

        # 显示错误信息
        ttk.Label(error_dialog, text=message).pack(padx=20, pady=10)
        ttk.Button(error_dialog, text="确定",
                   command=lambda: self._close_error(error_dialog)).pack(pady=5)

        # 设置关闭协议
        error_dialog.protocol("WM_DELETE_WINDOW", lambda: self._close_error(error_dialog))

    def _close_error(self, dialog):
        """安全关闭错误弹窗"""
        dialog.grab_release()
        dialog.destroy()
        self._setup_modal_control(init=False)

    def safe_close(self):
        """安全关闭协议"""
        self.update_dp_list()
        self.grab_release()
        self.destroy()

    def create_header(self):
        """创建表格头部"""
        header_frame = tk.Frame(self, bg="#F0F0F0")
        header_frame.pack(fill=tk.X, padx=10, pady=5)

        headers = ["Index", "Type", "Value", "HEX", "Action"]
        for col, text in enumerate(headers):
            label = tk.Label(header_frame, text=text, bg="#F0F0F0", width=15 if col < 3 else 8)
            label.grid(row=0, column=col, padx=2, pady=2)

    def create_table(self):
        """创建可滚动表格区域"""
        container = tk.Frame(self)
        container.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # 创建画布和滚动条
        self.canvas = tk.Canvas(container, highlightthickness=0)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=self.canvas.yview)
        self.scroll_frame = tk.Frame(self.canvas)

        # 配置画布滚动
        self.scroll_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.create_window((0, 0), window=self.scroll_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)

        # 布局组件
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def create_buttons(self):
        """创建功能按钮"""
        btn_frame = tk.Frame(self)
        btn_frame.pack(pady=10)

        ttk.Button(btn_frame, text="Add Row", command=self.add_row).grid(row=0, column=0, padx=5)
        ttk.Button(btn_frame, text="Reset", command=self.clear_table, style="red.TButton").grid(row=0, column=1, padx=5)
        ttk.Button(btn_frame, text="Send", command=self.submit_data).grid(row=0, column=2, padx=5)

    def add_row(self, dp=None):
        """添加新行逻辑"""
        row_frame = tk.Frame(self.scroll_frame)
        row_frame.pack(fill=tk.X, pady=2)

        # 创建行组件
        index_entry = ttk.Entry(row_frame, width=15)
        type_combo = ttk.Combobox(row_frame, values=DATA_TYPES, width=15, state="readonly")
        value_entry = ttk.Entry(row_frame, width=15)
        hex_var = tk.BooleanVar()
        hex_check = ttk.Checkbutton(row_frame, variable=hex_var)
        delete_btn = ttk.Button(row_frame, text="Del", command=lambda: self.delete_row(row_frame))

        if dp:
            index_entry.insert(0, dp['index'])
            type_value = PayloadData.type_map[dp['type']]
            type_combo.set(type_value)
            value_entry.insert(0, dp['value'])
            hex_var.set(dp['is_hex'])
        else:
            self.update_dp_list()
            index_value = "0"
            if self.parent.dp_list:
                index_value = int(self.parent.dp_list[-1]['index']) + 1
            index_entry.insert(0,  index_value)
            type_combo.current(0)

        self.row_counter += 1

        # 布局组件
        components = [index_entry, type_combo, value_entry, hex_check, delete_btn]
        for col, widget in enumerate(components):
            widget.grid(row=0, column=col, padx=2, pady=2, sticky="ew")

        # 存储行对象
        self.rows.append({
            "frame": row_frame,
            "index": index_entry,
            "type": type_combo,
            "value": value_entry,
            "hex": hex_var
        })
        self.update_dp_list()

    def delete_row(self, target_frame):
        """删除指定行"""
        for row in self.rows:
            if row["frame"] == target_frame:
                row["frame"].destroy()
                self.rows.remove(row)
                break
        self.update_dp_list()

    def clear_table(self):
        """清空表格"""
        for row in self.rows:
            row["frame"].destroy()
        self.rows.clear()
        self.row_counter = 0
        self.update_dp_list()
        self.add_row()

    def validate_data(self):
        index_list = []
        """数据校验逻辑"""
        for row in self.rows:
            i = row["index"].get().strip()
            if not i:
                return "Index cannot be empty"
            if i in index_list:
                return f"Index [{i}] is duplicated"
            index_list.append(i)
        return None

    def submit_data(self):
        """数据提交逻辑"""
        if error := self.validate_data():
            self.logger.warning(error)
            self.show_error(error)
        else:
            self.update_dp_list()

            # 调用发送函数
            self._send(self.parent.dp_list)
            self.logger.info(f"{self.parent.dp_list} has been send.")
            # messagebox.showinfo("Send Success", f"{result} has been send.")

    def _send(self, data):
        client = self.parent.xlink_vehicle
        if client is not None and client.is_connected():
            client.publish_multiple_datapoint_to_xlink(data)

    def update_dp_list(self):
        self.parent.dp_list = []
        for row in self.rows:
            data = {
                "index": row["index"].get(),
                "type": find_keys_by_value(PayloadData.type_map, row["type"].get()),
                "value": row["value"].get(),
                "is_hex": row["hex"].get()
            }
            self.parent.dp_list.append(data)


if __name__ == "__main__":
    app = MyApp()
    app.mainloop()
