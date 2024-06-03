import paho.mqtt.client as mqtt
import time
from vehicle_payload import PayloadData, VehiclePayload


class XlinkVehicle:
    def __init__(self, host, port, username, password, device_id, model, logger=logging.getLogger(__name__)):
        if logger:
            self.logger = logger
        self.client_id = "X:DEVICE;A:2;V:1;"
        self.host = host
        # self.host = "mqtt.eclipseprojects.io"
        self.port = port
        self.keepalive = 20
        self.username = username
        self.password = password
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

    def is_connected(self):
        return self.client.is_connected()

    def connect_to_xlink(self):
        try:
            self.client.username_pw_set(self.username, self.password)
            self.client.on_connect = self.on_connect
            self.client.on_disconnect = self.on_disconnect
            self.client.on_publish = self.on_publish
            self.client.connect(self.host, self.port, self.keepalive)
            self.logger.info(f"Client [{self.client_id}] is connected to {self.host}:{self.port}")

            self.client.publish(f"$3/{self.device_id}", PayloadData.hex_string_to_byte("00030000"), 1)
            # self.client.subscribe(f"$4/{self.device_id}", 1)
            # self.client.publish(f"$4/{self.device_id}", PayloadData.hex_string_to_byte("0004000100"), 0)
            # self.client.subscribe(f"$7/{self.device_id}", 1)
            # self.client.subscribe(f"$9/{self.device_id}", 1)
            # self.client.subscribe(f"$c/{self.device_id}", 1)
            # self.client.subscribe(f"$h/{self.device_id}", 1)
            # self.client.subscribe(f"$l/{self.device_id}", 1)
            # self.client.publish(f"$j/{self.device_id}", PayloadData.hex_string_to_byte("0013000108"), 1)
            # self.client.subscribe(f"$e", 1)
            # self.client.publish(f"$6/{self.device_id}", VehiclePayload(105, "9", f"{self.model}").get_byte(), 1)
            # for i in [104, 211, 1, 2, 3, 215, 4, 5, 217, 216]:
            #     self.client.publish(f"$6/{self.device_id}", VehiclePayload(i, "0", "0").get_byte(), 1)
            self.publish_datapoint_to_xlink(0, "0", "63")
            self.client.loop_start()
        except Exception as e:
            self.logger.error(f"Cannot connect to MQTT broker: {e}")

    def disconnect_to_xlink(self):
        try:
            if self.client is not None:
                self.client.loop_stop()
                self.client.disconnect()
                self.client = None
                self.logger.info(f"Client [{self.client_id}] is disconnected")
        except Exception as e:
            self.logger.error(f"Cannot disconnect: {e}")

    def publish_datapoint_to_xlink(self, index, data_type, value):
        data_type = str(data_type)
        try:
            self.client.publish(f"$6/{self.device_id}", VehiclePayload(index, data_type, value).get_byte(), 1)
            self.logger.info(f"Publishing to xlink: {index=}, type={PayloadData.type_map[data_type]}, {value=}")
        except Exception as e:
            self.logger.error(f"Cannot publish to xlink: {e}")

    def publish_error_to_xlink(self, index, value):
        # if not isinstance(index, int):
        #     index = int(index)
        # if not isinstance(value, str):
        #     value = str(value)
        self.publish_datapoint_to_xlink(index, 0, value)

    def mock_cutting(self):
        # Fleet-ProductDetail-009
        # 1
        self.publish_datapoint_to_xlink(7, 1, 1000)
        self.publish_datapoint_to_xlink(11, 1, 1000)
        self.publish_datapoint_to_xlink(18, 1, 2000)
        self.publish_datapoint_to_xlink(24, 1, 2000)
        self.publish_datapoint_to_xlink(28, 1, 2000)
        session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.publish_datapoint_to_xlink(94, 9, f"{datetime.now().strftime("%Y%m%d%H%M%S")}, 40.7128, -74.0060, {datetime.now().strftime("%Y%m%d%H%M%S")}")
        self.publish_datapoint_to_xlink(218, 9, f"{session_id},200,2,3,1")
        self.wait(60)

        # 2
        self.publish_datapoint_to_xlink(94, 9, f"{datetime.now().strftime("%Y%m%d%H%M%S")}, 40.7228, -74.0060, {datetime.now().strftime("%Y%m%d%H%M%S")}")
        self.publish_datapoint_to_xlink(218, 9, f"{session_id},300,3,4,1")
        self.wait(10)

        # 3
        self.publish_datapoint_to_xlink(18, 1, 0)
        self.publish_datapoint_to_xlink(24, 1, 0)
        self.publish_datapoint_to_xlink(28, 1, 0)
        self.publish_datapoint_to_xlink(94, 9, f"{datetime.now().strftime("%Y%m%d%H%M%S")}, 40.7228, -74.0160, {datetime.now().strftime("%Y%m%d%H%M%S")}")
        self.publish_datapoint_to_xlink(218, 9, f"{session_id},300,3,4,2")
        self.wait(10)

        #4
        self.publish_datapoint_to_xlink(7, 1, 0)
        self.publish_datapoint_to_xlink(11, 1, 0)
        self.wait(10)

        # 5
        self.publish_datapoint_to_xlink(94, 9, f"{datetime.now().strftime("%Y%m%d%H%M%S")}, 40.7328, -74.0160, {datetime.now().strftime("%Y%m%d%H%M%S")}")
        self.publish_datapoint_to_xlink(218, 9, f"{session_id},300,4,4,1")
        self.wait(10)

        # 6
        self.wait(60)
        self.publish_datapoint_to_xlink(94, 9, f"{datetime.now().strftime("%Y%m%d%H%M%S")}, 40.7328, -74.0260, {datetime.now().strftime("%Y%m%d%H%M%S")}")
        self.publish_datapoint_to_xlink(218, 9, f"{session_id},300,15,4,0")
        self.wait(10)

        # 9
        self.publish_datapoint_to_xlink(7, 1, 1000)
        self.publish_datapoint_to_xlink(11, 1, 1000)
        self.publish_datapoint_to_xlink(18, 1, 2000)
        self.publish_datapoint_to_xlink(24, 1, 2000)
        self.publish_datapoint_to_xlink(28, 1, 2000)
        session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.publish_datapoint_to_xlink(94, 9, f"{datetime.now().strftime("%Y%m%d%H%M%S")}, 40.7428, -74.0260, {datetime.now().strftime("%Y%m%d%H%M%S")}")
        self.publish_datapoint_to_xlink(218, 9, f"{session_id},150,1,3,1")
        self.wait(10)
        pass


if __name__ == "__main__":
    host = "cantonrlmudp.globetools.com"
    port = 1883
    username = "163e82bac7ca1f41163e82bac7ca9001"
    password = "47919B30B9A23BA33DBB5FA976E99BA2"
    device_id = "1144502349"
    model = "CZ60R24X"
    client = XlinkVehicle(device_id, model)
    client.connect_to_xlink()
    client.publish_error_to_xlink(104, "11")
    for i in range(10):
        print(i)
        time.sleep(1)
    client.disconnect_to_xlink()
