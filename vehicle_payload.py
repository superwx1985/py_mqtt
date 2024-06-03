import binascii
import struct


class VehiclePayload:

    @classmethod
    def change_bin_str_to_byte(cls, binary_string):
        # 将二进制字符串转换为整数
        integer_value = int(binary_string, 2)
        # 将整数转换为字节对象
        byte_object = integer_value.to_bytes((integer_value.bit_length() + 7) // 8, byteorder='big')
        return byte_object

    def __init__(self, index, _type, value, is_hex=False):
        self.payload_type = "0006"  # 数据包类型
        self.sync_datapoint_flag = "01100000"  # 数据端点上报标识
        # 7 设备名称标识（name flag）
        # 6 数据端点标识（dp flag）表示datapoint payload是否有数据端点数据
        # 5 数据端点模板标识（template flag）表示 datapoint payload是非数据模板类型的端点数据
        # 4 不推送消息标识（unPush flag）
        # 3 指定时间标识（timestamp flag）根据当前时区，8个字节Unix时间戳，在设备名称（如果有的话）后面，在datapoint payload前面
        # 2 数据端点解析失败返回结果不断开连接（MQTT标准协议解析失败或其他错误仍然断开连接），当开启本选项时，在时间标识后面增加两个字节的MsgID
        # 1~0 预留
        self.payload_data_byte = PayloadData(index, _type, value, is_hex).get_byte()
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
    def is_float(cls, value):
        try:
            float(value)
            return '.' in value
        except ValueError:
            return False

    @classmethod
    def float_to_hex(cls, f):
        # 将浮点数转换为十六进制表示（IEEE 754 标准）
        return hex(struct.unpack('<I', struct.pack('<f', f))[0])

    @classmethod
    def dec_to_hex_with_complement(cls, decimal_str, hex_digits):
        if cls.is_float(decimal_str):
            # 输入值是浮点数
            decimal_number = float(decimal_str)

            # 将浮点数转换为十六进制字符串
            hex_str = cls.float_to_hex(decimal_number)[2:].upper()

            # 确保十六进制字符串的长度符合要求，不足则补零
            hex_str = hex_str.zfill(hex_digits)
        else:
            # 输入值是整数
            decimal_number = int(decimal_str)

            # 计算十六进制的最大值
            max_value = 2 ** (4 * hex_digits)

            # 如果是负数，计算其补码
            if decimal_number < 0:
                decimal_number = max_value + decimal_number

            # 将整数转换为十六进制字符串，去掉'0x'前缀，并转换为大写
            hex_str = hex(decimal_number)[2:].upper()

            # 确保十六进制字符串的长度符合要求，不足则补零
            hex_str = hex_str.zfill(hex_digits)

        # 返回最终的十六进制字符串
        return hex_str

    def __init__(self, index, _type, value, is_hex=False):
        self.index = int(index)
        self.type = _type
        self.length = 0
        self.value = value
        self.is_hex = is_hex

    def get_byte(self):
        index_byte = self.int_to_1byte(self.index)
        _type_index = str(self.type)
        if _type_index in self.type_map:
            if _type_index in ("0", "b"):  # Byte
                self.type = "0"  # Boolean传输时实际是Byte
                if self.value is True or "true" == self.value.lower():
                    value = "01"
                elif self.value is False or "false" == self.value.lower():
                    value = "00"
                else:
                    if self.is_hex:
                        value = str(self.value).zfill(2)
                    else:
                        value = self.dec_to_hex_with_complement(self.value, 2)
                # 补齐到偶数位
                # if len(value) % 2 != 0:
                #     value = '0' + value
                value_byte = binascii.unhexlify(value)
            elif _type_index in ("1", "2"):  # Int16, Unsigned Int16
                # value = self.int_to_hex16(int(self.value, 16))
                if self.is_hex:
                    value = str(self.value).zfill(4)
                else:
                    value = self.dec_to_hex_with_complement(self.value, 4)
                value_byte = binascii.unhexlify(value)
            elif _type_index in ("3", "4", "7"):  # Int32, Unsigned Int32, Float
                if self.is_hex:
                    value = str(self.value).zfill(8)
                else:
                    value = self.dec_to_hex_with_complement(self.value, 8)
                value_byte = binascii.unhexlify(value)
            elif _type_index in ("5", "6"):  # Int64, Unsigned Int64
                if self.is_hex:
                    value = str(self.value).zfill(16)
                else:
                    value = self.dec_to_hex_with_complement(self.value, 16)
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
    _index = 1
    _type = 3
    _value = '10'
    _is_hex = True
    pd = PayloadData(_index, _type, _value, _is_hex)
    print(pd.get_byte().hex())
    vp = VehiclePayload(_index, _type, _value, _is_hex)
    print(vp.get_byte().hex())
