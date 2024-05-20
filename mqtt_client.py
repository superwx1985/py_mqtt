import time
from log import get_logger
import paho.mqtt.client as mqtt

__all__ = ["MQTTClient"]
logger = get_logger(__name__)


class MQTTClient:

    def __init__(self, host, port, keepalive, username="", password="", client_id=""):
        self.host = host
        self.port = port
        self.mqtt_client_id = client_id
        self.keepalive = keepalive
        self.username = username
        self.password = password
        self.client = None

    def on_connect(self, client, userdata, flags, reason_code, properties):
        if reason_code.is_failure:
            print(f"Failed to connect: {reason_code}. loop_forever() will retry connection")
        else:
            # we should always subscribe from on_connect callback to be sure
            # our subscribed is persisted across reconnections.
            print(f"Connected!")

    def on_message(self, client, userdata, msg):
        # payload = msg.payload.decode('utf-8')
        # payload = payload.replace('\n', '').replace('\r', '').replace(' ', '')
        # logger.debug('subscribe: %s , payload: %s, QoS = %s' % (msg.topic, payload, msg.qos))
        #
        # self.queue.put(msg)
        print(msg.topic + " " + str(msg.payload))

    def on_subscribe(self, client, userdata, mid, reason_code_list, properties):
        # Since we subscribed only for a single channel, reason_code_list contains
        # a single entry
        if reason_code_list[0].is_failure:
            print(f"Broker rejected you subscription: {reason_code_list[0]}")
        else:
            print(f"Broker granted the following QoS: {reason_code_list[0].value}")

    def on_unsubscribe(self, client, userdata, mid, reason_code_list, properties):
        # Be careful, the reason_code_list is only present in MQTTv5.
        # In MQTTv3 it will always be empty
        if len(reason_code_list) == 0 or not reason_code_list[0].is_failure:
            print("unsubscribe succeeded (if SUBACK is received in MQTTv3 it success)")
        else:
            print(f"Broker replied with failure: {reason_code_list[0]}")
        client.disconnect()

    def subscribe(self, topic, qos=0):
        self.client.subscribe(topic, qos)
        logger.info('subscribe the topic: %s' % topic)

    def unsubscribe(self, topic):
        self.client.unsubscribe(topic)
        logger.info('unsubscribe %s' % topic)

    def receive_msg(self, timeout=None):
        logger.info('waiting for message.')
        if timeout is None:
            timeout = self.heartbeat
        return self.queue.get(timeout=timeout)

    def publish(self, topic, payload, qos=0, retain=False):
        self.client.publish(topic, payload, qos, retain)
        logger.debug('public topic = %s, payload = %s , qos = %s, retain = %s' % (topic, payload, qos, retain))

    def log_callback(self, client, userdata, level, msg):
        logger.info('public topic: %s ' % msg)
        pass

    def start(self):
        if self.client is None:
            self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=self.mqtt_client_id)
            self.client.on_connect = self.on_connect
            self.client.on_message = self.on_message
            self.client.on_subscribe = self.on_subscribe
            self.client.on_unsubscribe = self.on_unsubscribe
            self.client.username_pw_set(self.username, self.password)
            self.client.connect(self.host, self.port, self.keepalive)
            logger.info("client('%s') is connected" % self.mqtt_client_id)
            self.client.loop_start()
        else:
            logger.error("mqtt_client object is None")

    def stop(self):
        if self.client is not None:
            self.client.loop_stop()
            logger.info("client('%s')  is disconnected" % self.mqtt_client_id)
            self.client.disconnect()
            self.client = None


if __name__ == '__main__':
    host = "mqtt.eclipseprojects.io"
    port = 1883
    keepalive = 60
    username = ""
    password = ""
    client_id = "test1"

    user_client = MQTTClient(host, port, keepalive, username, password, client_id)
    user_client.start()
    for i in range(5):
        print(i)
        time.sleep(1)
    user_client.stop()


