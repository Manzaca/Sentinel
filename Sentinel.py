import sys
import datetime
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QLabel, QLineEdit, QStackedWidget, QFileDialog, QMessageBox
from PyQt5.QtGui import QPixmap, QPalette, QColor
import requests
import platform
import os
import time
import dep_signing as signature

#            |                |
secret_key = '0000000000000000'  # Secret key for signing
version = '1.1'  # Version of the program



def apply_dark_theme(app):
    dark_palette = QPalette()
    dark_palette.setColor(QPalette.Window, QColor(45, 45, 45))
    dark_palette.setColor(QPalette.WindowText, QColor(220, 220, 220))
    dark_palette.setColor(QPalette.Base, QColor(35, 35, 35))
    dark_palette.setColor(QPalette.AlternateBase, QColor(45, 45, 45))
    dark_palette.setColor(QPalette.ToolTipBase, QColor(45, 45, 45))
    dark_palette.setColor(QPalette.ToolTipText, QColor(220, 220, 220))
    dark_palette.setColor(QPalette.Text, QColor(220, 220, 220))
    dark_palette.setColor(QPalette.Button, QColor(50, 50, 50))
    dark_palette.setColor(QPalette.ButtonText, QColor(220, 220, 220))
    dark_palette.setColor(QPalette.BrightText, QColor(255, 0, 0))
    dark_palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
    dark_palette.setColor(QPalette.HighlightedText, QColor(0, 0, 0))

    app.setPalette(dark_palette)

def apply_light_theme(app):
    light_palette = QPalette()
    light_palette.setColor(QPalette.Window, QColor(255, 255, 255))  # White background
    light_palette.setColor(QPalette.WindowText, QColor(0, 0, 0))  # Black text
    light_palette.setColor(QPalette.Base, QColor(255, 255, 255))  # White background for text inputs
    light_palette.setColor(QPalette.AlternateBase, QColor(240, 240, 240))  # Lighter background for alternating items
    light_palette.setColor(QPalette.ToolTipBase, QColor(255, 255, 220))  # Light yellow tooltips
    light_palette.setColor(QPalette.ToolTipText, QColor(0, 0, 0))  # Black text in tooltips
    light_palette.setColor(QPalette.Text, QColor(0, 0, 0))  # Black text
    light_palette.setColor(QPalette.Button, QColor(240, 240, 240))  # Light gray button
    light_palette.setColor(QPalette.ButtonText, QColor(0, 0, 0))  # Black text on buttons
    light_palette.setColor(QPalette.BrightText, QColor(255, 0, 0))  # Red text for warnings
    light_palette.setColor(QPalette.Highlight, QColor(42, 130, 218))  # Highlight color (blue)
    light_palette.setColor(QPalette.HighlightedText, QColor(255, 255, 255))  # White text on highlighted items

    app.setPalette(light_palette)

# Function to get the path to the resource files

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


class ConnectionWorker(QThread):
    connection_checked = pyqtSignal(bool)  # Signal to send the connection status

    def run(self):
        result = conn_check()  # Run the connection check
        self.connection_checked.emit(result)  # Emit result

