from mqtt_client import MQTTClient
import time
from vehicle_payload import PayloadData, VehiclePayload

host = "cantonrlmudp.globetools.com"
port = 1883
keepalive = 60
username = "163e82bac7ca1f41163e82bac7ca9001"
password = "47919B30B9A23BA33DBB5FA976E99BA2"
client_id = "X:DEVICE;A:2;V:1;"
device_id = "1144502349"


def on_publish(client, userdata, mid, reason_code, properties):
    print(f"Published, {reason_code=}")


def on_message(client, userdata, msg):
    print(f"{msg.topic}: {str(msg.payload)}")


user_client = MQTTClient(host, port, keepalive, username, password, client_id)
user_client.on_publish = on_publish
user_client.on_message = on_message
user_client.start()

user_client.publish(f"$3/{device_id}", PayloadData.hex_string_to_byte("00030000"), 1)
user_client.subscribe(f"$4/{device_id}", 1)
user_client.publish(f"$4/{device_id}", PayloadData.hex_string_to_byte("0004000100"), 0)
user_client.subscribe(f"$7/{device_id}", 1)
user_client.publish(f"$6/{device_id}", VehiclePayload(105, "9", "CZ60R24X").get_byte(), 1)
for i in [104, 211, 1, 2, 3, 215, 4, 5, 217, 216]:
    user_client.publish(f"$6/{device_id}", VehiclePayload(i, "0", "0").get_byte(), 1)


for i in range(10):
    print(i)
    time.sleep(1)
user_client.publish(f"$6/{device_id}", VehiclePayload(104, "0", "11").get_byte(), 1)
for i in range(10):
    print(i)
    time.sleep(1)
user_client.publish(f"$6/{device_id}", VehiclePayload(104, "0", "13").get_byte(), 1)
for i in range(10):
    print(i)
    time.sleep(1)
user_client.stop()
