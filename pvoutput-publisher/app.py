import sys
from time import sleep
from configobj import ConfigObj, ConfigObjError
from validate import Validator
import paho.mqtt.client as mqtt


class MyMQTTClass(mqtt.Client):

    def on_connect(self, mqttc, obj, flags, rc):
        print("Connected: "+str(rc))
        # susbscribe to topics of interest
        for key, value in self.topics.items():
            self.subscribe(value, 0)

    def on_message(self, mqttc, obj, msg):
        print(msg.topic+" "+str(msg.qos)+" "+str(msg.payload))

    def on_subscribe(self, mqttc, obj, mid, granted_qos):
        print("Subscribed: "+str(mid)+" "+str(granted_qos))

    # def on_log(self, mqttc, obj, level, string):
    #    print(string)

    def run(self, host, topics):
        self.connect(host, 1883, 60)
        self.topics = topics
        # handles reconnection but not subscriptions
        self.loop_start()


def main_loop():
    print('boilerplate')
    sleep(600)


if __name__ == '__main__':

    # set objects
    try:
        config = ConfigObj("./config/pvoutput-publisher.conf",
                            configspec="pvoutput-configspec.ini")
        validator = Validator()
        config.validate(validator)
    except ConfigObjError:
        print('Could not read config or configspec file', ConfigObjError)

    # MQTT Client and connection with topics
    mqttc = MyMQTTClass()
    mqttc.run(config['MQTTHOST'],config['topics'].dict())

    try:
        # run
        main_loop()

        # if we reach this point something went wrong so let's gracefully
        # terminate mqtt client loop
        print('Returned from main: stop client loop - this shall never happen')
        mqttc.disconnect()
        mqttc.loop_stop()

    except KeyboardInterrupt:
        mqttc.disconnect()
        mqttc.loop_stop()
        print('\nExiting by user request.\n')
        sys.exit(0)
