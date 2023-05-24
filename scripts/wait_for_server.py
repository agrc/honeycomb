import requests
from time import sleep

while True:
    try:
        requests.get('https://localhost:6443/arcgis/rest/', verify=False)

        break;
    except Exception as error:
        print('waiting for arcgis server to start')
        sleep(10)
