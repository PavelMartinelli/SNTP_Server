import time

import ntplib
from time import ctime

client = ntplib.NTPClient()
while True:
    response = client.request('127.0.0.1', port=12345)
    print("Текущее время:", ctime(response.tx_time))
    time.sleep(0.8)