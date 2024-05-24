detector = dlib.get_frontal_face_detector()

# Load shape predictor
shape_predictor_path = os.path.join(BASE_DIRECTORY, "faceRecognition", "shape_predictor_68_face_landmarks.dat")
shape_predictor = dlib.shape_predictor(shape_predictor_path)

# Load face recognition model
face_recognition_model_path = os.path.join(BASE_DIRECTORY, "faceRecognition", "dlib_face_recognition_resnet_model_v1.dat")
face_recognition_model = dlib.face_recognition_model_v1(face_recognition_model_path)

# Display loading message
def display_loading_message():
    os.system(f"python {BASE_DIRECTORY}/display_message.py 'Loading face recognition models...'")

# Call the function to display loading message
display_loading_message()

