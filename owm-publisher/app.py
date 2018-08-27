import sys
import paho.mqtt.publish as publish
from time import sleep
from configobj import ConfigObj
from pyowm import OWM


class Weather(object):
    API = ''
    lat = 0.0
    lon = 0.0
    temperature = 0.0
    cloud_pct = 0
    cmo_str = ''

    def __init__(self, API, lat, lon):
        self.API = API
        self.lat = lat
        self.lon = lon
        self.owm = OWM(self.API)

    def get(self):
        obs = self.owm.weather_at_coords(self.lat, self.lon)
        w = obs.get_weather()
        status = w.get_detailed_status()
        self.temperature = w.get_temperature(unit='celsius')['temp']
        self.cloud_pct = w.get_clouds()
        self.cmo_str = ('%s with cloud coverage of %s percent' % (status, self.cloud_pct))
        return w


def main_loop(owm):
    while True:
        print(owm.get().to_JSON())

        # msg = {'topic':"<topic>", 'payload':"<payload>", 'qos':<qos>, 'retain':<retain>}
        # publish.multiple(msgs, hostname="mqtt", port=1883, client_id="", keepalive=60,
        #         will=None, auth=None, tls=None, protocol=mqtt.MQTTv31)
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
