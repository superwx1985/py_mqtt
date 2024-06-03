import threading
import time
import tkinter as tk
import logging
from tkinter import ttk
from tkinter import scrolledtext
from xlink_vehicle import XlinkVehicle
from vehicle_payload import PayloadData


class MyApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.log_handler = None
        self.xlink_vehicle = None
        self.logger = logging.getLogger()
        self.logger.setLevel(logging.DEBUG)
        self.connect_active_button = []
        self.running_mock_cutting = False
        self.switchs_statue = False

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

        def set_error(key, value):
            if self.xlink_vehicle is not None and self.xlink_vehicle.is_connected():
                self.xlink_vehicle.publish_error_to_xlink(key, value)

        def create_separator(root, row, columnspan):
            separator = ttk.Separator(root, orient='horizontal')
            separator.grid(row=row, column=0, columnspan=columnspan, sticky='ew', pady=2)

        # 创建主窗口
        self.title("GLOBE Vehicle Error Code Sender")
        # self.geometry("400x200")

        left_frame = tk.Frame(self, width=300)
        left_frame.grid(row=0, column=0, sticky="nsew")

        right_frame = tk.Frame(self, width=400)
        right_frame.grid(row=0, column=1, sticky="nsew")

        i = 0
        # 创建包含连接状态和环境标签的frame
        frame1 = tk.Frame(left_frame)
        frame1.grid(row=i, column=0, sticky="e")

        # 创建环境下拉框
        label = tk.Label(frame1, text="Environment")
        label.grid(row=0, column=1, padx=2, pady=2, sticky='e')
        self.env_combo = ttk.Combobox(left_frame, state="readonly")
        self.env_combo['values'] = ('DEV6', 'DEV9',)
        self.env_combo.current(0)
        self.env_combo.grid(row=i, column=2, padx=2, pady=2, sticky='w')

        connect_row = i
        def connect():
            broker = {
                "DEV6": {"host": "cantonrlmudp.globetools.com", "port": 1883,
                         "username": "163e82bac7ca1f41163e82bac7ca9001",
                         "password": "47919B30B9A23BA33DBB5FA976E99BA2"},
                "DEV9": {"host": "dev9-xlink-mqtt.globe-groups.com", "port": 1883,
                         "username": "163e82ca81421f41163e82ca81427001",
                         "password": "c94d6dd9dc9efe1016e78cfddb519210"},
            }
            if self.xlink_vehicle is None:
                env_id = self.env_combo.get()
                self.xlink_vehicle = XlinkVehicle(broker[env_id]["host"], broker[env_id]["port"],
                                                  broker[env_id]["username"], broker[env_id]["password"],
                                                  entries1["Device ID"].get(), entries1["Model"].get(), self.logger)
                self.xlink_vehicle.connect_to_xlink()
                self.connect_button.grid_remove()
                self.disconnect_button.grid(row=connect_row, column=4, padx=2, sticky='w')

        def disconnect():
            if self.xlink_vehicle is not None and self.xlink_vehicle.is_connected():
                self.xlink_vehicle.disconnect_to_xlink()
                self.xlink_vehicle = None
                self.connect_button.grid(row=connect_row, column=4, padx=2, sticky='w')
                self.disconnect_button.grid_remove()

        self.connect_button = tk.Button(left_frame, text="Connect", fg="green", width=10,
                                        command=connect)
        self.connect_button.grid(row=i, column=4, padx=2, sticky='w')

        self.disconnect_button = tk.Button(left_frame, text="Disconnect", fg="red", width=10,
                                           command=lambda: async_call(disconnect))
        self.connect_active_button.append(self.disconnect_button)

        i += 1

        # 连接状态标签
        self.status_label = tk.Label(left_frame, text="Disconnected", bg="red", fg="white", font=('Arial', 8))
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

        # 创建后面8个输入框
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

            button = tk.Button(root, text="Set", command=lambda: async_call(set_error, key=key, value=entry.get()), width=10)
            button.grid(row=row, column=column + 4, padx=2, sticky='w')

            return entry, checkbox_var, button

        entries2 = dict()
        error_map = {104: {"code": "BMS", "name": "Battery"},
                     211: {"code": "BC", "name": "Battery charger"},
                     1: {"code": "TR", "name": "Right wheel motor controller"},
                     2: {"code": "TL", "name": "Left wheel motor controller"},
                     3: {"code": "ML", "name": "Left blade motor controller"},
                     215: {"code": "MLS", "name": "Second left blade motor controller"},
                     4: {"code": "MM", "name": "Middle blade motor controller"},
                     5: {"code": "MR", "name": "Right blade motor controller"},
                     217: {"code": "MRS", "name": "Second right blade motor controller"},
                     216: {"code": "AT", "name": "Attachment controller"},
                     174: {"code": "?", "name": "Vehicle error code"},
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
                    if is_hex is False and data_type not in ("9", "A", "b"):
                        value = self.decimal_to_hex(value)
                    self.xlink_vehicle.publish_datapoint_to_xlink(key, data_type, value)
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
        self.custom_type_combo['values'] = ('Byte', 'Boolean', 'Int16', 'Unsigned Int16', 'Int32', 'Unsigned Int32',
                                            'Unsigned Int64', 'Float', 'String')
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

        def find_keys_by_value(d, target_value):
            return [key for key, value in d.items() if value == target_value][0]

        self.custom_send_button = tk.Button(left_frame, text="Set", command=lambda: async_call(
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
                self.xlink_vehicle.toggle_switch(not self.switchs_statue)
                self.switchs_statue = not self.switchs_statue

        left_buttons_frame = tk.Frame(left_frame)
        left_buttons_frame.grid(row=i, column=0, columnspan=4)

        self.clean_error_button = tk.Button(left_buttons_frame, text="Clean Error", command=clean_error)
        self.clean_error_button.grid(row=0, column=0, padx=5)
        self.connect_active_button.append(self.clean_error_button)

        self.set_all_button = tk.Button(left_buttons_frame, text="Set All", command=lambda: async_call(set_all))
        self.set_all_button.grid(row=0, column=1, padx=5)
        self.connect_active_button.append(self.set_all_button)

        self.mock_cutting_button = tk.Button(left_buttons_frame, text="Mock Cutting", command=lambda: async_call(mock_cutting))
        self.mock_cutting_button.grid(row=0, column=2, padx=5)

        self.toggle_switch_button = tk.Button(left_buttons_frame, text="Toggle Switch", command=lambda: async_call(toggle_switch))
        self.toggle_switch_button.grid(row=0, column=3, padx=5)
        self.connect_active_button.append(self.toggle_switch_button)
        i += 1

        # 创建一个 ScrolledText 小部件用于显示日志
        i = 0
        self.log_widget = scrolledtext.ScrolledText(right_frame, state='disabled', width=70, height=34, wrap='none', font=('Arial', 8))
        self.log_widget.grid(row=i, column=0, padx=2, pady=2)
        i += 1
        # 创建并配置水平滚动条
        x_scrollbar = tk.Scrollbar(right_frame, orient=tk.HORIZONTAL, command=self.log_widget.xview)
        x_scrollbar.grid(row=i, column=0, sticky='ew')
        self.log_widget.configure(xscrollcommand=x_scrollbar.set)
        i += 1

        # 创建自定义日志处理器
        self.log_handler = TextHandler(self.log_widget)

        # 设置日志格式
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        self.log_handler.setFormatter(formatter)

        # 获取根日志记录器并添加处理器
        logger = logging.getLogger()
        logger.setLevel(logging.DEBUG)
        logger.addHandler(self.log_handler)

        def clear():
            self.log_widget.configure(state='normal')
            self.log_widget.delete(1.0, tk.END)  # 清空内容
            self.log_widget.configure(state='disabled')

        clean_log_button = tk.Button(right_frame, text="Clear Log", command=clear, width=10)
        clean_log_button.grid(row=i, column=0, padx=2, pady=2)
        i += 1

        # 创建底部按钮
        # buttons_frame = tk.Frame(self)
        # buttons_frame.grid(row=1, column=0, columnspan=5, pady=5)

        self.loop_update_status()

    def update_status(self):
        # 检查 MQTT 客户端是否连接
        if self.xlink_vehicle is not None and self.xlink_vehicle.is_connected():
            self.status_label.config(text="Connected", bg="green")
            self.connect_button.config(state='disabled')
            for button in self.connect_active_button:
                button.config(state='normal')
            if self.running_mock_cutting is False:
                self.mock_cutting_button.config(state='normal')
        else:
            self.status_label.config(text="Disconnected", bg="red")
            self.connect_button.config(state='normal')
            for button in self.connect_active_button:
                button.config(state='disabled')
            self.mock_cutting_button.config(state='disabled')

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


class TextHandler(logging.Handler):
    def __init__(self, widget):
        super().__init__()
        self.widget = widget

    def emit(self, record):
        msg = self.format(record)
        print(msg)
        self.widget.configure(state='normal')
        self.widget.insert(tk.END, msg + '\n')
        self.widget.configure(state='disabled')
        self.widget.yview(tk.END)


if __name__ == "__main__":
    app = MyApp()
    app.mainloop()
