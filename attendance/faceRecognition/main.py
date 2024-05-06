import cv2
import multiprocessing
import picamera
import RPi.GPIO as GPIO
import time
import dlib
import numpy as np
import os
import json
from datetime import datetime
from pyzbar.pyzbar import decode
import requests
from urllib.parse import urlparse
from get_mac_address import get_mac_address
from get_device_info import get_device_info
from config import URL, THRESHOLD
from datetime import datetime


#/home/admin/attendance/display_message.py


GPIO.setmode(GPIO.BCM)
touch_button_pin = 14
GPIO.setup(touch_button_pin, GPIO.IN, pull_up_down = GPIO.PUD_DOWN)

def display_message_and_retry(message):
    command = "python /home/admin/attendance/display_message.py"
    for word in message.split():
        command += f" '{word}'"
    os.system(command)
    

os.system("python /home/admin/attendance/display_message.py 'Getting device' 'info..' ")
device_mac_address = get_mac_address()
device_info = get_device_info()
while device_info is None or not device_info.get('isVerified'):
    if device_info is None:
        display_message_and_retry("unable to connect")
    else:
        display_message_and_retry(device_info.get('message'))
    time.sleep(3)
    os.system("python /home/admin/attendance/display_message.py 'Touch button' 'to retry' 'or restart device' ")
    while GPIO.input(touch_button_pin) == GPIO.LOW:
        pass
    os.system("python /home/admin/attendance/display_message.py 'Getting device' 'info..' ")
    device_info = get_device_info()
    if device_info is not None and device_info.get('isVerified'):
        break


device_id = device_info.get('id')
captured_encoding = None


detector = dlib.get_frontal_face_detector()
shape_predictor = dlib.shape_predictor("/home/admin/attendance/faceRecognition/shape_predictor_68_face_landmarks.dat")
face_recognition_model = dlib.face_recognition_model_v1("/home/admin/attendance/faceRecognition/dlib_face_recognition_resnet_model_v1.dat")
os.system("python /home/admin/attendance/display_message.py 'Loading face' 'recognition models..' ")


def verify_employee(code):
    try:
        response = requests.get(URL+'/kiosk/employee/info', headers={"device":device_mac_address, "employee_id":str(code)})
        if response.status_code == 200:
            data = response.json()
            id = data.get('id')
            isRemoved = data.get('isRemoved');
            active = data.get('active');
            if active == False or isRemoved == True:
                return None
            else:
                return id
        else:
            return None
    except Exception as e:
        return None

def capture_face():
    try:
        os.system("python /home/admin/attendance/display_message.py 'Capturing' 'face...' ")
        with picamera.PiCamera() as camera:
            camera.resolution=(720,576)
            #capturing image
            time.sleep(5)
            image_timestamp = str(time.time())
            path = '/home/admin/Desktop/faceRecognition/capture_facedata/'+image_timestamp+'.jpg'
            camera.capture(path)
            return path
    except Exception as e:
        os.system("python /home/admin/attendance/display_message.py 'Failed' 'to capture' 'face' ")
        return None

def get_face_encoding(image):
    img = cv2.imread(image)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    face = detector(gray)
    if len(face)==0:
        return 1
    else:
        shape = shape_predictor(img, face[0])
        face_encoding = face_recognition_model.compute_face_descriptor(img, shape)
        return face_encoding

def get_face_encoding_and_save(image, empId):
    img = cv2.imread(image)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    face = detector(gray)
    if len(face)==0:
        return 1
    else:
        shape = shape_predictor(img, face[0])
        face_encoding = face_recognition_model.compute_face_descriptor(img, shape)
        directory_path = os.path.join(os.getcwd(), 'facedata', str(empId), 'encodings')
        if not os.path.exists(directory_path):
            os.makedirs(directory_path)
        file_name = os.path.basename(image)
        file_path = os.path.join(directory_path, f"{file_name}.npy")
        np.save(file_path, np.array(face_encoding))
        os.remove(image)

def compare_faces(encodings):
        face_encoding1, face_encoding2 = encodings
        distance = np.linalg.norm(np.array(face_encoding1) - np.array(face_encoding2))
        return distance

