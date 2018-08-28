import sys
import json
import paho.mqtt.publish as publish
from time import sleep
from configobj import ConfigObj
from pyowm import OWM
from pyowm.exceptions import OWMError


class Weather(object):
    API = ''
    lat = 0.0
    lon = 0.0

    def __init__(self, API, lat, lon):
        self.API = API
        self.lat = lat
        self.lon = lon
        self.owm = OWM(self.API)

    def get(self):
        obs = self.owm.weather_at_coords(self.lat, self.lon)
        w = obs.get_weather()
        return w


def main_loop(owm):
    base_topic = 'weather'
    msgs = []
    while True:
        try:
            weather = owm.get()
        except OWMError as err:
            print("Error: ", err)

        json_data = json.loads(weather.to_JSON())

        for key, value in json_data.items():
            # hack for temperature in unit=Celsius
            if key == 'temperature':
                value = weather.get_temperature(unit='celsius')
            # msg = {'topic':"<topic>", 'payload':"<payload>", 'qos':<qos>,
            #  'retain':<retain>}
            if not isinstance(value, dict):
                msg = {}
                msg['topic'] = base_topic + '/' + key
                msg['payload'] = value
                msgs.append(msg)
            else:
                chain_topic = base_topic + '/' + key
                for key2, value2 in value.items():
                    msg = {}
                    msg['topic'] = chain_topic + '/' + key2
                    msg['payload'] = value2
                    msgs.append(msg)

        publish.multiple(msgs, hostname="mqtt", port=1883)
        sleep(60)


if __name__ == '__main__':
    try:
        # set objects
        config = ConfigObj("./config/owm-publisher.conf")
        owm = Weather(config['OWMKEY'], float(config['OWMLAT']), float(config['OWMLON']))

        # run
        main_loop(owm)
    except KeyboardInterrupt:
        print('\nExiting by user request.\n')
        sys.exit(0)
