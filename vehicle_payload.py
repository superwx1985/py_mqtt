import binascii


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
                "8": "Double", "9": "String", "A": "Binary"}

    @classmethod
    def string_to_hex_ascii(cls, s):
        hex_values = [format(ord(char), '02X') for char in s]
        return ''.join(hex_values)

    @classmethod
    def hex_string_to_byte(cls, s):
        # 转换为 bytes 对象
        return bytes.fromhex(s)

    def __init__(self, index, _type, value):
        self.index = index
        self.type = _type
        self.length = 0
        self.value = value

    def get_byte(self):
        index_byte = self.index.to_bytes((self.index.bit_length() + 7) // 8, 'big')
        value_byte = b''
        if self.type in self.type_map:
            _type = self.type_map[self.type]
            if "Byte" == _type:
                # 补齐到一个字节
                value_byte = binascii.unhexlify(self.value.zfill(2))
            elif "String" == _type:
                value_byte = bytes(self.value, 'ascii')
        else:
            raise ValueError("Invalid payload type")

        # 将value长度数转换为十六进制字符串
        length_hex_string = hex(len(value_byte))[2:]
        # 补齐到6位，如果不足6位则在前面补零
        padded_length_hex_string = length_hex_string.zfill(3)
        type_and_length_hex_string = f"{self.type}{padded_length_hex_string}"
        type_and_length_byte = binascii.unhexlify(type_and_length_hex_string)
        return index_byte + type_and_length_byte + value_byte


if __name__ == "__main__":
    pd = PayloadData(105, '9', 'RZ42M82')
    print(pd.get_byte().hex())
    vp = VehiclePayload(105, '9', 'RZ42M82')
    print(vp.get_byte().hex())
