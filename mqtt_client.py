import time
import logging
from log import get_logger
import paho.mqtt.client as mqtt

__all__ = ["MQTTClient"]


class MQTTClient:

    def __init__(self, host, port, keepalive, username="", password="", client_id="", mqtt_protocol=mqtt.MQTTv311, logger=None):
        if logger:
            self.logger = logger
        else:
            self.logger = get_logger(__name__)
            self.logger.setLevel(logging.DEBUG)
        self.host = host
        self.port = port
        self.mqtt_client_id = client_id
        self.mqtt_protocol = mqtt_protocol
        self.keepalive = keepalive
        self.username = username
        self.password = password
        self.client = None
        self.additional_attr = dict()
        self.manual_disconnect = False

    def on_connect(self, client, userdata, flags, reason_code, properties):
        if reason_code.is_failure:
            self.logger.info(f"Failed to connect: {reason_code}. loop_forever() will retry connection")
        else:
            # we should always subscribe from on_connect callback to be sure
            # our subscribed is persisted across reconnections.
            self.logger.info(f"Connected!")

    # 回调函数 - 连接断开时被调用
    def on_disconnect(self, client, userdata, disconnect_flags, reason_code, properties):
        self.logger.info(f"Disconnected with result code {reason_code}")
        # if not self.manual_disconnect:
        #     self.stop()  # 禁止自动重连

    def on_message(self, client, userdata, msg):
        self.logger.info(f"{msg.topic}: {str(msg.payload)}")

    def on_publish(self, client, userdata, mid, reason_code, properties):
        self.logger.info(f"Published, {reason_code=}")

    def on_subscribe(self, client, userdata, mid, reason_code_list, properties):
        # Since we subscribed only for a single channel, reason_code_list contains
        # a single entry
        if reason_code_list[0].is_failure:
            self.logger.info(f"Broker rejected you subscription: {reason_code_list[0]}")
        else:
            self.logger.info(f"Broker granted the following QoS: {reason_code_list[0].value}")

    def on_unsubscribe(self, client, userdata, mid, reason_code_list, properties):
        # Be careful, the reason_code_list is only present in MQTTv5.
        # In MQTTv3 it will always be empty
        if len(reason_code_list) == 0 or not reason_code_list[0].is_failure:
            self.logger.info("unsubscribe succeeded (if SUBACK is received in MQTTv3 it success)")
        else:
            self.logger.info(f"Broker replied with failure: {reason_code_list[0]}")

    def subscribe(self, topic, qos=0):
        self.client.subscribe(topic, qos)
        self.logger.info('subscribe the topic: %s' % topic)

    def unsubscribe(self, topic):
        self.client.unsubscribe(topic)
        self.logger.info('unsubscribe %s' % topic)

    def publish(self, topic, payload, qos=0, retain=False):
        self.client.publish(topic, payload, qos, retain)
        self.logger.info('public topic = %s, payload = %s , qos = %s, retain = %s' % (topic, payload.hex(), qos, retain))


    def start(self):
        if self.client is None:
            self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2,
                                      client_id=self.mqtt_client_id,
                                      protocol=self.mqtt_protocol)
            self.client.on_connect = self.on_connect
            self.client.on_disconnect = self.on_disconnect
            self.client.on_message = self.on_message
            self.client.on_publish = self.on_publish
            self.client.on_subscribe = self.on_subscribe
            self.client.on_unsubscribe = self.on_unsubscribe
            self.client.username_pw_set(self.username, self.password)
            self.client.reconnect_delay_set(min_delay=5, max_delay=10)
            self.client.connect(self.host, self.port, self.keepalive)
            self.manual_disconnect = False
            self.logger.info("client('%s') is connected" % self.mqtt_client_id)
            self.client.loop_start()
        else:
            self.logger.error("mqtt_client object is None")

    def stop(self):
        if self.client is not None:
            # self.client.loop_stop()
            self.logger.info("client('%s')  is disconnected" % self.mqtt_client_id)
            self.manual_disconnect = True
            self.client.disconnect()
            self.client.loop_stop()
            self.client = None


if __name__ == '__main__':
    host = "mqtt.eclipseprojects.io"
    port = 1883
    keepalive = 60
    username = ""
    password = ""
    client_id = "test1"

    user_client = MQTTClient(host, port, keepalive, username, password, client_id, mqtt.MQTTv311)
    user_client.start()
    for i in range(5):
        print(i)
        time.sleep(1)
    user_client.stop()


