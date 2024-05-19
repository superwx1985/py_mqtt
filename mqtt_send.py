import paho.mqtt.client as mqtt


def on_connect(client, userdata, flags, reason_code, properties):
    print(f"Connected with result code {reason_code}")
    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe("vic_test/20240517")

mqttc = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
mqttc.on_connect = on_connect

mqttc.connect("mqtt.eclipseprojects.io", 1883, 60)
# mqttc.connect("broker.emqx.io", 1883, 60)

topic = "vic_test/20240517"
payload = "Hello, MQTT!"
mqttc.publish(topic, payload)

print("Message published to topic:", topic)

mqttc.disconnect()
