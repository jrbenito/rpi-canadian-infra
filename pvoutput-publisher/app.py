import sys
from time import sleep
from configobj import ConfigObj, ConfigObjError
from validate import Validator


def main_loop():
    print('boilerplate')


if __name__ == '__main__':
    try:
        # set objects
        try:
            config = ConfigObj("./config/pvoutput-publisher.conf",
                               configspec="pvoutput-configspec.ini")
            validator = Validator()
            config.validate(validator)
        except ConfigObjError:
            print('Could not read config or configspec file', ConfigObjError)

        print(config.items())
        # run
        main_loop()
    except KeyboardInterrupt:
        print('\nExiting by user request.\n')
        sys.exit(0)
