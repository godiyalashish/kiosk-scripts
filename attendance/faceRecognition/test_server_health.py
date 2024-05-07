import requests
import os
import time
import RPi.GPIO as GPIO
import sys
from config import URL,BASE_DIRECTORY

GPIO.setmode(GPIO.BCM)
touch_button_pin = 14
GPIO.setup(touch_button_pin, GPIO.IN, pull_up_down = GPIO.PUD_DOWN)

def check_health(url):
    try:
        response = requests.get(url)
        return response
    except requests.RequestException as e:
        return e

if __name__ == "__main__":
    response = check_health(URL)
    while response.status_code != 200:
        if isinstance(response, requests.Response):  
            os.system(f"python {BASE_DIRECTORY}/display_message.py 'cannot connect' 'to server'")
            time.sleep(3)
            os.system(f"python {BASE_DIRECTORY}/display_message.py 'Touch Button to' ' retry server' 'connection' ")
        else:
            os.system(f"python {BASE_DIRECTORY}/display_message.py 'Err:' '114'")
            time.sleep(3)
            os.system(f"python {BASE_DIRECTORY}/display_message.py 'Touch Button to' ' retry server' 'connection' ")

        while GPIO.input(touch_button_pin) == GPIO.LOW:
            pass
        
        response = check_health(URL)

    if(response.status_code == 200):
        os.system(f"python {BASE_DIRECTORY}/display_message.py 'Server' 'connection' 'successfull'")
        
