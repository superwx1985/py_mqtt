from mqtt_client import MQTTClient
import time
from vehicle_payload import PayloadData, VehicleDataPointPayload


class xlinkVehicle:
    def __init__(self, device_id, model, logger=None):
        if logger:
            self.logger = logger
        self.client_id = "X:DEVICE;A:2;V:1;"
        self.host = "cantonrlmudp.globetools.com"
        self.host = "mqtt.eclipseprojects.io"
        self.port = 1883
        self.keepalive = 20
        self.username = "163e82bac7ca1f41163e82bac7ca9001"
        self.password = "47919B30B9A23BA33DBB5FA976E99BA2"
        self.user_client = MQTTClient(self.host, self.port, self.keepalive, self.username, self.password,
                                      self.client_id, 4, self.logger)
        self.device_id = device_id
        self.model = model

    def connect_to_xlink(self):
        self.user_client.start()
        self.user_client.publish(f"$3/{self.device_id}", PayloadData.hex_string_to_byte("00030000"), 1)
        self.user_client.subscribe(f"$4/{self.device_id}", 1)
        self.user_client.publish(f"$4/{self.device_id}", PayloadData.hex_string_to_byte("0004000100"), 0)
        self.user_client.subscribe(f"$7/{self.device_id}", 1)
        self.user_client.subscribe(f"$9/{self.device_id}", 1)
        self.user_client.subscribe(f"$c/{self.device_id}", 1)
        self.user_client.subscribe(f"$h/{self.device_id}", 1)
        self.user_client.subscribe(f"$l/{self.device_id}", 1)
        self.user_client.publish(f"$j/{self.device_id}", PayloadData.hex_string_to_byte("0013000108"), 1)
        self.user_client.subscribe(f"$e", 1)
        self.user_client.publish(f"$6/{self.device_id}", VehicleDataPointPayload(105, "9", f"{self.model}").get_byte(), 1)
        for i in [104, 211, 1, 2, 3, 215, 4, 5, 217, 216]:
            self.user_client.publish(f"$6/{self.device_id}", VehicleDataPointPayload(i, "0", "0").get_byte(), 1)
        # self.user_client.ping

    def publish_error_to_xlink(self, index, value):
        if not isinstance(index, int):
            index = int(index)
        if not isinstance(value, str):
            value = str(value)
        self.user_client.publish(f"$6/{self.device_id}", VehicleDataPointPayload(index, "0", value).get_byte(), 1)

    def disconnect_to_xlink(self):
        self.user_client.stop()


if __name__ == "__main__":
    device_id = "1144502349"
    model = "CZ60R24X"
    client = xlinkVehicle(device_id, model)
    client.connect_to_xlink()
    client.publish_error_to_xlink(104, "11")
    for i in range(10):
        print(i)
        time.sleep(1)
    client.disconnect_to_xlink()
