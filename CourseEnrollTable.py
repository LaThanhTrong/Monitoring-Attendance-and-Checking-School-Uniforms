import sqlite3
from PyQt5 import uic
from PyQt5.QtWidgets import QMainWindow, QTableWidgetItem, QMessageBox, QAbstractItemView
from PyQt5.QtCore import pyqtSignal, Qt
from datetime import datetime
import pandas as pd

class CourseEnrollTable(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi("CourseEnroll.ui", self)
        self.cbb_course.addItems([course for course in self.getCourse()])
        self.btn_save.setEnabled(False)
        self.fetch_enroll_student_data()
        self.cbb_course.currentTextChanged.connect(lambda: self.fetch_enroll_student_data())
        self.fetch_not_enroll_student_data()
        self.cbb_course.currentTextChanged.connect(lambda: self.fetch_not_enroll_student_data())
        self.updateButtonStatus()
        self.setButtonConnection()
        self.input_room.textChanged.connect(self.changed)
        self.input_lesson.textChanged.connect(self.changed)
        self.input_week.textChanged.connect(self.changed)
        self.btn_check.clicked.connect(self.validate)
        self.btn_save.clicked.connect(self.save)

        # Set selection behavior to select entire rows
        self.tableUnavai.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tableAvai.setSelectionBehavior(QAbstractItemView.SelectRows)

    def save(self):
        try:
            conn = sqlite3.connect('database.db')
            cursor = conn.cursor()
            # Delete all data from schedule and CourseEnroll tables
            cursor.execute("DELETE FROM schedule WHERE enroll_id IN (SELECT enroll_id FROM CourseEnroll WHERE course_id = ?)", (self.cbb_course.currentText(),))
            cursor.execute("DELETE FROM CourseEnroll WHERE course_id = ?", (self.cbb_course.currentText(),))

            for row in range(self.tableAvai.rowCount()):
                student_id = self.tableAvai.item(row, 0).text()
                course_id = self.cbb_course.currentText()
                enroll_date = self.tableAvai.item(row, 2).text()

                # Insert data into CourseEnroll table
                cursor.execute("INSERT INTO CourseEnroll (enroll_date, student_id, course_id) VALUES (?, ?, ?)", (enroll_date, student_id, course_id))

                # Retrieve the newly inserted enroll_id
                enroll_id = cursor.lastrowid

                # Insert data into schedule table
                schedule_lesson = self.input_lesson.text()
                schedule_room = self.input_room.text()
                schedule_week = self.input_week.text()
                cursor.execute("INSERT INTO schedule (schedule_lesson, schedule_room, schedule_week, enroll_id) VALUES (?, ?, ?, ?)",
                            (schedule_lesson, schedule_room, schedule_week, enroll_id))

            conn.commit()
            QMessageBox.information(self, "Success", "The course enrollment data has been saved.", QMessageBox.Ok)
        except Exception as e:
            conn.rollback()
            QMessageBox.critical(self, "Error", f"An error occurred.\nError:{e}", QMessageBox.Ok)

        conn.close()
        self.change_signal.emit()
        self.input_room.clear()
        self.input_lesson.clear()
        self.input_week.clear()
        self.btn_save.setEnabled(False)
        self.fetch_enroll_student_data()
        self.fetch_not_enroll_student_data()
        self.updateButtonStatus()

    change_signal = pyqtSignal()

    def validate(self):
        if(len(self.input_room.text()) == 0 or len(self.input_lesson.text()) == 0 or len(self.input_week.text()) == 0):
            QMessageBox.warning(self, "Empty Field", "Please fill in all the fields.", QMessageBox.Ok)
        else:
            QMessageBox.information(self, "Validate", "The validation is success.", QMessageBox.Ok)
            self.btn_save.setEnabled(True)

    def changed(self):
        self.btn_save.setEnabled(False)
    
    def setButtonConnection(self):
        self.tableUnavai.itemSelectionChanged.connect(self.updateButtonStatus)
        self.tableAvai.itemSelectionChanged.connect(self.updateButtonStatus)

        self.btn_right.clicked.connect(self.buttonAddClicked)
        self.btn_left.clicked.connect(self.buttonRemoveClicked)
        self.btn_rightAll.clicked.connect(self.buttonAddAllClicked)
        self.btn_leftAll.clicked.connect(self.buttonRemoveAllClicked)

    def buttonAddClicked(self):
        row = self.tableUnavai.currentRow()
        items = [self.tableUnavai.takeItem(row, col) for col in range(self.tableUnavai.columnCount())]
        
        # Create a new QTableWidgetItem with the current date (yyyy-mm-dd)
        current_date = datetime.now().strftime('%Y-%m-%d')
        date_item = QTableWidgetItem(current_date)
        
        # Add the date item to the end of the items list
        items.append(date_item)
        
        self.addItemsToTable(self.tableAvai, items)
        

    def buttonRemoveClicked(self):
        row = self.tableAvai.currentRow()
        items = [self.tableAvai.takeItem(row, col) for col in range(self.tableAvai.columnCount())]
        self.addItemsToTable(self.tableUnavai, items)

    def addItemsToTable(self, table, items):
        row = table.rowCount()
        table.insertRow(row)
        for col, item in enumerate(items):
            table.setItem(row, col, item)
        self.removeEmptyUnavaiRows()
        self.removeEmptyAvaiRows()
    
    def removeEmptyUnavaiRows(self):
        rows_to_remove = []
        for row in range(self.tableUnavai.rowCount() - 1, -1, -1):
            row_is_empty = all(self.tableUnavai.item(row, col) is None for col in range(self.tableUnavai.columnCount()))
            if row_is_empty:
                rows_to_remove.append(row)

        for row in rows_to_remove:
            self.tableUnavai.removeRow(row)

    def removeEmptyAvaiRows(self):
        rows_to_remove = []
        for row in range(self.tableAvai.rowCount() - 1, -1, -1):
            row_is_empty = all(self.tableAvai.item(row, col) is None for col in range(self.tableAvai.columnCount()))
            if row_is_empty:
                rows_to_remove.append(row)

        for row in rows_to_remove:
            self.tableAvai.removeRow(row)
    
    def buttonAddAllClicked(self):
        while self.tableUnavai.rowCount() > 0:
            row = self.tableUnavai.rowCount() - 1
            items = [self.tableUnavai.takeItem(row, col) for col in range(self.tableUnavai.columnCount())]
            
            # Create a new QTableWidgetItem with the current date (yyyy-mm-dd)
            current_date = datetime.now().strftime('%Y-%m-%d')
            date_item = QTableWidgetItem(current_date)
            
            # Add the date item to the end of the items list
            items.append(date_item)
            
            self.addItemsToTable(self.tableAvai, items)
            self.removeEmptyUnavaiRows()
        

    def buttonRemoveAllClicked(self):
        while self.tableAvai.rowCount() > 0:
            row = self.tableAvai.rowCount() - 1
            items = [self.tableAvai.takeItem(row, col) for col in range(self.tableAvai.columnCount())]
            self.addItemsToTable(self.tableUnavai, items)
            self.removeEmptyAvaiRows()

    def updateButtonStatus(self):
        self.btn_right.setDisabled(not bool(self.tableUnavai.selectedItems()) or self.tableUnavai.rowCount() == 0)
        self.btn_left.setDisabled(not bool(self.tableAvai.selectedItems()) or self.tableAvai.rowCount() == 0)

    def getCourse(self):
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        sql = "SELECT course_id FROM courses"
        rows = cursor.execute(sql)
        columns = [col[0] for col in rows.description]
        records = rows.fetchall()
        df = pd.DataFrame(records, columns=columns)
        course = []
        for index, row in df.iterrows():
            course.append(row['course_id'])
        conn.close()
        return course
    
    def fetch_not_enroll_student_data(self, search=None):
        # Create a database
        conn = sqlite3.connect('database.db')

        # Create a cursor
        cursor = conn.cursor()

        # Execute the sql statement
        if(search is None):
            sql = """
                SELECT students.student_id, students.student_name FROM students
                LEFT JOIN courseenroll ON students.student_id = courseenroll.student_id AND courseenroll.course_id = ?
                WHERE courseenroll.student_id IS NULL
            """
            cursor.execute(sql,(self.cbb_course.currentText(),))
        else:
            sql = """
                SELECT students.student_id, students.student_name FROM students
                LEFT JOIN courseenroll ON students.student_id = courseenroll.student_id AND courseenroll.course_id = ? WHERE students.student_id LIKE ? and courseenroll.student_id IS NULL
            """
            search = "%" + search + "%"
            cursor.execute(sql,(self.cbb_course.currentText(), search))

        # Fetch all the rows
        rows = cursor.fetchall()

        # Close the connection
        conn.close()

        courses_data = []
        self.tableUnavai.clearContents()
        self.tableUnavai.setRowCount(0)
        for row in rows:
            course = {
                "student_id": row[0],
                "student_name": row[1]
            }
            courses_data.append(course)
        
        for row, course in enumerate(courses_data):
            self.tableUnavai.insertRow(row)
            self.tableUnavai.setItem(row, 0, QTableWidgetItem(course["student_id"]))
            self.tableUnavai.setItem(row, 1, QTableWidgetItem(course["student_name"]))
            # Set item flags to make cells not editable
            for col in range(2):
                item = self.tableUnavai.item(row, col)
                if item:
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)

         # Apply padding to the table cells
        self.tableUnavai.setStyleSheet("QTableWidget::item { padding: 5px; }")

    def fetch_enroll_student_data(self, search=None):
        # Create a database
        conn = sqlite3.connect('database.db')

        # Create a cursor
        cursor = conn.cursor()

        # Execute the sql statement
        if(search is None):
            sql = """
                SELECT courseenroll.student_id, students.student_name, courseenroll.enroll_date FROM courseenroll
                JOIN students ON courseenroll.student_id = students.student_id AND courseenroll.course_id = ?
            """
            cursor.execute(sql,(self.cbb_course.currentText(),))
        else:
            sql = """
                SELECT courseenroll.student_id, students.student_name, courseenroll.enroll_date FROM courseenroll
                JOIN students ON courseenroll.student_id = students.student_id AND courseenroll.course_id = ? WHERE courseenroll.student_id LIKE ?
            """
            search = "%" + search + "%"
            cursor.execute(sql,(self.cbb_course.currentText(),search,))

        # Fetch all the rows
        rows = cursor.fetchall()

        # Close the connection
        conn.close()

        courses_data = []
        self.tableAvai.clearContents()
        self.tableAvai.setRowCount(0)
        for row in rows:
            course = {
                "student_id": row[0],
                "student_name": row[1],
                "enroll_date": row[2]
            }
            courses_data.append(course)
        
        for row, course in enumerate(courses_data):
            self.tableAvai.insertRow(row)
            self.tableAvai.setItem(row, 0, QTableWidgetItem(course["student_id"]))
            self.tableAvai.setItem(row, 1, QTableWidgetItem(course["student_name"]))
            self.tableAvai.setItem(row, 2, QTableWidgetItem(course["enroll_date"]))
            # Set item flags to make cells not editable
            for col in range(3):
                item = self.tableAvai.item(row, col)
                if item:
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)

         # Apply padding to the table cells
        self.tableAvai.setStyleSheet("QTableWidget::item { padding: 5px; }")
    
    def closeEvent(self, event):
        self.input_room.clear()
        self.input_lesson.clear()
        self.input_week.clear()
        self.btn_save.setEnabled(False)
        self.fetch_enroll_student_data()
        self.fetch_not_enroll_student_data()
        self.updateButtonStatus()
        super().closeEvent(event)