class MyApp(QWidget):
    def __init__(self):
        super().__init__()

        self.start_time = None  # Stores exam start time
        self.submission_time = None  # Stores submission time
        self.exam_path = None  # Stores selected file path
        self.elapsed_time = 0  # Stores the elapsed time in seconds
        self.running = True

        self.initUI()
    
    def closeEvent(self, event):
        apply_light_theme(app)
        reply = QMessageBox.question(self, "Confirm Exit", "Are you sure you want to close?\n\nYour Exam will be terminated.", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            disable_proxy()
            event.accept()
        else:
            apply_dark_theme(app)
            event.ignore()

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

    def start_connection_check(self):
        self.conn_thread = ConnectionWorker()
        self.conn_thread.connection_checked.connect(self.handle_connection_result)
        self.conn_thread.start()
    
    def handle_connection_result(self, status):
        if status and self.running:
            self.invalidate_exam()

    def create_logo(self):
        try:
            logo_label = QLabel(self)
            logo_label.setPixmap(QPixmap(resource_path('logo_long.png')).scaled(457, 100))
            logo_label.setAlignment(Qt.AlignCenter)
            return logo_label
        except Exception as e:
            print(f"Error in the image: {e}")

    def create_intro_screen(self):
        self.intro_screen = QWidget()
        layout = QVBoxLayout()

        # Track logo clicks
        self.logo_click_count = 0  

        logo = self.create_logo()
        logo.mousePressEvent = self.logo_clicked  # Connect logo click
        layout.addWidget(logo)

        intro_text = '''Welcome to Sentinel

    This program has been designed to ensure a secure and distraction-free environment during your exam.

    The device will have no internet access during the exam, and any attempt to connect to the internet will immediately terminate the program and invalidate your exam credentials.'''
        
        text_label = QLabel(intro_text, self)
        text_label.setWordWrap(True)
        text_label.setAlignment(Qt.AlignLeft)
        layout.addWidget(text_label)

        proceed_button = QPushButton('Proceed to Exam Setup', self)
        if platform.system() == 'Windows':
            proceed_button.setStyleSheet("color: black")
        proceed_button.clicked.connect(lambda: self.stacked_widget.setCurrentWidget(self.exam_setup_screen))
        layout.addWidget(proceed_button)

        self.intro_screen.setLayout(layout)
        self.stacked_widget.addWidget(self.intro_screen)

    def logo_clicked(self, event):
        """Handle logo clicks and display only the logo and a message after 5 clicks."""
        self.logo_click_count += 1
        if self.logo_click_count >= 5:
            self.logo_click_count = 0  # Reset counter
            self.gotcha()  # Call gotcha function

    def gotcha(self):
        """Clear the intro screen and display only the logo with a message."""
        for i in reversed(range(self.intro_screen.layout().count())):
            widget = self.intro_screen.layout().itemAt(i).widget()
            if widget:
                widget.deleteLater()  # Remove all widgets

        # Add only the logo and a message
        logo = self.create_logo()
        self.intro_screen.layout().addWidget(logo)

        message = QLabel('Software created by A. Manzaca\nAll Rights Reserved 2025\n\nCopy it and I will install a virus on your goddam computer\nGot it?\n\nCheers!', self)
        message.setAlignment(Qt.AlignCenter)
        self.intro_screen.layout().addWidget(message)

    def create_exam_setup_screen(self):
        self.exam_setup_screen = QWidget()
        layout = QVBoxLayout()

        layout.addWidget(self.create_logo())

        # Exam length label
        exam_label = QLabel(f'\nOnce the exam starts your connection will be disabled.\nDo not forget to submit your exam before the end of the exam time.\n\nIf you close this app, your professor will be notified.\n\n Good luck!', self)
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
        if platform.system() == 'Windows':
            self.student_id_input.setStyleSheet("color: black")
        layout.addWidget(self.student_id_input)

        # Create a dummy button to shift focus
        dummy_button = QPushButton("", self)
        dummy_button.setVisible(False)  # Hide the button
        layout.addWidget(dummy_button)

        # After setting up UI, move focus away from the input field
        QTimer.singleShot(100, dummy_button.setFocus)

        
        self.warning_label = QLabel("Invalid ID. The Student ID must be exactly 9 digits.", self)
        self.warning_label.setStyleSheet("color: red;")
        self.warning_label.setAlignment(Qt.AlignCenter)
        self.warning_label.hide()
        layout.addWidget(self.warning_label)

        start_exam_button = QPushButton('Start Exam', self)
        
        if platform.system() == 'Windows':
            start_exam_button.setStyleSheet("color: black")
        start_exam_button.clicked.connect(self.start_exam)
        layout.addWidget(start_exam_button)

        self.exam_setup_screen.setLayout(layout)
        self.stacked_widget.addWidget(self.exam_setup_screen)



    def create_exam_screen(self):
        self.exam_screen = QWidget()
        self.exam_layout = QVBoxLayout()
        self.logo = self.create_logo()  # Create the logo widget
        self.exam_layout.addWidget(self.logo)

        self.exam_progress_label = QLabel(f"00:00", self)
        self.exam_progress_label.setAlignment(Qt.AlignCenter)
        self.exam_layout.addWidget(self.exam_progress_label)

        self.upload_button = QPushButton('Submit', self)
        self.upload_button.clicked.connect(self.submit_exam)
        if platform.system() == 'Windows':
            self.upload_button.setStyleSheet("color: black")
        self.exam_layout.addWidget(self.upload_button)

        self.exam_screen.setLayout(self.exam_layout)
        self.stacked_widget.addWidget(self.exam_screen)

    def submit_exam(self):
        # Open file dialog to select a file (ensure it's not blocking)
        self.exam_path, _ = QFileDialog.getOpenFileName(self, "Select Exam File", "", "All Files (*);;Text Files (*.txt)")

        apply_light_theme(app)

        if self.exam_path:  # If a file is selected
            # Extract the file name from the full path
            file_name = os.path.basename(self.exam_path)

            
            # Show confirmation dialog with the file name only
            reply = QMessageBox.question(self, 'Confirm Exam Submission', 
                                        f"You selected the file: {file_name}\n\n Do you wish to continue and end your exam?", 
                                        QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

            if reply == QMessageBox.Yes:
                # Proceed with the exam submission
                apply_dark_theme(app)
                self.finalize_exam()  # Call the function to end the exam and proceed
            else:
                # Reset, allow the user to select the file again
                print("Exam submission canceled, please select the file again.")
                apply_dark_theme(app)
                return
            
        else:
            
            print("No file selected.")
            apply_dark_theme(app)

        


    def start_exam(self):
        self.setMinimumSize(520, 400)
        self.resize(520, 400)  # You can adjust the size here as needed
        
        student_id = self.student_id_input.text()
        if len(student_id) == 9 and student_id.isdigit():
            enable_proxy()  # Activates proxy when exam starts
            self.warning_label.hide()
            self.start_time = datetime.datetime.now()
            print(f"Exam started at {self.start_time} for Student ID: {student_id}")

            self.stacked_widget.setCurrentWidget(self.exam_screen)

            # Create the toggle button if it doesn't exist
            if not hasattr(self, 'toggle_on_top_button'):
                self.toggle_on_top_button = QPushButton("Toggle Always on Top", self)
                self.toggle_on_top_button.clicked.connect(self.toggle_always_on_top)
                if platform.system() == 'Windows':
                    self.toggle_on_top_button.setStyleSheet("color: black")
                self.layout().addWidget(self.toggle_on_top_button)

                self.timer = QTimer(self)
                self.timer.timeout.connect(self.update_timer)
                self.timer.start(1000)
                self.exam_progress_label.setStyleSheet("font-size: 40px; font-weight: light;")
                self.conn_check_timer = QTimer(self)
                self.conn_check_timer.timeout.connect(self.start_connection_check)
                self.conn_check_timer.start(1000)
            else:
                self.warning_label.show()
                self.student_id_input.clear()

    def toggle_always_on_top(self):
        if self.windowFlags() & Qt.WindowStaysOnTopHint:
            # If the window is already always on top, remove the flag and show the logo
            self.setWindowFlags(self.windowFlags() & ~Qt.WindowStaysOnTopHint)  # Remove "always on top" flag
            self.logo.show()  # Show the logo again
            self.upload_button.show()  # Show the submit button again
            
            # Resize the window back to its original size
            self.setMinimumSize(520, 400)
            self.resize(520, 400)  # You can adjust the size here as needed
        else:
            # If the window is not always on top, add the flag and hide the logo
            self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)  # Enable "always on top"
            self.logo.hide()  # Hide the logo in always on top mode
            self.upload_button.hide()  # Hide the submit button in always on top mode
            
            # Resize the window for the always-on-top mode
            self.setMinimumSize(200, 135)  # Disable any minimum size constraints
            self.resize(200, 135)  # You can adjust the size here as needed
        
        self.show()  # Re-apply window flags and size


    def update_timer(self):
        self.elapsed_time = int((datetime.datetime.now() - self.start_time).total_seconds())

        # Convert elapsed time to minutes and seconds
        minutes = self.elapsed_time // 60
        seconds = self.elapsed_time % 60

        # Format time as MM:SS
        formatted_time = f"{minutes:02}:{seconds:02}"

        # Update the label with the formatted time
        self.exam_progress_label.setText(f"{formatted_time}")
        

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

        self.running = False
        self.show_confirmation_screen()

    def show_confirmation_screen(self):

        self.exam_layout.addWidget(self.create_logo())  # Add the logo
        confirmation_label = QLabel("Your exam has been successfully saved.\nYou may close this window.", self)
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
        invalidated_text = 'Your exam has been invalidated.\nPlease contact the Professor for assistance.'
        invalid_label = QLabel(invalidated_text, self)
        invalid_label.setAlignment(Qt.AlignCenter)
        invalid_label.setStyleSheet("font-size: 18px; font-weight: bold; color: red;")
        self.exam_layout.addWidget(invalid_label)


def conn_check(url="https://www.google.com", timeout=5):
    
    time.sleep(timeout+1)
    try:
        requests.get(url, timeout=timeout)
        print("Internet connection detected. Exam invalidated.")
        return True  # Internet detected, exam invalidated 
    except requests.RequestException:
        print("No internet connection detected. Proceeding with the exam.")
        return False  # No internet connection, safe to continue
    else:
        return False


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
    apply_dark_theme(app)

    window = MyApp()
    window.show()
    sys.exit(app.exec_())
