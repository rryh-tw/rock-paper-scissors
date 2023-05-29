import cv2
import mediapipe as mp
from mediapipe import tasks
from mediapipe.tasks.python import vision
from itertools import count
import os
import sys
import time
import random


from PySide6.QtCore import Qt, QThread, Signal, Slot, QTimer
from PySide6.QtGui import QAction, QImage, QKeySequence, QPixmap

from PySide6.QtWidgets import (QApplication, QComboBox, QGroupBox,
                               QHBoxLayout, QLabel, QMainWindow, QPushButton,
                               QSizePolicy, QVBoxLayout, QWidget)




result_text = ""
def callback(result: vision.GestureRecognizerResult, img: mp.Image, timestamp: int):
    global result_text
    result_text = result.gestures[0][0].category_name if result.gestures else "None"



options = vision.GestureRecognizerOptions(
    base_options=tasks.BaseOptions(model_asset_path='gesture_recognizer.task'),
    running_mode=vision.RunningMode.LIVE_STREAM,
    result_callback=callback)
recognizer = vision.GestureRecognizer.create_from_options(options)
    
class Thread(QThread):
    updateFrame = Signal(QImage)
    def __init__(self, parent=None):
        QThread.__init__(self, parent)
        self.status = True
        self.cap = True


    def run(self):
        self.cap = cv2.VideoCapture(0)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1080)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1920)

        for timestamp in count(1):
            ret, frame = self.cap.read()
            if not ret:
                continue

            frame = cv2.flip(frame, 1)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame)
            recognizer.recognize_async(mp_image, timestamp)
            cv2.putText(frame, result_text, (10, 40), cv2.FONT_HERSHEY_COMPLEX_SMALL, 1, (0, 255, 255), 1, cv2.LINE_AA)
            # Reading the image in RGB to display it
            color_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # Creating and scaling QImage
            h, w, ch = color_frame.shape
            img = QImage(color_frame.data, w, h, ch * w, QImage.Format_RGB888)
            scaled_img = img.scaled(640, 480, Qt.KeepAspectRatio)

            # Emit signal
            self.updateFrame.emit(scaled_img)
        sys.exit(-1)

class Game:
    def __init__(self):
        self.avaiable_types = ["Victory", "Closed_Fist", "Open_Palm"]
    
    def compare_winning(self, computer_index, player_index):
        if computer_index == player_index:
            return "tie"
        elif computer_index == (player_index + 1) % 3:
            return "computer win"
        else:
            return "you win"


class Window(QMainWindow):
    def __init__(self):
        super().__init__()
        # Title and dimensions
        self.setWindowTitle("Patterns detection")
        self.setGeometry(0, 0, 800, 500)

        # Create a label for the display camera
        self.label = QLabel(self)
        self.label.setFixedSize(640, 480)

        # Computer label for the display of computer gesture
        self.computer_image_label = QLabel(self)
        self.computer_image_label.setFixedSize(378, 503)

        image_layout = QHBoxLayout()
        image_layout.addWidget(self.label)
        image_layout.addWidget(self.computer_image_label)

        # Thread in charge of updating the image
        self.th = Thread(self)
        self.th.finished.connect(self.close)
        self.th.updateFrame.connect(self.setImage)

        # Buttons layout
        buttons_layout = QHBoxLayout()
        self.button1 = QPushButton("Start")
        self.button2 = QPushButton("Stop/Close")
        self.button1.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        self.button2.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        buttons_layout.addWidget(self.button2)
        buttons_layout.addWidget(self.button1)

        right_layout = QHBoxLayout()
        right_layout.addLayout(buttons_layout, 1)

        # Main layout
        layout = QVBoxLayout()
        layout.addLayout(image_layout)
        layout.addLayout(right_layout)

        # Central widget
        widget = QWidget(self)
        widget.setLayout(layout)
        self.setCentralWidget(widget)

        # Connections
        self.button1.clicked.connect(self.start)
        self.button2.clicked.connect(self.kill_thread)
        self.button2.setEnabled(False)

        # Result Text
        self.text = QLabel("result: ")
        layout.addWidget(self.text, alignment=Qt.AlignmentFlag.AlignCenter)

        self.mylabel = QLabel('timer', self)
        self.mylabel.move(60, 50)
        layout.addWidget(self.mylabel, alignment=Qt.AlignmentFlag.AlignCenter)

        # timer
        self.counter = 5

        self.mytimer = QTimer(self)
        self.mytimer.timeout.connect(self.onTimer)
        self.mytimer.start(1000)

        # win/lose state
        self.WinnerStateText = QLabel("comparing")
        layout.addWidget(self.WinnerStateText, alignment=Qt.AlignmentFlag.AlignCenter)

        

    def onTimer(self):
        self.counter -= 1
        self.mylabel.setText(str(self.counter))
        if self.counter == 0:
            self.counter = 5
            computer_index = random.randint(0, 2)
            img = QImage(f"computer_gesture/{computer_index}.HEIC")
            scaled_img = img.scaled(640, 480, Qt.KeepAspectRatio)

            # Set the QPixmap object as the image for the QLabel
            self.computer_image_label.setPixmap(QPixmap.fromImage(scaled_img))

            if result_text in Game().avaiable_types:
                player_index = Game().avaiable_types.index(result_text)
                self.WinnerStateText.setText(Game().compare_winning(computer_index=computer_index, player_index=player_index))
            else:
                self.WinnerStateText.setText("Wrong Gesture")

    @Slot()
    def kill_thread(self):
        print("Finishing...")
        self.button2.setEnabled(False)
        self.button1.setEnabled(True)
        self.th.cap.release()
        cv2.destroyAllWindows()
        self.status = False
        self.th.terminate()
        # Give time for the thread to finish
        time.sleep(1)

    @Slot()
    def start(self):
        print("Starting...")
        self.button2.setEnabled(True)
        self.button1.setEnabled(False)
        # self.th.set_file(self.combobox.currentText())
        self.th.start()

    @Slot(QImage)
    def setImage(self, image):
        self.label.setPixmap(QPixmap.fromImage(image))
        self.text.setText(result_text)
    



if __name__ == "__main__":
    app = QApplication()
    w = Window()
    w.show()
    sys.exit(app.exec())