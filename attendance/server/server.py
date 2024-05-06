from flask import Flask, send_file, redirect, request, jsonify
import subprocess
import threading
import os

app = Flask(__name__)

def shutdown_server():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug server')
    func()
    
def perform_post_response_actions(password, ssid):
    # Execute subprocess commands here
    subprocess.run(['sudo', 'tee', '-a', '/etc/wpa_supplicant/wpa_supplicant.conf'], input=f'\nnetwork={{\n ssid="{ssid}"\n psk="{password}"\n}}\n'.encode(), check=True)
    subprocess.run(['sudo', '/usr/bin/autohotspot'])
    shutdown_server()

@app.route('/')
def hello():
    return send_file('./index.html')

@app.route('/connect', methods=['POST'])
def connectWifi():
    data = request.json;
    password = data.get('password')
    ssid = data.get('ssid')
    threading.Thread(target=perform_post_response_actions, args=(password, ssid)).start()
    return jsonify({"message": "under process"})





if __name__ == '__main__':
    os.system('/home/admin/attendnce/display_message.py "Hotspot open please" "visit ip address and" "enter wifi cred."')
    app.run(host='0.0.0.0', port=80)
