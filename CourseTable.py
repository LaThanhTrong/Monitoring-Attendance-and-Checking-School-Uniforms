import sqlite3
import pandas as pd
from PyQt5.QtWidgets import QMainWindow, QTableWidgetItem, QMessageBox
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5 import uic

class CourseTable(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi("Courses.ui", self)
        self.btn_save.setEnabled(False)
        self.fetch_course_data()
        self.btn_search.clicked.connect(lambda: self.fetch_course_data(self.input_search.text()))
        self.cbb_teacher.addItems([teacher for teacher in self.getTeacherID()])
        self.btn_check.clicked.connect(self.validate)
        self.btn_save.clicked.connect(self.save)
        self.update = False

        # Connect textChanged signals to methods
        self.input_id.textChanged.connect(self.changed)
        self.input_name.textChanged.connect(self.changed)
        self.input_credits.textChanged.connect(self.changed)
        self.cbb_teacher.currentTextChanged.connect(self.changed)

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
                    UPDATE courses
                    SET course_name = ?,
                        course_credit = ?,
                        teacher_id = ?
                    WHERE course_id = ?
                """
                data = (self.input_name.text(), int(self.input_credits.text()), self.cbb_teacher.currentText(), self.input_id.text().upper())
                cursor.execute(sql, data)
                conn.commit()
                conn.close()
                QMessageBox.information(self, "Success", f"Course {self.input_id.text().upper()} has been updated.", QMessageBox.Ok)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"An error occurred.\nError:{e}", QMessageBox.Ok)

        else:
            try:
                conn = sqlite3.connect('database.db')
                cursor = conn.cursor()
                query = "INSERT INTO courses VALUES (?,?,?,?)"
                data = (self.input_id.text().upper(), self.input_name.text(), int(self.input_credits.text()), self.cbb_teacher.currentText())
                cursor.execute(query, data)
                conn.commit()
                conn.close()
                QMessageBox.information(self, "Success", "The course data has been saved.", QMessageBox.Ok)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"An error occurred.\nError:{e}", QMessageBox.Ok)

        self.change_signal.emit()
        self.input_search.clear()
        self.input_id.clear()
        self.input_name.clear()
        self.input_credits.clear()
        self.btn_save.setEnabled(False)
        self.update = False
        self.fetch_course_data()
    
    change_signal = pyqtSignal()
    
    def validate(self):
        isValid = False
        try:
            conn = sqlite3.connect('database.db')
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM courses WHERE course_id = ?", (self.input_id.text().upper(),))
            rows = cursor.fetchall()
            conn.close()
            if(rows):
                self.update = True
            else:
                self.update = False
        except Exception as e:
                QMessageBox.critical(self, "Error", f"An error occurred.\nError:{e}", QMessageBox.Ok)
        
        if(len(self.input_id.text().upper()) == 0 or len(self.input_name.text()) == 0 or len(self.input_credits.text()) == 0):
            QMessageBox.warning(self, "Empty Field", "Please fill in all the fields.", QMessageBox.Ok)
        elif not self.input_credits.text().isdigit():
            QMessageBox.warning(self, "Invalid Credits", "Please enter a valid number for credits.", QMessageBox.Ok)
        else:
            QMessageBox.information(self, "Validate", "The validation is success.", QMessageBox.Ok)
            isValid = True

        if(isValid):
            self.btn_save.setEnabled(True)
            
    def getTeacherID(self):
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        sql = "SELECT teacher_id FROM teachers"
        rows = cursor.execute(sql)
        columns = [col[0] for col in rows.description]
        records = rows.fetchall()
        df = pd.DataFrame(records, columns=columns)
        teacherID = []
        for index, row in df.iterrows():
            teacherID.append(row['teacher_id'])
        conn.close()
        return teacherID
    
    def fetch_course_data(self, search=None):
        # Create a database
        conn = sqlite3.connect('database.db')

        # Create a cursor
        cursor = conn.cursor()

        # Execute the sql statement
        if(search is None):
            sql = """
                SELECT courses.course_id, courses.course_name, courses.course_credit, courses.teacher_id, teachers.teacher_name FROM courses
                JOIN teachers ON courses.teacher_id = teachers.teacher_id
            """
            cursor.execute(sql)
        else:
            sql = """
                SELECT courses.course_id, courses.course_name, courses.course_credit, courses.teacher_id, teachers.teacher_name FROM courses
                JOIN teachers ON courses.teacher_id = teachers.teacher_id WHERE courses.course_id LIKE ?
            """
            search = "%" + search + "%"
            cursor.execute(sql,(search,))

        # Fetch all the rows
        rows = cursor.fetchall()

        # Close the connection
        conn.close()

        self.courses_data = []
        self.table.clearContents()
        self.table.setRowCount(0)
        for row in rows:
            course = {
                "course_id": row[0],
                "course_name": row[1],
                "course_credit": row[2],
                "teacher_id": row[3],
                "teacher_name": row[4]
            }
            self.courses_data.append(course)
        
        for row, course in enumerate(self.courses_data):
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(course["course_id"]))
            self.table.setItem(row, 1, QTableWidgetItem(course["course_name"]))
            self.table.setItem(row, 2, QTableWidgetItem(str(course["course_credit"])))
            self.table.setItem(row, 3, QTableWidgetItem(course["teacher_id"]))
            self.table.setItem(row, 4, QTableWidgetItem(course["teacher_name"]))
            # Set item flags to make cells not editable
            for col in range(5):
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
        self.input_credits.clear()
        self.update = False
        self.btn_save.setEnabled(False)
        self.fetch_course_data()
        super().closeEvent(event)