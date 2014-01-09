"""
Created on February 22 2013

@author: sriramm

"""
import sys
sys.dont_write_bytecode = True
from requires import LOOP, SERVER, PORT, SETTINGS
from socket import error as SockErr
from mongoengine import connect, ConnectionError
from pymongo.errors import AutoReconnect


if __name__ == '__main__':
    try:
        connect(host='localhost',
                port=SETTINGS['mongo_port'],
                db=SETTINGS['mongo_db'])
        if len(sys.argv) == 2:
            try:
                S_PORT = int(sys.argv[1])
            except TypeError:
                S_PORT = PORT
                print "Non numeric port. Starting on {0}".format(PORT)
        else:
            S_PORT = PORT
        SERVER.bind(S_PORT)
        SERVER.start()
        print "Started on http://0.0.0.0:{0}".format(S_PORT)
        LOOP.start()
    except KeyboardInterrupt:
        pass
    except SockErr:
        sys.exit("Another program using the port. Please try again")
    except ConnectionError:
        sys.exit("Unable to connect to DB")
    except AutoReconnect:
        sys.exit(
            "Please check if MongoDB is running on port %d"
            % SETTINGS['mongo_port'])
