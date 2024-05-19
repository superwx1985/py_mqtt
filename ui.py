import tkinter as tk

root = tk.Tk()
root.title("My App")
root.geometry("300x200")

def on_button_click():
    print("Button was clicked!")

# 创建一个按钮并绑定点击事件处理函数
button = tk.Button(root, text="Click Me!", command=on_button_click)
button.pack()

root.mainloop()