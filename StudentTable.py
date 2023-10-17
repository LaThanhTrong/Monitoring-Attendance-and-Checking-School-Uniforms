import os
import re
import shutil
import sqlite3
import zipfile
from PyQt5 import uic
from PyQt5.QtWidgets import QMainWindow, QTableWidgetItem, QMessageBox, QFileDialog
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import pyqtSignal, Qt

class StudentTable(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi("Students.ui", self)

        self.fetch_student_data()
        self.btn_search.clicked.connect(lambda: self.fetch_student_data(self.input_search.text()))
        self.btn_openFile.clicked.connect(self.open_file)
        self.btn_check.clicked.connect(self.validate)
        self.btn_save.setEnabled(False)
        self.btn_delete.clicked.connect(self.deleteStudent)
        self.btn_save.clicked.connect(self.save)
        self.isFile = False
        self.update = False

        # Connect textChanged signals to methods
        self.input_id.textChanged.connect(self.changed)
        self.input_name.textChanged.connect(self.changed)
        self.cbb_gender.currentTextChanged.connect(self.changed)
        self.input_major.textChanged.connect(self.changed)
        self.input_email.textChanged.connect(self.changed)
        self.label.textChanged.connect(self.filechanged)

        self.setWindowIcon(QIcon("icon.png"))

    def changed(self):
        self.btn_save.setEnabled(False)
        self.update = False
    
    def filechanged(self):
        self.btn_save.setEnabled(False)
        if self.label.text():
            self.isFile = True
        else:
            self.isFile = False

    def open_file(self):
        options = QFileDialog.Options()
        options |= QFileDialog.ReadOnly
        f = QFileDialog.getOpenFileName(self, 'Open zip file', './', "Zip Files (*.zip)", options=options)
        if f[0]:
            self.label.setText(f[0])
            self.isFile = True

    def fetch_student_data(self, search=None):
        # Create a database
        conn = sqlite3.connect('database.db')

        # Create a cursor
        cursor = conn.cursor()

        # Execute the sql statement
        if(search is None):
            cursor.execute("SELECT * FROM students")
        else:
            search = "%" + search + "%"
            cursor.execute("SELECT * FROM students WHERE student_id LIKE ?",(search,))

        # Fetch all the rows
        rows = cursor.fetchall()

        # Close the connection
        conn.close()

        self.students_data = []
        self.table.clearContents()
        self.table.setRowCount(0)
        for row in rows:
            student = {
                "student_id": row[0],
                "student_name": row[1],
                "student_gender": row[2],
                "student_major": row[3],
                "student_email": row[4]
            }
            self.students_data.append(student)
        
        for row, student in enumerate(self.students_data):
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(student["student_id"]))
            self.table.setItem(row, 1, QTableWidgetItem(student["student_name"]))
            self.table.setItem(row, 2, QTableWidgetItem(student["student_gender"]))
            self.table.setItem(row, 3, QTableWidgetItem(student["student_major"]))
            self.table.setItem(row, 4, QTableWidgetItem(student["student_email"]))
            # Set item flags to make cells not editable
            for col in range(5):
                item = self.table.item(row, col)
                if item:
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)

         # Apply padding to the table cells
        self.table.setStyleSheet("QTableWidget::item { padding: 5px; }")

    def save(self):
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        if(self.update):
            try:
                conn = sqlite3.connect('database.db')
                cursor = conn.cursor()
                sql = """
                    UPDATE students
                    SET student_name = ?,
                        student_gender = ?,
                        student_major = ?,
                        student_email = ?
                    WHERE student_id = ?
                """
                data = (self.input_name.text(), self.cbb_gender.currentText(), self.input_major.text(), self.input_email.text(), self.input_id.text().upper())
                cursor.execute(sql, data)
                conn.commit()
                conn.close()
                if not self.isFile:
                    QMessageBox.information(self, "Success", f"Student {self.input_id.text().upper()} has been updated.", QMessageBox.Ok)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"An error occurred.\nError:{e}", QMessageBox.Ok)

            if(self.isFile):
                try:
                    directory_path = './datafaces'  # Specify the path to the directory containing .pkl files
                    for filename in os.listdir(directory_path):
                        if filename.endswith('.pkl'):
                            file_path = os.path.join(directory_path, filename)
                            os.remove(file_path)
                    extract_folder = f'./datafaces/{self.input_id.text().upper()}'
                    shutil.rmtree(extract_folder)
                    zip_file_path = self.label.text()
                    # Source and destination file paths
                    os.makedirs(extract_folder, exist_ok=True)
                    self.extract_images_from_zip(zip_file_path, extract_folder)
                    # Remove the extracted ZIP file
                    extracted_zip_path = os.path.join(extract_folder, os.path.basename(zip_file_path))
                    if os.path.exists(extracted_zip_path):
                        os.remove(extracted_zip_path)
                    QMessageBox.information(self, "Success", f"Student {self.input_id.text().upper()} has been updated.", QMessageBox.Ok)
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"An error occurred.\nError:{e}", QMessageBox.Ok)

        else:
            try:
                conn = sqlite3.connect('database.db')
                cursor = conn.cursor()
                query = "INSERT INTO students VALUES (?,?,?,?,?)"
                data = (self.input_id.text().upper(), self.input_name.text(), self.cbb_gender.currentText(), self.input_major.text(), self.input_email.text())
                cursor.execute(query, data)
                conn.commit()
                conn.close()

                directory_path = './datafaces'  # Specify the path to the directory containing .pkl files
                for filename in os.listdir(directory_path):
                    if filename.endswith('.pkl'):
                        file_path = os.path.join(directory_path, filename)
                        os.remove(file_path)

                extract_folder = f'./datafaces/{self.input_id.text().upper()}'
                zip_file_path = self.label.text()
                # Source and destination file paths
                os.makedirs(extract_folder, exist_ok=True)
                self.extract_images_from_zip(zip_file_path, extract_folder)
                # Remove the extracted ZIP file
                extracted_zip_path = os.path.join(extract_folder, os.path.basename(zip_file_path))
                if os.path.exists(extracted_zip_path):
                    os.remove(extracted_zip_path)
                QMessageBox.information(self, "Success", "The student data has been saved.", QMessageBox.Ok)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"An error occurred.\nError:{e}", QMessageBox.Ok)

        self.change_signal.emit()
        self.input_search.clear()
        self.input_id.clear()
        self.input_name.clear()
        self.input_major.clear()
        self.input_email.clear()
        self.label.clear()
        self.btn_save.setEnabled(False)
        self.isFile = False
        self.update = False
        self.fetch_student_data()
    
    def deleteStudent(self):
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute("SELECT student_id FROM students")
        student_ids = [row[0] for row in cursor.fetchall()]
        conn.close()
        if(self.input_search.text() == ""):
            QMessageBox.critical(self, "Error", "Please enter student ID.", QMessageBox.Ok)
        elif(self.input_search.text().upper() not in student_ids):
            QMessageBox.critical(self, "Error", "Student ID does not exist.", QMessageBox.Ok)
        else:
            if(QMessageBox.question(self, "Delete Student", f"Are you sure you want to delete {self.input_search.text().upper()}?", QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes):
                try:
                    conn = sqlite3.connect('database.db')
                    cursor = conn.cursor()
                    # Get the enroll_id values associated with the student to be deleted
                    cursor.execute("SELECT enroll_id FROM CourseEnroll WHERE student_id = ?", (self.input_search.text().upper(),))
                    enroll_ids = cursor.fetchall()
                    for enroll_id in enroll_ids:
                        cursor.execute("DELETE FROM schedule WHERE enroll_id = ?", (enroll_id[0],))
                     # Delete student's enrollment records
                    cursor.execute("DELETE FROM CourseEnroll WHERE student_id = ?", (self.input_search.text().upper(),))
                    # Delete the student record
                    cursor.execute("DELETE FROM students WHERE student_id = ?", (self.input_search.text().upper(),))
                    conn.commit()
                    shutil.rmtree(f'./datafaces/{self.input_search.text().upper()}')
                    directory_path = './datafaces'  # Specify the path to the directory containing .pkl files
                    for filename in os.listdir(directory_path):
                        if filename.endswith('.pkl'):
                            file_path = os.path.join(directory_path, filename)
                            os.remove(file_path)
                    conn.close()
                    QMessageBox.information(self, "Success", f"Student {self.input_search.text().upper()} has been deleted.", QMessageBox.Ok)
                except Exception as e:
                    conn.rollback()
                    conn.close()
                    QMessageBox.critical(self, "Error", f"An error occurred.\nError:{e}", QMessageBox.Ok)
                
                self.change_signal.emit()
        
        self.input_search.clear()
        self.fetch_student_data()
    
    change_signal = pyqtSignal()
    
    def extract_images_from_zip(self, zip_file_path, extract_folder):
        with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
            image_files = [name for name in zip_ref.namelist() if name.lower().endswith(('.png', '.jpg', '.jpeg'))]
            zip_ref.extractall(extract_folder, members=image_files)
    
    def closeEvent(self, event):
        # Clear input fields when the window is closed
        self.input_search.clear()
        self.input_id.clear()
        self.input_name.clear()
        self.input_major.clear()
        self.input_email.clear()
        self.label.clear()
        self.btn_save.setEnabled(False)
        self.isFile = False
        self.update = False
        self.fetch_student_data()
        super().closeEvent(event)

    def validate(self):
        isValid = False
        try:
            conn = sqlite3.connect('database.db')
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM students WHERE student_id = ?", (self.input_id.text().upper(),))
            rows = cursor.fetchall()
            conn.close()
            if(rows):
                self.update = True
            else:
                self.update = False
        except Exception as e:
                QMessageBox.critical(self, "Error", f"An error occurred.\nError:{e}", QMessageBox.Ok)
        
        if len(self.input_id.text().upper()) == 0 or len(self.input_name.text()) == 0 or len(self.input_major.text()) == 0 or len(self.input_email.text()) == 0:
            QMessageBox.warning(self, "Empty Field", "Please fill in all the fields.", QMessageBox.Ok)
        elif not re.match(r"[^@]+@[^@]+\.[^@]+", self.input_email.text()):
            QMessageBox.warning(self, "Invalid Email", "Please enter a valid email.", QMessageBox.Ok)
        else:
            if self.update and not self.isFile:
                QMessageBox.information(self, "Validate", "The validation is success.", QMessageBox.Ok)
                isValid = True
            elif not self.update and not self.isFile:
                isValid = False
                QMessageBox.warning(self, "No File Selected", "Please select a zip file.", QMessageBox.Ok)
            else:
                self.isFile = True
                try:
                    allowed_extensions = ['.png', '.jpg', '.jpeg']
                    # Open the zip file in read mode
                    with zipfile.ZipFile(self.label.text(), 'r') as zip_ref:
                        # Get a list of all files in the zip archive
                        zip_contents = zip_ref.namelist()

                        # Check if all files have allowed extensions
                        for file_name in zip_contents:
                            _, file_extension = os.path.splitext(file_name)
                            if file_extension.lower() not in allowed_extensions:
                                isValid = False
                                QMessageBox.critical(self, "Invalid File Extension", f"Invalid file extension found: {file_extension}. Only PNG, JPG, and JPEG files are allowed.", QMessageBox.Ok)
                                break
                        else:
                            isValid = True
                            QMessageBox.information(self, "Validate", "The validation is success.", QMessageBox.Ok)

                except zipfile.BadZipFile:
                    isValid = False
                    QMessageBox.critical(self, "Invalid File", "The provided file is not a valid zip archive.", QMessageBox.Ok)
                except Exception as e:
                    isValid = False
                    QMessageBox.critical(self, "Error", "An error occurred while validating the zip file.", QMessageBox.Ok)

        if(isValid):
            self.btn_save.setEnabled(True)