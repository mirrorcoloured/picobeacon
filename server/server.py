import time
import json

from flask import Flask, request

app = Flask(__name__)

@app.route('/', methods=['GET'])
def home():
    print("Got home request")
    return "Hi I am server", 200

sleep_request = 10

@app.route('/log_data', methods=['POST'])
def log_data():
    # print("Got data input")
    data = json.loads(request.data.decode())
    print('Device', data['mac'])
    # print('!!! DATA', data)

    with open('data.txt', 'a') as file:
        file.write(str(data) + '\n')

    headers = ['stime', 'ctime', 'mac', 'ssid', 'bssid', 'rssi']
    with open('data.csv', 'a') as file:
        for network in data['networks']:
            # print('!!! NETWORK', network)
            if network['ssid'][:7] in ['beacon-', 'Firelin']:
                data_row = ",".join([
                    str(time.time()),
                    str(data['time']),
                    str(data['mac']),
                    str(network['ssid']),
                    str(network['bssid']),
                    str(network['rssi']),
                    ])
                # print('data row', data_row)
                file.write(data_row + "\n")

    return {
        "sleep_request": sleep_request
        }, 200

if __name__ == '__main__':
    # app.run(host="0.0.0.0", debug=True)
    app.run(host="0.0.0.0")