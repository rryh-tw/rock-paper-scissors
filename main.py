import random as rd
import cv2
import mediapipe as mp
from mediapipe import tasks
from mediapipe.tasks.python import vision
from itertools import count
from PySide6.QtCore import Qt, QTimer, QThread, Signal, Slot
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import (
    QApplication, QHBoxLayout,QLabel,  QMainWindow,
    QPushButton, QVBoxLayout, QWidget
    )

class Thread(QThread):
    signal = Signal(QImage, str)
    def __init__(self, parent):
        super().__init__(parent)
        self.text = ""
        options = vision.GestureRecognizerOptions(
            base_options=tasks.BaseOptions(model_asset_path='gesture_recognizer.task'),
            running_mode=vision.RunningMode.LIVE_STREAM,
            result_callback=self.callback
        )
        self.recognizer = vision.GestureRecognizer.create_from_options(options)

    def callback(self, result, img, timestamp):
        if result.gestures:
            self.text = result.gestures[0][0].category_name
        else:
            self.text = 'None'

    def run(self):
        self.cap = cv2.VideoCapture(0)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1080)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1920)
        for timestamp in count(1):
            ret, frame = self.cap.read()
            if not ret:
                return
            frame = cv2.flip(frame, 1)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame)
            self.recognizer.recognize_async(mp_image, timestamp)

            cv2.putText(frame, self.text, (20, 20), cv2.FONT_HERSHEY_COMPLEX_SMALL, 1, (0, 255, 255))
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            h, w, c = frame.shape
            qt_image = QImage(frame.data, w, h, c * w, QImage.Format.Format_RGB888)
            

            self.signal.emit(qt_image, self.text)


class MainWindow(QMainWindow):
    def __init__(self):
        self.width = 1040
        self.height = 520
        self.winner_count = [0, 0]
        super().__init__()
        self.setWindowTitle("AI猜猜拳")
        self.setGeometry(0, 0, self.width, self.height)

        self._thread = Thread(self)
        self._thread.signal.connect(self.update)

        self.player = QLabel(self)
        self.computer = QLabel(self)
        img = QImage(f"resources/3.jpg")
        img = img.scaled(self.width * 0.4, self.height * 0.7, Qt.AspectRatioMode.KeepAspectRatio)
        self.computer.setPixmap(QPixmap.fromImage(img))

        self.text = QLabel("Loading...")
        self.state = QLabel("Comparing")
        self.count = QLabel("")
        self.scoreboard = QLabel("0:0")
        
        stream = QHBoxLayout()
        stream.addWidget(self.player, alignment=Qt.AlignmentFlag.AlignLeft)
        stream.addWidget(self.scoreboard, alignment=Qt.AlignmentFlag.AlignCenter)
        stream.addWidget(self.computer, alignment=Qt.AlignmentFlag.AlignRight)

        

        self.btn_start = QPushButton("Start")
        self.btn_finish = QPushButton("Finish")

        self.btn_finish.setEnabled(False)

        self.btn_start.clicked.connect(self.start)
        self.btn_finish.clicked.connect(self.finish)

        buttons = QHBoxLayout()
        buttons.addWidget(self.btn_start)
        buttons.addWidget(self.btn_finish)

        layout = QVBoxLayout()
        layout.addLayout(stream)
        layout.addWidget(self.text, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.state, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.count, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addLayout(buttons)
        
        widget = QWidget(self)
        widget.setLayout(layout)

        self.setCentralWidget(widget)

        self._thread.start()

    def onTimer(self):
        self.counter -= 1
        self.count.setText(str(max(0, self.counter//5)))

        if self.counter // 5 > 2:
            self.count.setStyleSheet("background-color: green; border: 1px solid black;")
        elif self.counter // 5 > 0:
            self.count.setStyleSheet("background-color: yellow; border: 1px solid black;")
        else:
            self.count.setStyleSheet("background-color: red; border: 1px solid black;")

        if self.counter == 0:
            index = rd.randint(0, 2)
            img = QImage(f"resources/{index}.jpg")
            img = img.scaled(self.width * 0.4, self.height * 0.7, Qt.AspectRatioMode.KeepAspectRatio)
            self.computer.setPixmap(QPixmap.fromImage(img))
            gesture = ["Victory", "Closed_Fist", "Open_Palm"]
            if self._thread.text in gesture:
                player_index = gesture.index(self._thread.text)
                if index == player_index:
                    res = "Tie"
                elif index == (player_index + 1) % 3:
                    res = "Computer wins"
                    self.winner_count[1] += 1
                else:
                    res = "Human wins"
                    self.winner_count[0] += 1
                self.state.setText(res)
                self.scoreboard.setText(f'{self.winner_count[0]}:{self.winner_count[1]}')
            else:
                self.state.setText("Wrong Gesture")   
        elif self.counter < 0:
            if self.counter == -10:
                self.counter = 25
                self.state.setText("comparing")
        else:
            img = QImage(f"resources/{self.counter % 3}.jpg")
            img = img.scaled(self.width * 0.4, self.height * 0.7, Qt.AspectRatioMode.KeepAspectRatio)
            self.computer.setPixmap(QPixmap.fromImage(img))
   
    def start(self):
        print("Starting...")
        self.btn_start.setEnabled(False)
        self.btn_finish.setEnabled(True)
        self.counter = 25
        self.mytimer = QTimer(self)
        self.mytimer.timeout.connect(self.onTimer)
        self.mytimer.start(200)
    
    def finish(self):
        print("Finishing...")
        self.btn_finish.setEnabled(False)
        self._thread.cap.release()
        self._thread.terminate()
        app.exit()

    @Slot(QImage, str)
    def update(self, image, text):
        image = image.scaled(self.width * 0.4, self.height * 0.7, Qt.AspectRatioMode.KeepAspectRatio)
        self.player.setPixmap(QPixmap.fromImage(image))
        self.text.setText(text)


if __name__ == "__main__":
    app = QApplication()
    window = MainWindow()
    window.show()
    app.exec()