def get_stored_face_encodings(empId):
    directory_path = '/home/admin/Desktop/faceRecognition/facedata'
    face_encoding_path = os.path.join(directory_path, str(empId), 'encodings')
    if not os.path.exists(face_encoding_path):
        return None
    else:
        files = os.listdir(face_encoding_path)
        if len(files) == 0:
            return np.zeros(128)
        else:
            encodings_paths = [os.path.join(face_encoding_path, file) for file in files]
            return encodings_paths

def get_comparing_images(empId):
    directory_path = '/home/admin/Desktop/faceRecognition/facedata'
    face_data_path = os.path.join(directory_path, str(empId))
    if not os.path.exists(face_data_path):
        os.system("python /home/admin/attendance/display_message.py 'Getting face' 'data...' ")
        resp = download_face_data(empId, directory_path)
        if resp == True:
            os.system("python /home/admin/attendance/display_message.py 'Face data' 'received' ")
            return get_comparing_images(empId)
        else :
            os.system("python /home/admin/attendance/display_message.py 'Failed to get' 'face data' ")
            return []
    else:
        files = os.listdir(face_data_path)
        if len(files) == 0:
            os.system("python /home/admin/attendance/display_message.py 'Getting face' 'data...' ")
            resp = download_face_data(empId, directory_path)
            if resp == True:
                os.system("python /home/admin/attendance/display_message.py 'Face data' 'received' ")
                return get_comparing_images(empId)
            else :
                os.system("python /home/admin/attendance/display_message.py 'Failed to get' 'face data' ")
        else:
            file_paths = [os.path.join(face_data_path, file) for file in files]
            return file_paths

def start_face_recognition(empId):
    result=[]
    image_to_be_compared = capture_face()
    if image_to_be_compared is None:
        return None
    captured_encoding = get_face_encoding(image_to_be_compared)
    face_encodings = get_stored_face_encodings(empId)
    if face_encodings is not None:
        pool = multiprocessing.Pool()
        results = pool.map(compare_faces, [(captured_encoding, np.load(encoding_path)) for encoding_path in face_encodings])
    else:
        images_to_compare_with = get_comparing_images(empId)
        if not image_to_be_compared:
            return result
        pool = multiprocessing.Pool()
        results = pool.map(compare_faces, [(captured_encoding, get_face_encoding_and_save(image_path, empId)) for image_path in images_to_compare_with])
    
    os.remove(image_to_be_compared)
    return results

def download_face_data(empId, local_directory):
    retry_count = 0
    resp = download_and_store_face_data(empId, local_directory)
    while resp is False:
        retry_count += 1
        if retry_count > 3:
            break
        os.system("python /home/admin/attendance/display_message.py 'Failed' 'to fetch' 'face data' ")
        time.sleep(2)
        os.system("python /home/admin/attendance/display_message.py 'Touch to' 'retry' ")
        while GPIO.input(touch_button_pin) == GPIO.LOW:
            pass
        resp = download_and_store_face_data(empId, local_directory) 
    return resp

def download_and_store_face_data(empId, local_directory):
    try:
        
        headers = {
            "device":device_mac_address,
            "Content-Type": "application/json"
        }

        body = {
            "employee": empId
        }
        response = requests.post(URL+'/kiosk/get-all-face-data', headers=headers, json=body)
        responseUrls = response.json()['urls']
        if not responseUrls:
            return False
        for item in responseUrls:
            image_url = item['url']
            image_name = item['name']
            image_path = os.path.join(local_directory, image_name)
            image_response = requests.get(image_url)
            with open(image_path, 'wb') as f:
                f.write(image_response.content)
        return True

    except Exception as e:
        print(f"Error: {e}")
        return False

