import sys
import os
from PyQt5.QtCore import Qt, QDateTime, QThread, pyqtSignal
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QPushButton, 
    QDateTimeEdit, QSpinBox, QFileDialog, QProgressBar)
from PyQt5.QtGui import QPixmap, QPalette, QColor
import dep_signing as signature
from datetime import datetime
import shutil
import subprocess
import time
import platform

secret_key = '0000000000000000'
version = '1.0'




def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)



file_set = []
exam_length = 0
selected_date = ""
selected_directory = ""

 
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


def open_folder(folder_path):
    if os.name == 'nt':  # Windows
        subprocess.run(['explorer', folder_path])
    elif os.name == 'posix':  # macOS or Linux
        subprocess.run(['open', folder_path])


def save_text_file(directory, filename, content):
    # Ensure the directory exists
    os.makedirs(directory, exist_ok=True)
    
    # Create the full path for the file
    file_path = os.path.join(directory, filename)
    
    # Open the file and write the content
    with open(file_path, 'w') as file:
        file.write(content)

def time_dif(reference_time, check_time):
    
    return (check_time - reference_time).total_seconds() / 60

class ProcessingThread(QThread):
    progress = pyqtSignal(int)

    def __init__(self, files, selected_directory):
        super().__init__()
        self.files = files
        self.selected_directory = selected_directory

    def run(self):
        total_files = len(self.files)
        for i, file in enumerate(self.files, start=1):
            metadata,filepath = signature.unsign(file, self.selected_directory,secret_key)  # Pass both file path and selected directory
            
            actual_exam_length = (metadata['end_time'] - metadata['start_time']).total_seconds() / 60
            print(metadata['start_time'])

            logo_ascii = f'''
         ======                                                                                              
     ==============                                                                                          
   ===++++++++++++===                                                                                        
  =====%@@@@@@@@@=====      @@@@@@@@                                                                         
 =======*%%%%%%%======    @@@@         @@@@@@@@  @@@@   @@@  @@@@@@@@  @@@   @@@   @@@   @@@@@@@@  @@@       
 ========*@@@@%========    @@@@@@@@@   @@@       @@@@@@ @@@    @@@     @@@   @@@@@  @@   @@@       @@@       
 @@@@@@@+=+@@%==%@@@@@@          @@@@  @@@@@@    @@@ @@@@@@    @@@     @@@   @@ @@@@@@   @@@@@@    @@@       
  @@@@@@@*=+#=+@@@@@@@     @@@@@@@@@   @@@@@@@@  @@@   @@@@    @@@     @@@   @@   @@@@   @@@@@@@@  @@@@@@@@  
  @@@@@@@@#==+@@@@@@@@                                                                                      
    @@@@@@@#+@@@@@@@                                                                                         
      @@@@@@@@@@@@


      
'''
            if metadata['integrity']:
                if actual_exam_length < exam_length:
                    print(selected_date)
                    time_delta = time_dif(selected_date,metadata['start_time'])
                    if  abs(time_delta) < 5: # 5 minutes tolerance
                        print('Test is fully valid')

                        new_folder = os.path.join(os.path.dirname(filepath), "validated")
                        os.makedirs(new_folder, exist_ok=True)
                        new_path = os.path.join(new_folder, metadata['user_id'] + os.path.splitext(filepath)[1])
                        shutil.move(filepath, new_path)
                        save_text_file(new_folder,metadata['user_id'] + ".txt",logo_ascii + f"User ID: {metadata['user_id']}\nStart Time: {metadata['start_time']}\nEnd Time: {metadata['end_time']}\nIntegrity: {metadata['integrity']}\n")

                    else:
                        print('Test is invalid - start time is not within the tolerance')
                        new_folder = os.path.join(os.path.dirname(filepath), "invalidated")
                        os.makedirs(new_folder, exist_ok=True)
                        new_path = os.path.join(new_folder, metadata['user_id'] + os.path.splitext(filepath)[1])
                        shutil.move(filepath, new_path)
                        save_text_file(new_folder,metadata['user_id'] + ".txt",logo_ascii + f"User ID: {metadata['user_id']}\nStart Time: {metadata['start_time']}\nEnd Time: {metadata['end_time']}\nIntegrity: {metadata['integrity']}\n")
                else:
                    print('Test is invalid - exam lengh exceeded')
                    new_folder = os.path.join(os.path.dirname(filepath), "invalidated")
                    os.makedirs(new_folder, exist_ok=True)
                    new_path = os.path.join(new_folder, metadata['user_id'] + os.path.splitext(filepath)[1])
                    shutil.move(filepath, new_path)
                    save_text_file(new_folder,metadata['user_id'] + ".txt",logo_ascii + f"User ID: {metadata['user_id']}\nStart Time: {metadata['start_time']}\nEnd Time: {metadata['end_time']}\nIntegrity: {metadata['integrity']}\n")
            else:
                print('Test is invalid - integrity check failed')
                new_folder = os.path.join(os.path.dirname(filepath), "invalidated")
                os.makedirs(new_folder, exist_ok=True)
                new_path = os.path.join(new_folder, metadata['user_id'] + os.path.splitext(filepath)[1])
                shutil.move(filepath, new_path)
                save_text_file(new_folder,metadata['user_id'] + ".txt",logo_ascii + f"User ID: {metadata['user_id']}\nStart Time: {metadata['start_time']}\nEnd Time: {metadata['end_time']}\nIntegrity: {metadata['integrity']}\n")
            self.progress.emit(int((i / total_files) * 100))  # Update progress bar



