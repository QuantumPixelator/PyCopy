import sys
import os
import shutil
import threading
from PySide6 import QtWidgets, QtCore, QtGui

class FileCopier(QtCore.QObject):
    progressChanged = QtCore.Signal(int)
    completed = QtCore.Signal()
    errorOccurred = QtCore.Signal(str)

    def __init__(self, source_path, destination_path, overwrite=False, refresh=False, parent=None):
        super().__init__(parent)
        self.source_path = source_path
        self.destination_path = destination_path
        self.overwrite = overwrite
        self.refresh = refresh
        self.total_files = self._count_total_files()
        self.copied_files = 0
        self.thread = threading.Thread(target=self._copy_files_and_dirs)
        self.copied_folders = 0

    def _count_total_files(self):
        total_files = 0
        for _, _, files in os.walk(self.source_path):
            total_files += len(files)
        return total_files

    def _copy_files_and_dirs(self):
        try:
            for root, _, files in os.walk(self.source_path):
                destination_root = os.path.join(self.destination_path, os.path.relpath(root, self.source_path))
                if not os.path.exists(destination_root):
                    os.makedirs(destination_root)
                    self.copied_folders += 1

                for file in files:
                    source_file = os.path.join(root, file)
                    destination_file = os.path.join(destination_root, file)

                    if os.path.exists(destination_file) and not self.overwrite:
                        if self.refresh and os.path.getmtime(source_file) <= os.path.getmtime(destination_file):
                            continue

                    shutil.copy2(source_file, destination_file)
                    self.copied_files += 1
                    self.progressChanged.emit(self.copied_files)

            self.completed.emit()
        except Exception as e:
            self.errorOccurred.emit(str(e))

    def start(self):
        self.thread.start()

    def isRunning(self):
        return self.thread.is_alive()

class CopyWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyCopy")
        self.resize(500, 330)

        self.source_label = QtWidgets.QLabel("Source Path:")
        self.source_input = QtWidgets.QLineEdit()
        self.source_browse = QtWidgets.QPushButton("Browse")
        self.source_browse.clicked.connect(self.browse_source)

        self.destination_label = QtWidgets.QLabel("Destination Path:")
        self.destination_input = QtWidgets.QLineEdit()
        self.destination_browse = QtWidgets.QPushButton("Browse")
        self.destination_browse.clicked.connect(self.browse_destination)

        self.overwrite_checkbox = QtWidgets.QCheckBox("Overwrite existing files")
        self.refresh_checkbox = QtWidgets.QCheckBox("Copy only new/modified files")

        self.start_button = QtWidgets.QPushButton("Start Copying")
        self.start_button.clicked.connect(self.start_copying)

        self.progress_bar = QtWidgets.QProgressBar()
        
        self.info_label = QtWidgets.QLabel("File and folder permissions are copied as well.")
        self.info_label.setObjectName("infoLabel")

        source_layout = QtWidgets.QHBoxLayout()
        source_layout.addWidget(self.source_input)
        source_layout.addWidget(self.source_browse)

        destination_layout = QtWidgets.QHBoxLayout()
        destination_layout.addWidget(self.destination_input)
        destination_layout.addWidget(self.destination_browse)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.source_label)
        layout.addLayout(source_layout)
        layout.addWidget(self.destination_label)
        layout.addLayout(destination_layout)
        layout.addWidget(self.overwrite_checkbox)
        layout.addWidget(self.refresh_checkbox)
        layout.addWidget(self.start_button)
        layout.addWidget(self.progress_bar)
        
        font = QtGui.QFont()
        font.setItalic(True)
        font.setPointSize(7)
        self.info_label.setFont(font)

        layout.addWidget(self.info_label, alignment=QtCore.Qt.AlignCenter)

        container = QtWidgets.QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)
        
        layout.addStretch(1)

        self.apply_styles()

    def apply_styles(self):
        styles = """
            QWidget {
                font-size: 16px;
            }
            
            #infoLabel {
            color: darkgray;
        }

            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 10px 20px;
                text-align: center;
                border-radius: 4px;
            }

            QPushButton:hover {
                background-color: #1976D2;
            }

            QProgressBar {
                border: 2px solid #2196F3;
                border-radius: 5px;
                text-align: center;
            }

            QProgressBar::chunk {
                background-color: #2196F3;
            }
        """
        self.setStyleSheet(styles)

    def start_copying(self):
        source_path = self.source_input.text()
        destination_path = self.destination_input.text()

        overwrite = self.overwrite_checkbox.isChecked()
        refresh = self.refresh_checkbox.isChecked()

        self.file_copier = FileCopier(source_path, destination_path, overwrite, refresh)
        self.file_copier.progressChanged.connect(self.update_progress_bar)
        self.file_copier.completed.connect(self.on_completed)
        self.file_copier.errorOccurred.connect(self.on_error)
        self.file_copier.start()

    def update_progress_bar(self, value):
        percent_complete = (value / self.file_copier.total_files) * 100
        self.progress_bar.setValue(percent_complete)

    def on_completed(self):
        total_files_copied = self.file_copier.copied_files
        total_folders_copied = self.file_copier.copied_folders
    
        message = (f"Copying completed!\n n\Files: {total_files_copied}\nFolders: {total_folders_copied}")
    
        QtWidgets.QMessageBox.information(self, "Completed", message)


    def on_error(self, error_message):
        QtWidgets.QMessageBox.critical(self, "Error", error_message)

    def browse_source(self):
        path = QtWidgets.QFileDialog.getExistingDirectory(self, "Select Source Directory")
        if path:
            self.source_input.setText(path)

    def browse_destination(self):
        path = QtWidgets.QFileDialog.getExistingDirectory(self, "Select Destination Directory")
        if path:
            self.destination_input.setText(path)

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = CopyWindow()
    window.show()
    sys.exit(app.exec())
