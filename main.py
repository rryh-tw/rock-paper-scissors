import cv2
import mediapipe as mp
from mediapipe import tasks
from mediapipe.tasks.python import vision
from itertools import count

def main():

    def callback(result: vision.GestureRecognizerResult, img: mp.Image, timestamp: int):
        nonlocal text
        text = f"{timestamp} {result.gestures[0][0].category_name}" if result.gestures else f"{timestamp}"

    text = ""

    options = vision.GestureRecognizerOptions(
        base_options=tasks.BaseOptions(model_asset_path='gesture_recognizer.task'),
        running_mode=vision.RunningMode.LIVE_STREAM,
        result_callback=callback)

    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1080)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1920)

    with vision.GestureRecognizer.create_from_options(options) as recognizer:
        for timestamp in count(1):
            ret, frame = cap.read()
            if ret :
                frame = cv2.flip(frame, 1)
                mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame)
                print(mp_image)
                recognizer.recognize_async(mp_image, timestamp)
                cv2.putText(frame, text, (10, 40), cv2.FONT_HERSHEY_COMPLEX_SMALL, 1, (0, 255, 255), 1, cv2.LINE_AA)
                cv2.imshow('Mediapipe Feed', frame)
            if cv2.waitKey(1) == 27:
                break
    
    cap.release()
    cv2.destroyAllWindows()

if __name__ == '__main__':
    main()