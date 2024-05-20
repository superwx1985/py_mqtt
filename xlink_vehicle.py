from mqtt_client import MQTTClient
import time

host = "cantonrlmudp.globetools.com"
port = 1883
keepalive = 60
username = "163e82bac7ca1f41163e82bac7ca9001"
password = "47919B30B9A23BA33DBB5FA976E99BA2"
client_id = "X:DEVICE;A:2;V:1;"

user_client = MQTTClient(host, port, keepalive, username, password, client_id)
user_client.start()

# 16 进制字符串
hex_payload = "00030000"
# 转换为 bytes 对象
payload = bytes.fromhex(hex_payload)
user_client.publish("$3/851903679", payload, 1)
user_client.subscribe("$4/851903679", 1)

for i in range(10):
    print(i)
    time.sleep(1)
user_client.stop()
