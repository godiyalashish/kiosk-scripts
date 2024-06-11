import os
import subprocess

def get_mac_address():
    try:
        result = subprocess.run(['ip', 'link', 'show'], stdout=subprocess.PIPE, text=True).stdout
        for line in result.split('\n'):
            if 'link/ether' in line:
                return line.split()[1]
    except Exception as e:
        return None


