打包成带命令行日志窗口的exe
pyinstaller --onefile xx.py --name {output_name} {module_name}.py

打包成不带命令行日志窗口的exe
pyinstaller --onefile --windowed --name {output_name} {module_name}.py
pyinstaller --onefile --windowed --name "GLOBE Vehicle DP Sender" ui.py