import paho.mqtt.client as mqtt
import datetime
import time
import hashlib
from vehicle_payload import PayloadData, VehicleDataPointPayload, VehiclePairingPayload
from logger_config import get_logger


def get_utc_string(time_format="%Y%m%d%H%M%S"):
    return datetime.datetime.now(datetime.UTC).strftime(time_format)


class XlinkVehicle:
    def __init__(self, host, port, product_id, product_key, device_id, model, logger=get_logger(__name__)):
        if logger:
            self.logger = logger
        self.client_id = "X:DEVICE;A:2;V:1;"
        self.host = host
        # self.host = "mqtt.eclipseprojects.io"
        self.port = port
        self.keepalive = 20
        self.username = product_id
        self.password = self.generate_password(product_id, product_key)
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=self.client_id, protocol=mqtt.MQTTv311)
        self.device_id = device_id
        self.model = model

    def wait(self, seconds):
        start_time = time.time()
        remaining_time = seconds

        while remaining_time > 0:
            if remaining_time > 10:
                self.logger.info(f"Remaining time: {remaining_time:.0f} s")
                time.sleep(10)
            else:
                self.logger.info(f"Remaining time: {remaining_time:.0f} s")
                time.sleep(1)
            remaining_time = seconds - (time.time() - start_time)

        self.logger.info("Time's up!")

    def on_connect(self, client, userdata, connect_flags, reason_code, properties):
        if reason_code.is_failure:
            self.logger.info(f"Failed to connect. [{reason_code}].n")
        else:
            self.logger.info(f"Connected.")

    def on_disconnect(self, client, userdata, disconnect_flags, reason_code, properties):
        self.logger.info(f"Disconnected. [{reason_code}]")
        # if not self.manual_disconnect:
        #     self.stop()  # 禁止自动重连

    def on_publish(self, client, userdata, mid, reason_code, properties):
        self.logger.info(f"Published. [{reason_code}]")

    def loging_publish(self, *args, **kwargs):
        try:
            self.client.publish(*args, **kwargs)
            self.logger.info(f"Publishing to topic: {args[0]}, payload: {args[1].hex()}, qos: {args[2]}")
        except Exception as e:
            self.logger.error(f"Publish failed: {e}")

    def is_connected(self):
        return self.client.is_connected()

    def on_message(self, client, userdata, message):
        self.logger.info(f"Received message: {message.topic}: {message.payload.hex()}")
        # pairing response
        if message.topic == f"$h/{self.device_id}":
            if len(message.payload) == 14 and message.payload[:2].hex() == "0011":
                index = message.payload[4:6].hex()
                device_id = int(self.device_id)
                user_id = int(message.payload[6:10].hex(), 16)
                pairing_code = int(message.payload[10:14].hex(), 16)
                payload = VehiclePairingPayload(index, True, device_id, user_id, pairing_code).get_byte()
                self.loging_publish(f"$i", payload, 1)
                self.logger.info(f"Accepted pairing request from user {user_id} with pairing code {pairing_code}")

    def connect_to_xlink(self):
        try:
            self.client.username_pw_set(self.username, self.password)
            self.client.on_connect = self.on_connect
            self.client.on_disconnect = self.on_disconnect
            self.client.on_publish = self.on_publish
            self.client.on_message = self.on_message
            self.client.connect(self.host, self.port, self.keepalive)
            self.logger.info(f"Client [{self.client_id}] is connected to {self.host}:{self.port}")
            self.loging_publish(f"$3/{self.device_id}", PayloadData.hex_string_to_byte("00030000"), 1)  # 上线
            # self.client.publish(f"$4/{self.device_id}", PayloadData.hex_string_to_byte("0004000100"), 0)
            self.publish_datapoint_to_xlink(105, "9", self.model)  # model号
            # self.client.subscribe(f"$4/{self.device_id}", 1)
            # self.client.subscribe(f"$7/{self.device_id}", 1)
            # self.client.subscribe(f"$9/{self.device_id}", 1)
            self.client.subscribe(f"$c/{self.device_id}", 1)
            self.client.subscribe(f"$h/{self.device_id}", 1)  # 订阅配对消息
            # self.client.subscribe(f"$l/{self.device_id}", 1)
            # self.client.publish(f"$j/{self.device_id}", PayloadData.hex_string_to_byte("0013000108"), 1)
            # self.client.subscribe(f"$e", 1)

            # for i in [104, 211, 1, 2, 3, 215, 4, 5, 217, 216]:
            #     self.client.publish(f"$6/{self.device_id}", VehiclePayload(i, "0", "0").get_byte(), 1)
            self.publish_datapoint_to_xlink(0, "0", "95")  # 电量
            self.client.loop_start()
        except Exception as e:
            self.logger.error(f"Cannot connect to MQTT broker: {e}")
            raise e

    def disconnect_to_xlink(self):
        try:
            if self.client is not None:
                self.client.loop_stop()
                self.client.disconnect()
                self.client = None
                self.logger.info(f"Client [{self.client_id}] is disconnected")
        except Exception as e:
            self.logger.error(f"Cannot disconnect: {e}")

    def publish_datapoint_to_xlink(self, index, data_type, value, is_hex=False):
        try:
            data_type = str(data_type)
            dp_list = [{"index": index, "type": data_type, "value": value, "is_hex": is_hex}]
            payload = VehicleDataPointPayload(dp_list).get_byte()
            self.client.publish(f"$6/{self.device_id}", payload, 1)
            self.logger.info(f"Publishing DP to xlink: {index=}, type={PayloadData.type_map[data_type]}, {value=}, {is_hex=}, playload={payload.hex()}")
        except Exception as e:
            self.logger.error(f"Cannot publish to xlink: {e}")

    def publish_multiple_datapoint_to_xlink(self, dp_list):
        try:
            payload = VehicleDataPointPayload(dp_list).get_byte()
            self.client.publish(f"$6/{self.device_id}", payload, 1)
            self.logger.info(f"Publishing DP list to xlink: {dp_list}, playload={payload.hex()}")
        except Exception as e:
            self.logger.error(f"Cannot publish to xlink: {e}")

    def publish_error_to_xlink(self, index, value, is_hex=False):
        # if not isinstance(index, int):
        #     index = int(index)
        # if not isinstance(value, str):
        #     value = str(value)
        self.publish_datapoint_to_xlink(index, 0, value, is_hex)

    def toggle_switch(self, status=True):
        """
        A3S-VehiclesGeneralInfo-135
        DP 6
        a. Park status (Byte0 Bit0=0 -> Not parking | Byte0 Bit0=1 -> Parking)
        b. Seat status (Byte0 Bit1=0 -> No seated | Byte0 Bit1=1 -> On seat)
        c. Drive status (Byte0 Bit2=0 -> Stop | Byte0 Bit2=1 -> Running)
        d. Blade status (Byte0 Bit3=0 -> Stop | Byte0 Bit3=1 -> Running)
        DP 214
        e. ETO status  from DP214, 0: off,1: on
        for G20 gen2
        -Bit 0: 0 -> front ETO off, 1 -> front ETO on
        -Bit 1: 0 -> rear ETO off, 1 -> rear ETO on
        DP 106
        power 1 -> on, 0 -> off
        """
        if status:
            self.publish_datapoint_to_xlink(6, 0, "0F", is_hex=True)
            self.publish_datapoint_to_xlink(214, 0, 1)
            self.publish_datapoint_to_xlink(106, 0, 1)
        else:
            self.publish_datapoint_to_xlink(6, 0, "00", is_hex=True)
            self.publish_datapoint_to_xlink(214, 0, 1)
            self.publish_datapoint_to_xlink(106, 0, 1)

    def mock_cutting(self, coordinates=[40.7128, -74.0060]):
        coordinates = [45.42152, -75.69728]
        def change_posisiton(logtiage):
            pass
        # Fleet-ProductDetail-009
        # 0
        self.publish_datapoint_to_xlink(7, 1, 1000)
        self.publish_datapoint_to_xlink(11, 1, 1000)
        self.publish_datapoint_to_xlink(18, 1, 0)
        self.publish_datapoint_to_xlink(24, 1, 0)
        self.publish_datapoint_to_xlink(28, 1, 0)
        self.publish_datapoint_to_xlink(94, 9, f"{get_utc_string()},{coordinates[0]},{coordinates[1]},{get_utc_string()}")
        self.wait(10)

        # 1
        self.publish_datapoint_to_xlink(7, 1, 1000)
        self.publish_datapoint_to_xlink(11, 1, 1000)
        self.publish_datapoint_to_xlink(18, 1, 2000)
        self.publish_datapoint_to_xlink(24, 1, 2000)
        self.publish_datapoint_to_xlink(28, 1, 2000)
        session_id = get_utc_string()
        coordinates[0] += 0.001
        coordinates[1] += 0.001
        self.publish_datapoint_to_xlink(218, 9, f"{session_id},200,2,3,1")
        self.publish_datapoint_to_xlink(94, 9, f"{get_utc_string()},{coordinates[0]},{coordinates[1]},{get_utc_string()}")
        self.wait(10)
        self.wait(10)
        self.wait(10)
        self.wait(10)
        self.wait(10)
        self.wait(10)

        # 2
        coordinates[0] += 0.002
        coordinates[1] += 0.001
        self.publish_datapoint_to_xlink(94, 9, f"{get_utc_string()},{coordinates[0]},{coordinates[1]},{get_utc_string()}")
        self.publish_datapoint_to_xlink(218, 9, f"{session_id},300,3,4,1")
        self.wait(10)

        # 3
        coordinates[0] += 0.001
        coordinates[1] += 0.002
        self.publish_datapoint_to_xlink(18, 1, 0)
        self.publish_datapoint_to_xlink(24, 1, 0)
        self.publish_datapoint_to_xlink(28, 1, 0)
        self.publish_datapoint_to_xlink(94, 9, f"{get_utc_string()},{coordinates[0]},{coordinates[1]},{get_utc_string()}")
        self.publish_datapoint_to_xlink(218, 9, f"{session_id},300,3,4,1")
        self.wait(10)

        4
        self.publish_datapoint_to_xlink(7, 1, 0)
        self.publish_datapoint_to_xlink(11, 1, 0)
        self.wait(10)

        # 5
        self.publish_datapoint_to_xlink(94, 9, f"{get_utc_string()}, 40.7328, -74.0160, {get_utc_string()}")
        self.publish_datapoint_to_xlink(218, 9, f"{session_id},300,4,4,2")
        self.wait(10)

        # 6
        self.wait(60)
        self.publish_datapoint_to_xlink(94, 9, f"{get_utc_string()}, 40.7328, -74.0260, {get_utc_string()}")
        self.publish_datapoint_to_xlink(218, 9, f"{session_id},300,15,4,0")
        self.wait(10)

        # 9
        self.publish_datapoint_to_xlink(7, 1, 1000)
        self.publish_datapoint_to_xlink(11, 1, 1000)
        self.publish_datapoint_to_xlink(18, 1, 2000)
        self.publish_datapoint_to_xlink(24, 1, 2000)
        self.publish_datapoint_to_xlink(28, 1, 2000)
        session_id = get_utc_string()
        self.publish_datapoint_to_xlink(94, 9, f"{get_utc_string()}, 40.7428, -74.0260, {get_utc_string()}")
        self.publish_datapoint_to_xlink(218, 9, f"{session_id},150,1,3,1")
        self.wait(10)
        pass

    @staticmethod
    def generate_password(product_id, product_key):
        def md5_encryption(data):
            md5 = hashlib.md5()  # 创建一个md5对象
            md5.update(data.encode('utf-8'))  # 使用utf-8编码数据
            return md5.hexdigest()  # 返回加密后的十六进制字符串

        return md5_encryption(f'{product_id}{product_key}')


if __name__ == "__main__":
    host = "cantonrlmudp.globetools.com"
    port = 1883
    product_id = '163e82bac7ca1f41163e82bac7ca9001'
    product_key = '78348f781e99ced28bbbbfa73fc3c3ec'

    username = product_id
    password = XlinkVehicle.generate_password(product_id, product_key)
    device_id = "851906253"
    model = "RZ42M82"
    client = XlinkVehicle(host, port, username, password, device_id, model)
    client.connect_to_xlink()
    client.publish_error_to_xlink(104, "11")

    t = bytes.fromhex(f"$h/{device_id}".encode().hex())
    msg = mqtt.MQTTMessage(topic=t)
    msg.payload = bytes.fromhex("0011000a000732c6fb310001b207")
    client.on_message(None, None, msg)
    for i in range(10):
        print(i)
        time.sleep(1)
    client.disconnect_to_xlink()
