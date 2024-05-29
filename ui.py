import threading
import time
import tkinter as tk
import logging
from tkinter import ttk
from tkinter import scrolledtext
from xlink_vehicle import xlinkVehicle


class MyApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.log_handler = None
        self.xlink_vehicle = None
        self.logger = logging.getLogger()
        self.logger.setLevel(logging.DEBUG)

        def create_label_entry_pair(root, label_text, default, row, column):
            label = tk.Label(root, text=label_text)
            label.grid(row=row, column=column, padx=5, pady=5, sticky='e')

            entry = tk.Entry(root, width=20)
            entry.config(textvariable=tk.StringVar(value=default))
            entry.grid(row=row, column=column + 1, padx=5, pady=5, sticky='w')

            return entry

        def sent(key, value):
            if self.xlink_vehicle is not None and self.xlink_vehicle.is_connected():
                self.xlink_vehicle.publish_error_to_xlink(key, value)

        def create_label_entry_button(root, label_text, default, row, column, key):
            label = tk.Label(root, text=label_text)
            label.grid(row=row, column=column, padx=5, pady=5, sticky='w')

            entry = tk.Entry(root, width=20)
            entry.config(textvariable=tk.StringVar(value=default))
            entry.grid(row=row, column=column + 1, padx=5, pady=5, sticky='w')

            button = tk.Button(root, text="Sent", command=lambda: async_call(sent, key=key, value=entry.get()), width=10)
            button.grid(row=row, column=column + 2, padx=10, sticky='w')

            return entry, button

        def create_separator(root, row, columnspan):
            separator = ttk.Separator(root, orient='horizontal')
            separator.grid(row=row, column=0, columnspan=columnspan, sticky='ew', pady=10)

        # 创建主窗口
        self.title("GLOBE Vehicle Error Code Sender")
        # self.geometry("400x200")

        left_frame = tk.Frame(self, width=300)
        left_frame.grid(row=0, column=0, sticky="nsew")

        right_frame = tk.Frame(self, width=400)
        right_frame.grid(row=0, column=1, sticky="nsew")

        i = 0
        # 创建环境下拉框
        label = tk.Label(left_frame, text="环境")
        label.grid(row=i, column=0, padx=5, pady=5, sticky='e')
        self.combo = ttk.Combobox(left_frame, state="readonly")
        self.combo['values'] = ('DEV6', 'DEV9',)
        self.combo.current(0)
        self.combo.grid(row=i, column=1, padx=5, pady=5, sticky='e')

        # 连接状态标签
        self.status_label = tk.Label(left_frame, text="Disconnected", bg="red", fg="white")
        self.status_label.grid(row=i, column=2, pady=10)

        i += 1

        # 创建前两个输入框
        entries1 = dict()
        for k, v in {"Device ID": {"default": "1144502349"}, "Model": {"default": "CZ60R24X"}}.items():
            entries1[k] = create_label_entry_pair(left_frame, k, v["default"], i, 0)
            i += 1

        # 创建分割线
        create_separator(left_frame, i, 4)
        i += 1

        # 创建后面8个输入框
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
            entries2[k] = create_label_entry_button(left_frame, f"{k} | {v['code']} | {v['name']}", 0, i, 0, k)
            i += 1

        # 创建一个 ScrolledText 小部件用于显示日志
        self.log_widget = scrolledtext.ScrolledText(right_frame, state='disabled', width=70, height=28, wrap='none')
        self.log_widget.grid(row=0, column=0, padx=5, pady=5)
        # 创建并配置水平滚动条
        x_scrollbar = tk.Scrollbar(right_frame, orient=tk.HORIZONTAL, command=self.log_widget.xview)
        x_scrollbar.grid(row=1, column=0, sticky='ew')
        self.log_widget.configure(xscrollcommand=x_scrollbar.set)

        # 创建自定义日志处理器
        self.log_handler = TextHandler(self.log_widget)

        # 设置日志格式
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        self.log_handler.setFormatter(formatter)

        def clear():
            self.log_widget.configure(state='normal')
            self.log_widget.delete(1.0, tk.END)  # 清空内容
            self.log_widget.configure(state='disabled')

        # 获取根日志记录器并添加处理器
        logger = logging.getLogger()
        logger.setLevel(logging.DEBUG)
        logger.addHandler(self.log_handler)
        clean_button = tk.Button(right_frame, text="Clear", command=clear, width=10)
        clean_button.grid(row=2, column=0, padx=10)

        # 创建底部的4个按钮
        buttons_frame = tk.Frame(self)
        buttons_frame.grid(row=1, column=0, columnspan=4, pady=20)

        def connect():
            broker = {
                "DEV6": {"host": "cantonrlmudp.globetools.com", "port": 1883, "username": "163e82bac7ca1f41163e82bac7ca9001", "password": "47919B30B9A23BA33DBB5FA976E99BA2"},
                "DEV9": {"host": "dev9-xlink-mqtt.globe-groups.com", "port": 1883, "username": "163e82ca81421f41163e82ca81427001", "password": "c94d6dd9dc9efe1016e78cfddb519210"},
            }
            if self.xlink_vehicle is None:
                env_id = self.combo.get()
                self.xlink_vehicle = xlinkVehicle(broker[env_id]["host"], broker[env_id]["port"], broker[env_id]["username"], broker[env_id]["password"],
                                                  entries1["Device ID"].get(), entries1["Model"].get(), self.logger)
                self.xlink_vehicle.connect_to_xlink()

        def disconnect():
            if self.xlink_vehicle is not None and self.xlink_vehicle.is_connected():
                self.xlink_vehicle.disconnect_to_xlink()
                self.xlink_vehicle = None

        def send_all():
            if self.xlink_vehicle is not None and self.xlink_vehicle.is_connected():
                for k, v in entries2.items():
                    self.xlink_vehicle.publish_error_to_xlink(k, v[0].get())

        def reset():
            for k, v in entries2.items():
                v[0].delete(0, tk.END)  # 先清空 Entry 的内容
                v[0].insert(0, "0")

        def async_call(func, *args, **kwargs):
            t = threading.Thread(target=func, args=args, kwargs=kwargs)
            t.daemon = True
            t.start()

        self.connect_active_button = []
        for v in entries2.values():
            self.connect_active_button.append(v[1])

        self.connect_button = tk.Button(buttons_frame, text="Connect", fg="green",
                                        command=connect, width=10)
        self.connect_button.grid(row=0, column=0, padx=10)

        self.disconnect_button = tk.Button(buttons_frame, text="Disconnect", fg="red",
                                           command=lambda: async_call(disconnect), width=10)
        self.disconnect_button.grid(row=0, column=1, padx=10)
        self.connect_active_button.append(self.disconnect_button)

        self.reset_button = tk.Button(buttons_frame, text="Reset", command=reset, width=10)
        self.reset_button.grid(row=0, column=2, padx=10)

        self.sent_all_button = tk.Button(buttons_frame, text="Sent All", command=lambda: async_call(send_all), width=10)
        self.sent_all_button.grid(row=0, column=3, padx=10)
        self.connect_active_button.append(self.sent_all_button)
        i += 1

        self.loop_update_status()

    def update_status(self):
        # 检查 MQTT 客户端是否连接
        if self.xlink_vehicle is not None and self.xlink_vehicle.is_connected():
            self.status_label.config(text="Connected", bg="green")
            self.connect_button.config(state='disabled')
            for button in self.connect_active_button:
                button.config(state='normal')
        else:
            self.status_label.config(text="Disconnected", bg="red")
            self.connect_button.config(state='normal')
            for button in self.connect_active_button:
                button.config(state='disabled')

    def loop_update_status(self):
        self.update_status()
        # 1 秒后再次调用自己
        self.after(1000, self.loop_update_status)


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
