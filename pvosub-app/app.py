import sys
import requests
from datetime import datetime
from pytz import timezone
from time import sleep, time
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


class PVOutputAPI(object):
    wh_today_last = 0

    def __init__(self, API, systemID):
        self.API = API
        self.systemID = systemID

    def add_status(self, payload):
        """Add live output data. Data should contain the parameters as described
        here: http://pvoutput.org/help.html#api-addstatus ."""
        self.__call("https://pvoutput.org/service/r2/addstatus.jsp", payload)

    def add_output(self, payload):
        """Add end of day output information. Data should be a dictionary with
        parameters as described here: http://pvoutput.org/help.html#api-addoutput ."""
        self.__call("http://pvoutput.org/service/r2/addoutput.jsp", payload)

    def __call(self, url, payload):
        headers = {
            'X-Pvoutput-Apikey': self.API,
            'X-Pvoutput-SystemId': self.systemID,
            'X-Rate-Limit': '1'
        }

        # Make tree attempts
        for i in range(3):
            try:
                r = requests.post(url, headers=headers, data=payload, timeout=10)
                reset = round(float(r.headers['X-Rate-Limit-Reset']) - time())
                if int(r.headers['X-Rate-Limit-Remaining']) < 10:
                    print("Only {} requests left, reset after {} seconds".format(
                        r.headers['X-Rate-Limit-Remaining'],
                        reset))
                if r.status_code == 403:
                    print("Forbidden: " + r.reason)
                    sleep(reset + 1)
                else:
                    r.raise_for_status()
                    break
            except requests.exceptions.HTTPError as errh:
                print(localnow().strftime('%Y-%m-%d %H:%M'), " Http Error:", errh)
            except requests.exceptions.ConnectionError as errc:
                print(localnow().strftime('%Y-%m-%d %H:%M'), "Error Connecting:", errc)
            except requests.exceptions.Timeout as errt:
                print(localnow().strftime('%Y-%m-%d %H:%M'), "Timeout Error:", errt)
            except requests.exceptions.RequestException as err:
                print(localnow().strftime('%Y-%m-%d %H:%M'), "OOps: Something Else", err)

            sleep(3)
        else:
            print(localnow().strftime('%Y-%m-%d %H:%M'), "Failed to call PVOutput API")

    def send_status(self, date, energy_gen=None, power_gen=None, energy_imp=None,
                    power_imp=None, temp=None, vdc=None, cumulative=False, vac=None,
                    temp_inv=None, energy_life=None, comments=None, power_vdc=None):
        # format status payload
        payload = {
            'd': date.strftime('%Y%m%d'),
            't': date.strftime('%H:%M'),
        }

        # Only report total energy if it has changed since last upload
        # this trick avoids avg power to zero with inverter that reports
        # generation in 100 watts increments (Growatt and Canadian solar)
        if ((energy_gen) and
           ((self.wh_today_last > energy_gen) or (self.wh_today_last < energy_gen))):

            self.wh_today_last = int(energy_gen)
            payload['v1'] = int(energy_gen)

        if power_gen:
            payload['v2'] = float(power_gen)
        if energy_imp:
            payload['v3'] = int(energy_imp)
        if power_imp:
            payload['v4'] = float(power_imp)
        if temp:
            payload['v5'] = float(temp)
        if vdc:
            payload['v6'] = float(vdc)
        if cumulative:
            payload['c1'] = 1
        if vac:
            payload['v8'] = float(vac)
        if temp_inv:
            payload['v9'] = float(temp_inv)
        if energy_life:
            payload['v10'] = int(energy_life)
        if comments:
            payload['m1'] = str(comments)[:30]
        # calculate efficiency
        if power_gen and power_vdc:
            payload['v12'] = float(power_gen) / float(power_vdc)

        # Send status
        self.add_status(payload)


def main_loop():
    print('simulate an solar inverter')
    pvo.send_status(date=localnow(), power_gen=1000)
    # this boilerplate works for some seconds then exit
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

    # Local time with timezone
    def localnow():
        return datetime.now(tz=timezone(config['TimeZone']))

    # MQTT Client and connection with topics
    mqttc = MyMQTTClass(client_id="pvosub")
    mqttc.run(config['MQTTHOST'], config['topics'].dict())

    # PVOutput poster
    pvo = PVOutputAPI(config['APIKEY'], config['SYSTEMID'])

    try:
        # run
        main_loop()
    except KeyboardInterrupt:
        mqttc.disconnect()
        mqttc.loop_stop()
        print('\nExiting by user request.\n')
        sys.exit(0)

    # if we reach this point something went wrong so let's gracefully
    # terminate mqtt client loop
    print('Returned from main: stop client loop - this shall never happen')
    mqttc.disconnect()
    mqttc.loop_stop()