def decode_qr_code(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    qr_codes = decode(gray)
    for qr_code in qr_codes:
        data = qr_code.data.decode('utf-8')
        return data

def scan_qr_code():
    camera = cv2.VideoCapture(0)
    os.system("python /home/admin/attendance/display_message.py 'Looking for' 'QR code' ")
    data=''
    count = 0
    while True:
        if count>70:
            data = None
            os.system("python /home/admin/attendance/display_message.py 'Failed to scan' 'QR code' 'try again..' ")
            time.sleep(2)
            break
        count += 1
        ret, frame = camera.read()
        if not ret:
            os.system("python /home/admin/attendance/display_message.py 'Failed to scan' 'QR code' ")
            break
        data = decode_qr_code(frame)
        if data is not None:
           break;
    camera.release()
    cv2.destroyAllWindows()
    return data

def check_result_with_threshold(results):
    for result in results:
        if result is not None and result < THRESHOLD:
            return True
    return False

def replace_capture_encoding(empId, encoding):
    file_path = os.path.join(os.cwd, 'facedata', str(empId),'encodings', 'capture.npy')
    if(os.path.exists(file_path)):
        os.remove(file_path)
    np.save(file_path, np.array(encoding))

def markAttendance(empId, date):
    json_file_path = 'attendance.json'
    new_entry = {"empId":empId, "date": date}
    url = URL+"/kiosk/mark-attendance"
    try:
        if os.path.exists(json_file_path):
            with open(json_file_path, 'r') as file:
                data = json.load(file)
            data.append(new_entry)
            with open(json_file_path, 'w') as file:
                json.dump(data, file, indent=4)
        else:
            with open(json_file_path, 'w') as file:
                json.dump([new_entry], file, indent=4)
        
        headers = {"device":get_mac_address(), "Content-Type": "application/json"}
        request_body=[]
        with open(json_file_path, 'r') as file:
            request_body = json.load(file)
        print(request_body)
        response = requests.post(url,headers=headers ,json=request_body)
        if response.status_code == 200:
            print("POST request successful!")
            os.remove(json_file_path)
            return True
        else:
            print("POST request failed. Status code:", response.status_code)
            return False

    except Exception as e:
        print("Error:", e)
        return False

def main():
    os.system("python /home/admin/attendance/display_message.py 'Touch button' 'to start...' ")
    while True:
        if GPIO.input(touch_button_pin) == GPIO.HIGH:
            employee_id = scan_qr_code()
            captured_encoding = None
            
            if employee_id is None:
                os.system("python /home/admin/attendance/display_message.py 'Invalid' 'Employee Id'")
                time.sleep(2)
                os.system("python /home/admin/attendance/display_message.py 'Touch button' 'to start...' ")
                continue
            else:
                is_employee_verified = verify_employee(employee_id)
                if is_employee_verified is None :
                    os.system("python /home/admin/attendance/display_message.py 'Invalid' 'Employee Id'")
                    time.sleep(2)
                    os.system("python /home/admin/attendance/display_message.py 'Touch button' 'to start...' ")
                    continue
                os.system("python /home/admin/attendance/display_message.py 'Employee Id' '{}'".format(employee_id))
                face_comparision_results = start_face_recognition(employee_id)
                if face_comparision_results is None or not face_comparision_results:
                    os.system("python /home/admin/attendance/display_message.py 'Touch button' 'to start...' ")
                    continue
                result = check_result_with_threshold(face_comparision_results)
                if result == True:
                    os.system("python /home/admin/attendance/display_message.py 'Face Recognised' 'successfully' ")
                    resp = markAttendance(employee_id, datetime.now().strftime('%Y-%m-%d'))
                    if resp == False:
                        os.system("python /home/admin/attendance/display_message.py 'Failed' 'to mark attendance' 'try again'")
                        time.sleep(1)
                    replace_capture_encoding(employee_id, captured_encoding)
                    os.system("python /home/admin/attendance/display_message.py 'Touch button' 'to start...' ")
                    continue
                else:
                    os.system("python /home/admin/attendance/display_message.py 'Failed to' 'recognise please' 'try again'")
                    time.sleep(2);
                    os.system("python /home/admin/attendance/display_message.py 'Touch button' 'to start...' ")
                    continue
            time.sleep(.3)
        time.sleep(.1)

if __name__ == "__main__":
    main()
