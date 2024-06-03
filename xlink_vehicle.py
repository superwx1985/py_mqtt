import paho.mqtt.client as mqtt
import time
import logging
from vehicle_payload import PayloadData, VehiclePayload


class xlinkVehicle:
    def __init__(self, host, port, username, password, device_id, model, logger=None):
        if logger:
            self.logger = logger
        else:
            self.logger = logging.getLogger('xlinkVehicle')
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
            self.client.loop_start()
        except Exception as e:
            self.logger.error(f"Cannot connect to MQTT broker: {e}")

    def publish_error_to_xlink(self, index, value):
        try:
            if not isinstance(index, int):
                index = int(index)
            if not isinstance(value, str):
                value = str(value)
            self.client.publish(f"$6/{self.device_id}", VehiclePayload(index, "0", value).get_byte(), 1)
            self.logger.info(f"Publishing to xlink: index={index}, value={value}")
        except Exception as e:
            self.logger.error(f"Cannot publish to xlink: {e}")

    def disconnect_to_xlink(self):
        try:
            if self.client is not None:
                self.client.loop_stop()
                self.client.disconnect()
                self.client = None
                self.logger.info(f"Client [{self.client_id}] is disconnected")
        except Exception as e:
            self.logger.error(f"Cannot disconnect: {e}")


if __name__ == "__main__":
    host = "cantonrlmudp.globetools.com"
    port = 1883
    username = "163e82bac7ca1f41163e82bac7ca9001"
    password = "47919B30B9A23BA33DBB5FA976E99BA2"
    device_id = "1144502349"
    model = "CZ60R24X"
    client = xlinkVehicle(host, port, username, password, device_id, model)
    client.connect_to_xlink()
    client.publish_error_to_xlink(104, "11")
    for i in range(10):
        print(i)
        time.sleep(1)
    client.disconnect_to_xlink()