class ExamSetupApp(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI() 

    def initUI(self):
        self.setWindowTitle(f'Sentinel Review - V{version+'.'+ secret_key[12:]}')
        self.setGeometry(100, 100, 400, 300)

        self.layout = QVBoxLayout()

        # Logo
        self.logo_label = QLabel(self)
        self.logo_label.setPixmap(QPixmap(resource_path('logo_long.png')).scaled(350, 80, Qt.KeepAspectRatio))
        self.logo_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.logo_label)

        # Track logo clicks
        self.logo_click_count = 0  

        self.logo_label.mousePressEvent = self.logo_clicked  # Connect logo click

        # Date and time selector
        self.datetime_label = QLabel("Select Exam Start Time:", self)
        self.layout.addWidget(self.datetime_label)

        self.datetime_picker = QDateTimeEdit(self)
        self.datetime_picker.setDisplayFormat("yyyy-MM-dd HH:mm")
        self.datetime_picker.setCalendarPopup(True)
        self.datetime_picker.setDateTime(QDateTime(2025, 1, 1, 12, 0))  # Default: Jan 1, 2025, at 01:00
        if platform.system() == 'Windows':
            self.datetime_picker.setStyleSheet("color: black")
        self.layout.addWidget(self.datetime_picker)

        # Maximum exam length input
        self.exam_length_label = QLabel("Enter Maximum Exam Length (minutes):", self)
        self.layout.addWidget(self.exam_length_label)

        self.exam_length_input = QSpinBox(self)
        self.exam_length_input.setRange(1, 600)  # Limit to reasonable exam durations
        self.exam_length_input.setSuffix(" min")
        self.exam_length_input.setValue(60)  # Default to 60 minutes
        if platform.system() == 'Windows':
            self.exam_length_input.setStyleSheet("color: black")
        self.layout.addWidget(self.exam_length_input)

        # Submit button
        self.submit_button = QPushButton("Select Exams Folder", self)
        self.submit_button.clicked.connect(self.select_folder)
        if platform.system() == 'Windows':
            self.submit_button.setStyleSheet("color: black")
        self.layout.addWidget(self.submit_button)

        # Progress bar (initially hidden)
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        self.layout.addWidget(self.progress_bar)

        self.setLayout(self.layout)
    
    def logo_clicked(self, event):
        """Handle logo clicks and display only the logo and a message after 5 clicks."""
        self.logo_click_count += 1
        if self.logo_click_count >= 5:
            self.logo_click_count = 0  # Reset counter
            self.gotcha()  # Call gotcha function

    def gotcha(self):
        """Clear the current layout and display only the logo with a message."""
        # Remove all widgets from the layout
        while self.layout.count():
            widget = self.layout.takeAt(0).widget()
            if widget:
                widget.deleteLater()

        # Add only the logo and a message
        self.logo_label = QLabel(self)
        self.logo_label.setPixmap(QPixmap(resource_path('logo_long.png')).scaled(350, 80, Qt.KeepAspectRatio))
        self.logo_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.logo_label)

        message = QLabel(
            'Software created by A. Manzaca\nAll Rights Reserved 2025\n\n'
            'Copy it and I will install a virus on your goddamn computer\n'
            'Got it?\n\nCheers!',
            self
        )
        message.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(message)

    def select_folder(self):
        global selected_date, exam_length, folder_path

        folder_path = QFileDialog.getExistingDirectory(self, "Select Exam Folder")
        if folder_path:
            selected_date = self.datetime_picker.dateTime().toString("yyyy-MM-dd HH:mm")
            selected_date = datetime.strptime(selected_date, "%Y-%m-%d %H:%M")
            exam_length = self.exam_length_input.value()

            print(f"Selected Date and Time: {selected_date}")
            print(f"Selected Exam Length: {exam_length} minutes")
            print(f"Selected Folder Path: {folder_path}")

            # Get all .sntl files
            sntl_files = [os.path.join(folder_path, f) for f in os.listdir(folder_path) if f.endswith(".sntl")]
            
            print(f"Found {len(sntl_files)} .sntl files")

            if sntl_files:
                self.start_processing(sntl_files, folder_path)
            else:
                print("No .sntl files found.")

    def start_processing(self, files, selected_directory):
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)

        self.thread = ProcessingThread(files, selected_directory)
        self.thread.progress.connect(self.progress_bar.setValue)
        self.thread.start()
        self.thread.finished.connect(self.processing_complete)

    def processing_complete(self):
        print("Processing complete!")
        self.clear_screen()

    def clear_screen(self):
        open_folder(folder_path)
        for i in reversed(range(self.layout.count())):
            widget = self.layout.itemAt(i).widget()
            if widget and widget != self.logo_label:
                widget.deleteLater()
        


if __name__ == '__main__':
    app = QApplication(sys.argv)
    apply_dark_theme(app)
    window = ExamSetupApp()
    window.show()
    sys.exit(app.exec_())
