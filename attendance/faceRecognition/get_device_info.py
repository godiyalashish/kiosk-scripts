import requests
from get_mac_address import get_mac_address
from config import URL
import json
import os
from config import BASE_DIRECTORY


def get_device_info(isRebooted):
    json_file_path = f'{BASE_DIRECTORY}/faceRecognition/device_info.json'
    try:
        if(isRebooted is False):
            if(os.path.exists(json_file_path)):
                with open(json_file_path, 'r') as file:
                    data = json.load(file)
                return data
        response = requests.get(URL+'/kiosk/info', headers = {"device":get_mac_address()})
        if response.status_code == 200:
            data = response.json()
            print(data)
            os.makedirs(os.path.dirname(json_file_path), exist_ok=True)
            with open(json_file_path, 'w') as file:
                json.dump(data, file, indent=4)
            return data
        return None
    except Exception as e:
        print("Error:", e)
        return None


if __name__ == "__main__":
    get_device_info(True)