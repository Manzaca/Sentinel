import sys
import datetime
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QLabel, QLineEdit, QStackedWidget, QProgressBar, QFileDialog
from PyQt5.QtGui import QPixmap
import requests
import platform
import os
import time
import dep_signing as signature

secret_key = '0000000000000000'  # Secret key for signing
version = '1.0'  # Version of the program



# Function to get the path to the resource files

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)




class MyApp(QWidget):
    def __init__(self):
        super().__init__()

        self.start_time = None  # Stores exam start time
        self.submission_time = None  # Stores submission time
        self.exam_path = None  # Stores selected file path
        self.elapsed_time = 0  # Stores the elapsed time in seconds

        self.initUI()
    
    def closeEvent(self, event):
        disable_proxy()
        event.accept()

    def initUI(self):
        self.setWindowTitle(f'Sentinel - Secure Exam Environment - {version+'.'+ secret_key[12:]}')
        self.setGeometry(100, 100, 500, 400)

        self.stacked_widget = QStackedWidget()
        self.setLayout(QVBoxLayout())
        self.layout().addWidget(self.stacked_widget)

        self.create_intro_screen()
        self.create_exam_setup_screen()
        self.create_exam_screen()

        self.stacked_widget.setCurrentWidget(self.intro_screen)

    def create_logo(self):
        logo_label = QLabel(self)
        logo_label.setPixmap(QPixmap(resource_path('logo_long.png')).scaled(457, 100))
        logo_label.setAlignment(Qt.AlignCenter)
        return logo_label

    def create_intro_screen(self):
        self.intro_screen = QWidget()
        layout = QVBoxLayout()

        layout.addWidget(self.create_logo())

        intro_text = '''Welcome to Sentinel

This program has been designed to ensure a secure and distraction-free environment during your exam.

The device will have no internet access during the exam, and any attempt to connect to the internet will immediately terminate the program and invalidate your exam credentials.'''
        text_label = QLabel(intro_text, self)
        text_label.setWordWrap(True)
        text_label.setAlignment(Qt.AlignLeft)
        layout.addWidget(text_label)

        proceed_button = QPushButton('Proceed to the Exam Setup', self)
        proceed_button.clicked.connect(lambda: self.stacked_widget.setCurrentWidget(self.exam_setup_screen))
        layout.addWidget(proceed_button)

        self.intro_screen.setLayout(layout)
        self.stacked_widget.addWidget(self.intro_screen)

    def create_exam_setup_screen(self):
        self.exam_setup_screen = QWidget()
        layout = QVBoxLayout()

        layout.addWidget(self.create_logo())

        # Exam length label
        exam_label = QLabel(f'Exam Length: BRUH minutes', self)
        exam_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(exam_label)

        # Space for additional text (you can change this part)
        spacer_label = QLabel(" ", self)
        layout.addWidget(spacer_label)  # Add a space before the version

        # Version label
        version_label = QLabel(f"App Version: {version+'.'+ secret_key[12:]}", self)
        version_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(version_label)

        # Add a comment about version usage (in a separate label for clarity)
        version_comment_label = QLabel("Please make sure to use the correct version.", self)
        version_comment_label.setAlignment(Qt.AlignCenter)
        version_comment_label.setStyleSheet("color: red; font-style: italic;")
        layout.addWidget(version_comment_label)

        # Student ID input field
        self.student_id_input = QLineEdit(self)
        self.student_id_input.setPlaceholderText("Enter your 9-digit Student ID")
        self.student_id_input.setMaxLength(9)
        self.student_id_input.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.student_id_input)

        self.warning_label = QLabel("Invalid ID. The Student ID must be exactly 9 digits.", self)
        self.warning_label.setStyleSheet("color: red;")
        self.warning_label.setAlignment(Qt.AlignCenter)
        self.warning_label.hide()
        layout.addWidget(self.warning_label)

        start_exam_button = QPushButton('Start Exam', self)
        start_exam_button.clicked.connect(self.start_exam)
        layout.addWidget(start_exam_button)

        self.exam_setup_screen.setLayout(layout)
        self.stacked_widget.addWidget(self.exam_setup_screen)

    def create_exam_screen(self):
        self.exam_screen = QWidget()
        self.exam_layout = QVBoxLayout()

        self.exam_layout.addWidget(self.create_logo())

        self.exam_progress_label = QLabel(f"00:00", self)
        self.exam_progress_label.setAlignment(Qt.AlignCenter)
        self.exam_layout.addWidget(self.exam_progress_label)

        self.upload_button = QPushButton("Upload Exam and Submit", self)
        self.upload_button.clicked.connect(self.upload_exam)
        self.exam_layout.addWidget(self.upload_button)

        self.exam_screen.setLayout(self.exam_layout)
        self.stacked_widget.addWidget(self.exam_screen)

    def start_exam(self):
        student_id = self.student_id_input.text()
        if len(student_id) == 9 and student_id.isdigit():
            enable_proxy()  # Activates proxy when exam starts
            time.sleep(1)  # Simulate a brief delay for proxy setup
            self.warning_label.hide()
            self.start_time = datetime.datetime.now()
            print(f"Exam started at {self.start_time} for Student ID: {student_id}")

            self.stacked_widget.setCurrentWidget(self.exam_screen)

            self.timer = QTimer(self)
            self.timer.timeout.connect(self.update_timer)
            self.timer.start(1000)
            self.exam_progress_label.setStyleSheet("font-size: 40px; font-weight: light;")
            self.conn_check_timer = QTimer(self)
            self.conn_check_timer.timeout.connect(self.check_connection)
            self.conn_check_timer.start(1000)
        else:
            self.warning_label.show()
            self.student_id_input.clear()

    def update_timer(self):
        self.elapsed_time = int((datetime.datetime.now() - self.start_time).total_seconds())

        # Convert elapsed time to minutes and seconds
        minutes = self.elapsed_time // 60
        seconds = self.elapsed_time % 60

        # Format time as MM:SS
        formatted_time = f"{minutes:02}:{seconds:02}"

        # Update the label with the formatted time
        self.exam_progress_label.setText(f"{formatted_time}")
        

    def check_connection(self):
        if conn_check():
            self.invalidate_exam()

    def upload_exam(self):
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Exam File", "", "All Files (*);;PDF Files (*.pdf)", options=options)
        if file_path:
            self.exam_path = file_path
            self.submission_time = datetime.datetime.now()
            print(f"Exam file submitted at {self.submission_time}: {self.exam_path}")

            self.finalize_exam()

    def finalize_exam(self):
        self.timer.stop()
        self.conn_check_timer.stop()

        for i in reversed(range(self.exam_layout.count())):
            widget = self.exam_layout.itemAt(i).widget()
            if widget is not None:
                widget.deleteLater()

        try:
            signature.sign(self.exam_path, os.path.dirname(self.exam_path), self.student_id_input.text(), self.start_time, secret_key)  # Sign the exam submission
        except Exception as e:
            print(f"Error signing the exam: {e}")

        disable_proxy()  # Deactivates proxy after exam submission

        self.show_confirmation_screen()

    def show_confirmation_screen(self):
        self.exam_layout.addWidget(self.create_logo())  # Add the logo
        confirmation_label = QLabel("Your exam has been successfully saved.", self)
        confirmation_label.setAlignment(Qt.AlignCenter)
        confirmation_label.setStyleSheet("font-size: 16px; font-weight: bold; color: green;")
        self.exam_layout.addWidget(confirmation_label)

    def invalidate_exam(self):
        """Terminates the exam and displays an invalidation message"""
        self.timer.stop()
        self.conn_check_timer.stop()

        for i in reversed(range(self.exam_layout.count())):
            widget = self.exam_layout.itemAt(i).widget()
            if widget is not None:
                widget.deleteLater()

        self.exam_layout.addWidget(self.create_logo())  # Add the logo
        invalidated_text = r'''Your exam has been invalidated. 
        Please contact the Professor for assistance.'''
        invalid_label = QLabel(invalidated_text, self)
        invalid_label.setAlignment(Qt.AlignCenter)
        invalid_label.setStyleSheet("font-size: 18px; font-weight: bold; color: red;")
        self.exam_layout.addWidget(invalid_label)


