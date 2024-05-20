import time

import paho.mqtt.client as mqtt


def on_connect(client, userdata, flags, reason_code, properties):
    print(f"Connected with result code {reason_code}")
    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe("$4/851903679")


# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    print(msg.topic+" "+str(msg.payload))


mqttc = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="X:DEVICE;A:2;V:1;")
mqttc.on_connect = on_connect
mqttc.on_message = on_message

username = "163e82bac7ca1f41163e82bac7ca9001"
password = "47919B30B9A23BA33DBB5FA976E99BA2"
mqttc.username_pw_set(username, password)
mqttc.connect("cantonrlmudp.globetools.com", 1883, 60)
# mqttc.connect("broker.emqx.io", 1883, 60)

# Blocking call that processes network traffic, dispatches callbacks and
# handles reconnecting.
# Other loop*() functions are available that give a threaded interface and a
# manual interface.
# mqttc.loop_forever()
mqttc.loop_start()
for i in range(10):
    print(i)
    time.sleep(1)
mqttc.loop_stop()
