import binascii
import struct

from mqtt_client import MQTTClient


class VehiclePayload:

    @classmethod
    def change_bin_str_to_byte(cls, binary_string):
        # 将二进制字符串转换为整数
        integer_value = int(binary_string, 2)
        # 将整数转换为字节对象
        byte_object = integer_value.to_bytes((integer_value.bit_length() + 7) // 8, byteorder='big')
        return byte_object

    def __init__(self, index, _type, value):
        self.payload_type = "0006"  # 数据包类型
        self.sync_datapoint_flag = "01100000"  # 数据端点上报标识
        # 7 设备名称标识（name flag）
        # 6 数据端点标识（dp flag）表示datapoint payload是否有数据端点数据
        # 5 数据端点模板标识（template flag）表示 datapoint payload是非数据模板类型的端点数据
        # 4 不推送消息标识（unPush flag）
        # 3 指定时间标识（timestamp flag）根据当前时区，8个字节Unix时间戳，在设备名称（如果有的话）后面，在datapoint payload前面
        # 2 数据端点解析失败返回结果不断开连接（MQTT标准协议解析失败或其他错误仍然断开连接），当开启本选项时，在时间标识后面增加两个字节的MsgID
        # 1~0 预留
        self.payload_data_byte = PayloadData(index, _type, value).get_byte()
        self.sync_datapoint_flag_byte = self.change_bin_str_to_byte(self.sync_datapoint_flag)
        self.package_byte = self.sync_datapoint_flag_byte + self.payload_data_byte
        length_hex_string = hex(len(self.package_byte))[2:]
        padded_length_hex_string = length_hex_string.zfill(4)
        self.length_byte = binascii.unhexlify(padded_length_hex_string)
        self.byte = binascii.unhexlify(self.payload_type) + self.length_byte + self.package_byte

    def get_byte(self):
        return self.byte


class PayloadData:
    type_map = {"0": "Byte", "1": "Int16", "2": "Unsigned Int16", "3": "Int32",
                "4": "Unsigned Int32", "5": "Int64", "6": "Unsigned Int64", "7": "Float",
                "8": "Double", "9": "String", "A": "Binary", "b": "Boolean"}

    @classmethod
    def int_to_1byte(cls, n):
        if n < 0 or n > 255:
            raise ValueError("The value exceeds the 1-byte range")
        return n.to_bytes(1, byteorder='big')

    @classmethod
    def string_to_hex_ascii(cls, s):
        hex_values = [format(ord(char), '02X') for char in s]
        return ''.join(hex_values)

    @classmethod
    def hex_string_to_byte(cls, s):
        # 转换为 bytes 对象
        return bytes.fromhex(s)

    @classmethod
    def int_to_hex16(cls, n):
        # 确保数值在16位范围内
        if n < -32768 or n > 32767:
            raise ValueError("The value exceeds the range of a 16-bit integer")
        # 将数值转换为16位无符号整数
        n &= 0xFFFF
        # 将其转换为16进制字符串，并保证长度为4（不足时左补0）
        hex_string = f"{n:04x}"
        return hex_string

    @classmethod
    def int_to_hex32(cls, n):
        # 确保数值在32位范围内
        if n < -2**31 or n > 2**31-1:
            raise ValueError("The value exceeds the range of a 32-bit integer")
        # 将数值转换为32位无符号整数
        n &= 0xFFFFFFFF
        # 将其转换为32进制字符串，并保证长度为8（不足时左补0）
        hex_string = f"{n:08x}"
        return hex_string

    @classmethod
    def float_to_hex(cls, f):
        # 使用 struct.pack 将浮点数打包为二进制数据（32位单精度浮点数）
        packed = struct.pack('>f', f)

        # 使用 struct.unpack 将二进制数据解包为整数
        unpacked = struct.unpack('>I', packed)[0]

        # 将整数转换为16进制字符串，并保证长度为8（不足时左补0）
        hex_string = f"{unpacked:08x}"

        return hex_string

    def __init__(self, index, _type, value):
        self.index = int(index)
        self.type = _type
        self.length = 0
        self.value = value

    def get_byte(self):
        index_byte = self.int_to_1byte(self.index)
        value_byte = b''
        _type_index = str(self.type)
        if _type_index in self.type_map:
            # _type = self.type_map[_type_index]
            if _type_index in ("0", "b"):  # Byte
                self.type = "0"  # Boolean传输时实际是Byte
                if self.value is True or "true" == self.value.lower():
                    value = "1"
                elif self.value is False or "false" == self.value.lower():
                    value = "0"
                else:
                    value = str(self.value)
                # 补齐到1个字节
                if len(value) % 2 != 0:
                    value = '0' + value
                value_byte = binascii.unhexlify(value)
            elif "1" == _type_index:  # Int16
                value = self.int_to_hex16(int(self.value, 16))
                value_byte = binascii.unhexlify(value)
            elif "2" == _type_index:  # Unsigned Int16
                value_byte = binascii.unhexlify(format(int(self.value, 16), 'x').zfill(4))
            elif "3" == _type_index:  # Int32
                value = self.int_to_hex32(int(self.value))
                value_byte = binascii.unhexlify(value)
            elif "4" == _type_index:  # Unsigned Int32
                # 补齐到4个字节
                value_byte = binascii.unhexlify(format(int(self.value, 16), 'x').zfill(8))
            elif "7" == _type_index:  # Float
                value = self.float_to_hex(float(self.value))
                value_byte = binascii.unhexlify(value)
            elif "9" == _type_index:  # String
                value_byte = bytes(str(self.value), 'ascii')
            else:
                raise ValueError(f"Payload type [{self.type_map[_type_index]}] has not been implemented")
        else:
            raise ValueError(f"Invalid payload type [{_type_index}]")

        # 将value长度数转换为十六进制字符串
        length_hex_string = hex(len(value_byte))[2:]
        # 补齐到6位，如果不足6位则在前面补零
        padded_length_hex_string = length_hex_string.zfill(3)
        type_and_length_hex_string = f"{self.type}{padded_length_hex_string}"
        type_and_length_byte = binascii.unhexlify(type_and_length_hex_string)
        return index_byte + type_and_length_byte + value_byte


if __name__ == "__main__":
    _index = 0
    _type = 0
    _value = '100'
    pd = PayloadData(_index, _type, _value)
    print(pd.get_byte().hex())
    vp = VehiclePayload(_index, _type, _value)
    print(vp.get_byte().hex())