def conn_check(url="https://www.google.com", timeout=5):
    try:
        requests.get(url, timeout=timeout)
        print("Internet connection detected. Exam invalidated.")
        return True  # Internet detected, exam invalidated 
    except requests.RequestException:
        print("No internet connection detected. Proceeding with the exam.")
        return False  # No internet connection, safe to continue


def enable_proxy():
    if platform.system() == "Darwin":
        for interface in ["Wi-Fi", "Ethernet"]:
            os.system(f'networksetup -setwebproxy "{interface}" 127.0.0.1 9999')
            os.system(f'networksetup -setsecurewebproxy "{interface}" 127.0.0.1 9999')
    elif platform.system() == "Windows":
        os.system('reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Internet Settings" /v ProxyEnable /t REG_DWORD /d 1 /f')
        os.system('reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Internet Settings" /v ProxyServer /t REG_SZ /d "127.0.0.1:9999" /f')


def disable_proxy():
    if platform.system() == "Darwin":
        for interface in ["Wi-Fi", "Ethernet"]:
            os.system(f'networksetup -setwebproxystate "{interface}" off')
            os.system(f'networksetup -setsecurewebproxystate "{interface}" off')
    elif platform.system() == "Windows":
        os.system('reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Internet Settings" /v ProxyEnable /t REG_DWORD /d 0 /f')


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MyApp()
    window.show()
    sys.exit(app.exec_())