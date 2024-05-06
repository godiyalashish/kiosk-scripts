import requests
from get_mac_address import get_mac_address
from config import URL


def get_device_info():
    try:
        response = requests.get(URL+'/kiosk/info', headers = {"device":get_mac_address()})
        if response.status_code == 200:
            return response.json()
        else:
            print("failed")
            return None
    except Exception as e:
        print("Error:", e)
        return None

