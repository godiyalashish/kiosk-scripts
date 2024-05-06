import requests
import os
import json
import cv2
import urllib.request
import numpy as np
import dlib
import multiprocessing


from config import URL;
from get_mac_address import get_mac_address;



detector = dlib.get_frontal_face_detector()
shape_predictor = dlib.shape_predictor("/home/admin/attendance/faceRecognition/shape_predictor_68_face_landmarks.dat")
face_recognition_model = dlib.face_recognition_model_v1("/home/admin/attendance/faceRecognition/dlib_face_recognition_resnet_model_v1.dat")

missing_files = []


device_mac_address = get_mac_address();

def get_sync_data(codes):
    headers = {
        "device":device_mac_address,
        "Content-Type": "application/json"
    }

    body = {
        "employees": codes
    }
    try:
        response = requests.post(URL+'/kiosk/sync', headers=headers, json=body)
        if response.status_code == 200:
            return json.loads(response.text)
        else:
            return None
    except Exception as e:
        return None

def get_employees_code_to_sync_data(folder_path):
    folder_names = []
    if not os.path.exists(folder_path):
        return folder_names
    for item in os.listdir(folder_path):
        if os.path.isdir(os.path.join(folder_path, item)):
            folder_names.append(item)
    return folder_names

def delete_invalid_files_and_store_new_ones(folder_path, filenames, employee_id):
    
    for filename in filenames:
        file_path = os.path.join(folder_path, filename+'.npy')
        if not os.path.exists(file_path):
            missing_files.append((employee_id, filename))

    if not missing_files:
        return

    for item in os.listdir(folder_path):
        item_path = os.path.join(folder_path, item)
        if os.path.isfile(item_path):
            if item not in filenames:
                os.remove(item_path)
        elif os.path.isdir(item_path):
            if item == 'encodings':
                for encoding in os.listdir(item_path):
                    encoding_path = os.path.join(item_path, encoding)
                    if os.path.isfile(encoding_path):
                        if encoding.replace(".npy", "") not in filenames:
                            os.remove(encoding_path)
                    elif os.path.isdir(item_path):
                        continue
            continue

def sync_data(data):
    for employee_id, filenames in data.items():
        folder_path = os.path.join('/home/admin/attendance/faceRecognition', 'faceData', str(employee_id), 'encodings')
        if not os.path.exists(folder_path):
            os.makedirs(folder_path, exist_ok=True)
        delete_invalid_files_and_store_new_ones(folder_path, filenames, employee_id)

def get_face_encoding(image_path, empId, image_name):
    img = cv2.imread(image_path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    face = detector(gray)
    if len(face)==0:
        return
    else:
        shape = shape_predictor(img, face[0])
        face_encoding = face_recognition_model.compute_face_descriptor(img, shape)
        directory_path = os.path.join('/home/admin/attendance/faceRecognition' ,'faceData', str(empId),'encodings')
        if not os.path.exists(directory_path):
            os.makedirs(directory_path)
        file_path = os.path.join(directory_path, image_name+'.npy')
        np.save(file_path, np.array(face_encoding))

def download_image(image_url, destination_path, image_name):
    try:
        response = requests.get(image_url)
        if response.status_code == 200:
            with open(destination_path, 'wb') as f:
                f.write(response.content)
            return destination_path
        else:
            return None
    except Exception as e:
        return None


def get_image_and_store_encoding(args):
    empId, image = args
    headers = {
        "device": device_mac_address,
        "Content-Type": "application/json"
    }
    body = {
        "employee": empId,
        "image":image
    }
    try:
        response = requests.post(URL+'/kiosk/get-face-data', headers=headers, json=body)
        if response.status_code == 200:
            data = json.loads(response.text)
            downlad_path = os.path.join('/home/admin/attendance/faceRecognition','faceData',str(empId), image)
            res = download_image(data['url'], downlad_path, image)
            if res is None:
                return
            get_face_encoding(downlad_path, empId, image)
            os.remove(downlad_path)
        else:
            return
    except Exception as e:
        return

def main():
    os.system("python /home/admin/attendance/display_message.py 'syncing' 'data...' ")
    codes = get_employees_code_to_sync_data(os.path.join('/home/admin/attendance/faceRecognition','faceData'))
    if not codes:
        os.system("python /home/admin/attendance/display_message.py 'Data' 'Synced' 'Successfully...' ")
        return
    data = get_sync_data(codes)
    if data is None:
        os.system("python /home/admin/attendance/display_message.py 'Failed' 'to sync' 'data' ")
        return
    sync_data(data)
    if missing_files:
        pool = multiprocessing.Pool()
        pool.map(get_image_and_store_encoding, missing_files)
    os.system("python /home/admin/attendance/display_message.py 'Data' 'Synced' 'Successfully...' ")


if __name__ == "__main__":
    main()
