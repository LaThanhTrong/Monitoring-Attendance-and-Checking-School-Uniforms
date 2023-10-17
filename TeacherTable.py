import re
import sqlite3
from PyQt5.QtWidgets import QMainWindow, QTableWidgetItem, QMessageBox
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5 import uic

class TeacherTable(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi("Teachers.ui", self)
        self.fetch_teacher_data()
        self.btn_save.setEnabled(False)
        self.btn_search.clicked.connect(lambda: self.fetch_teacher_data(self.input_search.text()))
        self.btn_check.clicked.connect(self.validate)
        self.btn_save.clicked.connect(self.save)
        self.update = False

        # Connect textChanged signals to methods
        self.input_id.textChanged.connect(self.changed)
        self.input_name.textChanged.connect(self.changed)
        self.cbb_gender.currentTextChanged.connect(self.changed)
        self.input_email.textChanged.connect(self.changed)

        self.setWindowIcon(QIcon("icon.png"))

    def changed(self):
        self.btn_save.setEnabled(False)
        self.update = False

    def save(self):
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        if(self.update):
            try:
                conn = sqlite3.connect('database.db')
                cursor = conn.cursor()
                sql = """
                    UPDATE teachers
                    SET teacher_name = ?,
                        teacher_gender = ?,
                        teacher_email = ?
                    WHERE teacher_id = ?
                """
                data = (self.input_name.text(), self.cbb_gender.currentText(), self.input_email.text(), self.input_id.text().upper())
                cursor.execute(sql, data)
                conn.commit()
                conn.close()
                QMessageBox.information(self, "Success", f"Teacher {self.input_id.text().upper()} has been updated.", QMessageBox.Ok)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"An error occurred.\nError:{e}", QMessageBox.Ok)

        else:
            try:
                conn = sqlite3.connect('database.db')
                cursor = conn.cursor()
                query = "INSERT INTO teachers VALUES (?,?,?,?)"
                data = (self.input_id.text().upper(), self.input_name.text(), self.cbb_gender.currentText(), self.input_email.text())
                cursor.execute(query, data)
                conn.commit()
                conn.close()
                QMessageBox.information(self, "Success", "The teacher data has been saved.", QMessageBox.Ok)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"An error occurred.\nError:{e}", QMessageBox.Ok)

        self.change_signal.emit()
        self.input_search.clear()
        self.input_id.clear()
        self.input_name.clear()
        self.input_email.clear()
        self.btn_save.setEnabled(False)
        self.update = False
        self.fetch_teacher_data()

    change_signal = pyqtSignal()
    
    def validate(self):
        isValid = False
        try:
            conn = sqlite3.connect('database.db')
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM teachers WHERE teacher_id = ?", (self.input_id.text().upper(),))
            rows = cursor.fetchall()
            conn.close()
            if(rows):
                self.update = True
            else:
                self.update = False
        except Exception as e:
                QMessageBox.critical(self, "Error", f"An error occurred.\nError:{e}", QMessageBox.Ok)
        
        if len(self.input_id.text().upper()) == 0 or len(self.input_name.text()) == 0 or len(self.input_email.text()) == 0:
            QMessageBox.warning(self, "Empty Field", "Please fill in all the fields.", QMessageBox.Ok)
        elif not re.match(r"[^@]+@[^@]+\.[^@]+", self.input_email.text()):
            QMessageBox.warning(self, "Invalid Email", "Please enter a valid email.", QMessageBox.Ok)
        else:
            QMessageBox.information(self, "Validate", "The validation is success.", QMessageBox.Ok)
            isValid = True

        if(isValid):
            self.btn_save.setEnabled(True)
    
    def fetch_teacher_data(self, search=None):
        # Create a database
        conn = sqlite3.connect('database.db')

        # Create a cursor
        cursor = conn.cursor()

        # Execute the sql statement
        if(search is None):
            cursor.execute("SELECT * FROM teachers")
        else:
            search = "%" + search + "%"
            cursor.execute("SELECT * FROM teachers WHERE teacher_id LIKE ?",(search,))

        # Fetch all the rows
        rows = cursor.fetchall()

        # Close the connection
        conn.close()

        self.teachers_data = []
        self.table.clearContents()
        self.table.setRowCount(0)
        for row in rows:
            teacher = {
                "teacher_id": row[0],
                "teacher_name": row[1],
                "teacher_gender": row[2],
                "teacher_email": row[3]
            }
            self.teachers_data.append(teacher)
        
        for row, teacher in enumerate(self.teachers_data):
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(teacher["teacher_id"]))
            self.table.setItem(row, 1, QTableWidgetItem(teacher["teacher_name"]))
            self.table.setItem(row, 2, QTableWidgetItem(teacher["teacher_gender"]))
            self.table.setItem(row, 3, QTableWidgetItem(teacher["teacher_email"]))
            # Set item flags to make cells not editable
            for col in range(4):
                item = self.table.item(row, col)
                if item:
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)

         # Apply padding to the table cells
        self.table.setStyleSheet("QTableWidget::item { padding: 5px; }")
    
    def closeEvent(self, event):
        # Clear input fields when the window is closed
        self.input_search.clear()
        self.input_id.clear()
        self.input_name.clear()
        self.input_email.clear()
        self.update = False
        self.btn_save.setEnabled(False)
        self.fetch_teacher_data()
        super().closeEvent(event)