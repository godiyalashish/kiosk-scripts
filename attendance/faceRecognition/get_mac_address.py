import os
import re

def get_mac_address():
    try:
        output = os.popen('ifconfig').read()
        mac_address_search = re.search(r'ether\s([0-9a-fA-F]{2}(:[0-9a-fA-F]{2}){5})', output)
        if mac_address_search:
            mac_address = mac_address_search.group(1)
            return mac_address
        else:
            return None

    except Exception as e:
        print("Error:", e)
        return None


