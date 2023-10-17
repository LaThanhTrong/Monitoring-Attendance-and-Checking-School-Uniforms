from PyQt5.QtWidgets import *
from PyQt5 import uic
from PyQt5.QtMultimedia import QCameraInfo
from PyQt5.QtCore import QThread, pyqtSignal, Qt, QTimer
from PyQt5.QtGui import QImage, QPixmap, QIcon
import numpy as np
import cv2
import time
from ultralytics import YOLO
from deepface import DeepFace
from playsound import playsound
from csv import writer
import os
import pandas as pd
import torch
from datetime import datetime
import sqlite3
import re
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from dotenv import load_dotenv
from CourseEnrollTable import CourseEnrollTable
from CourseTable import CourseTable
from TeacherTable import TeacherTable
from StudentTable import StudentTable
from HardwareInfo import HardwareInfo


pre_timeframe = 0
new_timeframe = 0

class LoadingScreen(QSplashScreen):
    def __init__(self):
        super().__init__(QPixmap("loadingscreen.png"))  # You can provide your loading image here

class StudentPopup(QWidget):
    def __init__(self, student_data):
        super().__init__()

        self.table = QTableWidget()
        self.setWindowIcon(QIcon("icon.png"))
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Student ID", "Student Name", "Student Gender", "Student Major", "Student Email"])

        for row, student in enumerate(student_data):
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
        
        # Resize the column widths to fit the content
        self.table.resizeColumnsToContents()
         # Apply padding to the table cells
        self.table.setStyleSheet("QTableWidget::item { padding: 5px; }")

        table_width = self.table.horizontalHeader().length()
        self.resize(table_width + 50, 600)

        layout = QVBoxLayout()
        layout.addWidget(self.table)
        self.setLayout(layout)
        global courseID
        self.setWindowTitle("List of students who enrolled in " + courseID)

class ThreadClass(QThread):
    # Define signal for this thread to emit when need to interact with MainWindow
    ImageUpdate = pyqtSignal(QImage)
    FPS = pyqtSignal(int)
    global camIndex, isRotate, isAlarm
    
    def run(self):
        RED = (0,0,255)
        GREEN = (0,255,0)
        global STUDENTS
        CLOTHES = {
            0: ['Sleeve', GREEN],
            1: ['Sleeveless', RED]
        }

        PANTS = {
            0: ['Long-Pant', GREEN],
            1: ['Short-Pant', RED]
        }
        Capture = cv2.VideoCapture(camIndex, cv2.CAP_DSHOW)
        Capture.set(cv2.CAP_PROP_SETTINGS, 1)
        self.ThreadActive = True
        # Initiate model
        modelStudents = YOLO("./models/yolov8n.pt")
        modelFace = YOLO("./models/yolov8n-face.pt")
        modelClothes = YOLO("./models/yolov8m-clothes_v2.pt")
        modelPants = YOLO("./models/yolov8m-pants_v2.pt")
        modelCard = YOLO("./models/yolov8n-card_v2.pt")
        
        while (self.ThreadActive):
            ret, frame = Capture.read()
            if not ret:
                break
            if(isRotate):
                pass
            else:
                frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)

            img = frame.copy()
            global arcFace, arcStudents, arcClothes, arcPants, arcCard
            # Get frame current height after resize
            cur_height = frame.shape[0]

            sound = False
            personName = ""
            isClothes = ""
            isPants = ""
            isCard = ""
            isID = ""

            # Calculate FPS in real time
            global pre_timeframe, new_timeframe
            # Calculate FPS in real-time
            new_timeframe = time.time()
            fps = 1/(new_timeframe-pre_timeframe)
            pre_timeframe = new_timeframe
            fps = int(fps)
            Image = frame.copy()
            
            resultStudents = self.detection(modelStudents,frame,arcStudents)
            for i in range(len(resultStudents)):
                if (resultStudents[i][5] == 0):
                    # Copy a frame only contain a person
                    img = frame[int(resultStudents[i][1]):int(resultStudents[i][3]), int(resultStudents[i][0]):int(resultStudents[i][2])].copy()
                    Image = self.draw(frame,"Person",(235, 255, 55),int(resultStudents[i][0]),int(resultStudents[i][1]),int(resultStudents[i][2]),int(resultStudents[i][3]),resultStudents[i][4])
                     # Face, Clothes, Pants detector
                    resultFace = self.detection(modelFace,img,arcFace)
                    resultClothes = self.detection(modelClothes,img,arcClothes)
                    resultPants = self.detection(modelPants,img,arcPants)

                    if(len(resultFace) > 0):
                        # Copy a frame only contain a face
                        face = img[int(resultFace[0][1]):int(resultFace[0][3]), int(resultFace[0][0]):int(resultFace[0][2])].copy()
                        # Run face recognition
                        resultPerson = DeepFace.find(face,"./dataFaces",model_name="ArcFace", enforce_detection=False, distance_metric = "euclidean_l2")
                        list = np.array(resultPerson)
                        if list[0].any():
                            list = list[0][0]
                            predict = list[0]
                            res = str(predict)
                            isID = res.split("/")[1].split("\\")[1]
                            if(isID in STUDENTS):
                                list = STUDENTS.get(isID)
                                personName = list[0]
                                Image = self.draw(frame,personName,list[1], int(resultStudents[i][0]+resultFace[0][0]), int(resultStudents[i][1]+resultFace[0][1]), int(resultStudents[i][0]+resultFace[0][2]), int(resultStudents[i][1]+resultFace[0][3]))
                            
                    if(len(resultClothes) > 0):
                        # Copy a frame only contain clothes
                        clothesImg = img[int(resultClothes[0][1]):int(resultClothes[0][3]), int(resultClothes[0][0]):int(resultClothes[0][2])].copy()
                        # Card detector
                        resultCard = self.detection(modelCard, clothesImg, arcCard)
                        # Loop for number of card found in clothes (Remove loop only require only a card)
                        for c in range(len(resultCard)):
                            if(resultCard[c][5] == 0):
                                Image = self.draw(frame,"Card",(0,255,0), int(resultStudents[i][0]+resultClothes[0][0]+resultCard[c][0]), int(resultStudents[i][1]+resultClothes[0][1]+resultCard[c][1]), int(resultStudents[i][0]+resultClothes[0][0]+resultCard[c][2]), int(resultStudents[i][1]+resultClothes[0][1]+resultCard[c][3]),resultCard[c][4])
                                isCard = "Verified"
                        if(resultClothes[0][5] == 0 and resultClothes[0][4] > 0.5):
                            list = CLOTHES[resultClothes[0][5]]
                            Image = self.draw(frame,list[0],list[1], int(resultStudents[i][0]+resultClothes[0][0]), int(resultStudents[i][1]+resultClothes[0][1]), int(resultStudents[i][0]+resultClothes[0][2]), int(resultStudents[i][1]+resultClothes[0][3]),resultClothes[0][4])
                            isClothes = list[0]
                        if(resultClothes[0][5] == 1 and resultClothes[0][4] > 0.5):
                            list = CLOTHES[resultClothes[0][5]]
                            Image = self.draw(frame,list[0],list[1], int(resultStudents[i][0]+resultClothes[0][0]), int(resultStudents[i][1]+resultClothes[0][1]), int(resultStudents[i][0]+resultClothes[0][2]), int(resultStudents[i][1]+resultClothes[0][3]),resultClothes[0][4])
                            isClothes = list[0]
                            if(sound == False and isAlarm == True):
                                playsound('./sound.mp3')
                                sound = True

                    if(len(resultPants) > 0):
                        # Note: Detect pants only the bottom reach frame current height minus 15
                        if((resultPants[0][5] == 1) and (resultPants[0][4] > 0.5) and (resultStudents[i][1]+resultPants[0][3] < cur_height-15)):
                            list = PANTS[resultPants[0][5]]
                            Image = self.draw(frame,list[0],list[1], int(resultStudents[i][0]+resultPants[0][0]), int(resultStudents[i][1]+resultPants[0][1]), int(resultStudents[i][0]+resultPants[0][2]), int(resultStudents[i][1]+resultPants[0][3]),resultPants[0][4])
                            isPants = list[0]
                            if(sound == False and isAlarm == True):
                                playsound('./sound.mp3')
                                sound = True

                        if((resultPants[0][5] == 0) and (resultPants[0][4] > 0.5) and (resultStudents[i][1]+resultPants[0][3] < cur_height-15)):
                            list = PANTS[resultPants[0][5]]
                            Image = self.draw(frame,list[0],list[1], int(resultStudents[i][0]+resultPants[0][0]), int(resultStudents[i][1]+resultPants[0][1]), int(resultStudents[i][0]+resultPants[0][2]), int(resultStudents[i][1]+resultPants[0][3]),resultPants[0][4])
                            isPants = list[0]

                # Write in csv
                if(isID != "" and isID in STUDENTS):
                    now = datetime.now()
                    try:
                        self.write_csv(isID,personName,isClothes,isPants,isCard,now.strftime("%d/%m/%Y %H:%M:%S"))
                    except Exception as e:
                        pass
                    
            ConvertQtFormat = QImage(Image.data, Image.shape[1], Image.shape[0], QImage.Format_BGR888)
            Pic = ConvertQtFormat.scaled(411, 598, Qt.KeepAspectRatio)
            # Emit Thread from data Pic
            self.ImageUpdate.emit(Pic)
            self.FPS.emit(fps)
        Capture.release()

    def stop(self):
        self.ThreadActive = False
        self.quit()
        if(os.path.isfile('./attendance.csv')):
            global teacher, course, course_credits, room
            new_data = "Teacher," + teacher + "\n" + "Room," + room + "\n" + "Course," + course + "\n" + "Course Credit," + str(course_credits) + "\n"
            with open('./attendance.csv', 'r') as file:
                existing_content = file.read()
                file.close()

            combined_content = new_data + existing_content
            with open('./attendance.csv', 'w') as file:
                file.write(combined_content)
                file.close()

    def detection(self, model, frame, accuracy):
        # List of Results objects
        results = model(frame, conf = accuracy, stream=True)
        boxes = []
        for result in results:
            # Convert into tensor array contains all necessary data
            # [[x1,y1,x2,y2,conf,class],[x1,y1,x2,y2,conf,class], ...]
            boxes = result.boxes.data.to('cpu').numpy()
        return boxes
    
    def draw(self, frame, name, color, x1, y1, x2, y2, conf = -1):
        frame = cv2.rectangle(frame, (x1,y1), (x2,y2), color,  4)
        # Draw additional rectangle for label
        if(conf == -1):
            (text_width, text_height) = cv2.getTextSize('{}'.format(name), cv2.FONT_HERSHEY_SIMPLEX, fontScale=0.5, thickness=2)[0]
        else:
            (text_width, text_height) = cv2.getTextSize('{}: {}%'.format(name,str(int(conf*100))), cv2.FONT_HERSHEY_SIMPLEX, fontScale=0.5, thickness=2)[0]
        # Adding additional padding
        box_coords = ((x1-2, y1), (x1 + text_width + 2, y1 - text_height - 10))
        frame = cv2.rectangle(frame, box_coords[0], box_coords[1], color, cv2.FILLED)
        # Put Lable and Confidence
        if(conf == -1):
            frame = cv2.putText(frame, '{}'.format(name), (x1,y1-8), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,255,255), 2)
        else:
            frame = cv2.putText(frame, '{}: {}%'.format(name,str(int(conf*100))), (x1,y1-8), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,255,255), 2)
        return frame
    
    def write_csv(self,isID, person, isClothes, isPants, isCard, datetime):
        header = ['StudentID', 'StudentName', 'Clothes', 'Pants', 'Card', 'DateTime']
        file_path = './attendance.csv'

        if os.path.isfile(file_path):
            df = pd.read_csv(file_path, index_col=header[0])

            if isID in df.index:
                update_columns = [header[1], header[2], header[3], header[4], header[5]]
                data_to_update = [person, isClothes, isPants, isCard, datetime]

                for col, data in zip(update_columns, data_to_update):
                    if df.loc[isID, col] != "" and data == "":
                        pass
                    else:
                        df.loc[isID, col] = data

                df.loc[isID, header[5]] = datetime
                df.to_csv(file_path)
            else:
                new_person_data = [isID, person, isClothes, isPants, isCard, datetime]
                with open(file_path, 'a', encoding='utf-8') as f_object:
                    writer_object = writer(f_object)
                    writer_object.writerow(new_person_data)
        else:
            with open(file_path, 'a', encoding='utf-8') as f_object:
                writer_object = writer(f_object)
                writer_object.writerow(header)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        uic.loadUi("Opencv_dash.ui",self)
        self.hardware.setText(str(torch.device("cuda" if torch.cuda.is_available() else "cpu")).upper())
        try:
            self.device.setText(str(torch.cuda.get_device_name(0)))
        except Exception as e:
            self.device.setText("Torch CUDA not found")

        self.createTable()

        global isRotate, isAlarm
        isRotate = False
        isAlarm = True
        self.setWindowIcon(QIcon("icon.png"))
        self.cv2Worker = None 
        self.online_cam = QCameraInfo.availableCameras()
        self.hardware = HardwareInfo()
        self.hardware.start()
        self.hardware.cpu.connect(self.getCPU_usage)
        self.hardware.ram.connect(self.getRAM_usage)
        self.hardware.gpu.connect(self.getGPU_usage)

        self.camlist.addItems([cam.description() for cam in self.online_cam])
        self.checkCam()
        self.camlist.currentIndexChanged.connect(self.checkCam)
        self.camlist.currentTextChanged.connect(self.checkCam)
        self.btn_stop.setEnabled(False)
        self.btn_start.clicked.connect(self.StartWebCam)
        self.btn_stop.clicked.connect(self.StopWebCam)

        self.btn_rotate_set.clicked.connect(self.set_rotate)
        self.btn_alarm_set.clicked.connect(self.set_alarm)

        global arcFace, arcStudents, arcClothes, arcPants, arcCard
        arcFace = 0.5
        arcStudents = 0.5
        arcClothes = 0.5
        arcPants = 0.5
        arcCard = 0.5

        self.slide_face = self.findChild(QSlider, 'slide_face')
        self.label_face = self.findChild(QLabel, 'label_face')
        self.slide_face.setValue(int(arcFace*100))
        self.label_face.setText(str(int(arcFace*100)))
        self.slide_face.valueChanged.connect(self.changeValue_face)

        self.slide_students = self.findChild(QSlider, 'slide_students')
        self.label_students = self.findChild(QLabel, 'label_students')
        self.slide_students.setValue(int(arcStudents*100))
        self.label_students.setText(str(int(arcStudents*100)))
        self.slide_students.valueChanged.connect(self.changeValue_students)

        self.slide_clothes = self.findChild(QSlider, 'slide_clothes')
        self.label_clothes = self.findChild(QLabel, 'label_clothes')
        self.slide_clothes.setValue(int(arcClothes*100))
        self.label_clothes.setText(str(int(arcClothes*100)))
        self.slide_clothes.valueChanged.connect(self.changeValue_clothes)

        self.slide_pants = self.findChild(QSlider, 'slide_pants')
        self.label_pants = self.findChild(QLabel, 'label_pants')
        self.slide_pants.setValue(int(arcPants*100))
        self.label_pants.setText(str(int(arcPants*100)))
        self.slide_pants.valueChanged.connect(self.changeValue_pants)

        self.slide_card = self.findChild(QSlider, 'slide_card')
        self.label_card = self.findChild(QLabel, 'label_card')
        self.slide_card.setValue(int(arcCard*100))
        self.label_card.setText(str(int(arcCard*100)))
        self.slide_card.valueChanged.connect(self.changeValue_card)

        self.courselist.addItems([course for course in self.getCourse()])
        # Set the default selection to empty
        self.courselist.setCurrentIndex(-1)
        self.btn_coSetCourse.clicked.connect(lambda: self.setSchedule(self.courselist.currentText()))

        self.btn_sendEmail.clicked.connect(self.sendEmail)
        self.cooldown_timer = QTimer(self)
        self.cooldown_timer.timeout.connect(self.update_timer)
        self.remaining_time = 0

        self.btn_liststudents.clicked.connect(self.show_student_list)
        self.student_popup = None

        self.students = []

        self.students_table = StudentTable()
        self.students_table.change_signal.connect(self.listener)
        self.btn_studentsTable.clicked.connect(self.show_students_table)

        self.teachers_table = TeacherTable()
        self.teachers_table.change_signal.connect(self.listener)
        self.teachers_table.change_signal.connect(self.updateTeacher)
        self.btn_teachersTable.clicked.connect(self.show_teachers_table)

        self.courses_table = CourseTable()
        self.courses_table.change_signal.connect(self.listener)
        self.courses_table.change_signal.connect(self.updateCourse)
        self.btn_coursesTable.clicked.connect(self.show_courses_table)

        self.course_enroll_table = CourseEnrollTable()
        self.course_enroll_table.change_signal.connect(self.listener)
        self.btn_enrollsTable.clicked.connect(self.show_enrolls_table)

    def checkCam(self):
        if(self.camlist.count() == 0):
            self.btn_start.setEnabled(False)
        else:
            self.btn_start.setEnabled(True)
    
    def listener(self):
        if(self.courselist.currentIndex() != -1):
            self.updateCourse()
            self.setSchedule(self.courselist.currentText())

    def updateCourse(self):
        self.courselist.clear()
        self.courselist.addItems([course for course in self.getCourse()])
        self.course_enroll_table.cbb_course.clear()
        self.course_enroll_table.cbb_course.addItems([course for course in self.getCourse()])
    
    def updateTeacher(self):
        self.courses_table.cbb_teacher.clear()
        self.courses_table.cbb_teacher.addItems([teacher for teacher in self.getTeacherID()])

    def show_students_table(self):
        self.students_table.show()
    
    def show_teachers_table(self):
        self.teachers_table.show()
    
    def show_courses_table(self):
        self.courses_table.show()
    
    def show_enrolls_table(self):
        self.course_enroll_table.show()
    
    def createTable(self):
        # Create a database
        conn = sqlite3.connect('database.db')

        # Create a table
        sql_createStudents_table = """
        CREATE TABLE IF NOT EXISTS students (
            student_id TEXT PRIMARY KEY,
            student_name TEXT NOT NULL,
            student_gender TEXT NOT NULL,
            student_major TEXT NOT NULL,
            student_email TEXT NOT NULL
        )
        """

        sql_createTeachers_table = """
        CREATE TABLE IF NOT EXISTS teachers (
            teacher_id TEXT PRIMARY KEY,
            teacher_name TEXT NOT NULL,
            teacher_gender TEXT NOT NULL,
            teacher_email TEXT NOT NULL
        )
        """

        sql_createCourses_table = """
        CREATE TABLE IF NOT EXISTS courses (
            course_id TEXT PRIMARY KEY,
            course_name TEXT NOT NULL,
            course_credit INTEGER NOT NULL,
            teacher_id TEXT, FOREIGN KEY (teacher_id) REFERENCES teachers(teacher_id)
        )
        """

        sql_createCourseEnroll_table = """
        CREATE TABLE IF NOT EXISTS CourseEnroll (
            enroll_id INTEGER PRIMARY KEY AUTOINCREMENT,
            enroll_date DATE NOT NULL,
            student_id TEXT,
            course_id TEXT, 
            FOREIGN KEY (student_id) REFERENCES students(student_id),
            FOREIGN KEY (course_id) REFERENCES courses(course_id)
        )
        """

        sql_createSchedule_table = """
        CREATE TABLE IF NOT EXISTS schedule (
            schedule_id INTEGER PRIMARY KEY AUTOINCREMENT,
            schedule_lesson TEXT NOT NULL,
            schedule_room TEXT NOT NULL,
            schedule_week TEXT NOT NULL,
            enroll_id INTEGER, FOREIGN KEY (enroll_id) REFERENCES CourseEnroll(enroll_id)
        )   
        """

        # Create a cursor
        cursor = conn.cursor()

        # Execute the sql statement
        # Commit the changes
        try:
            cursor.execute(sql_createStudents_table)
            cursor.execute(sql_createTeachers_table)
            cursor.execute(sql_createCourses_table)
            cursor.execute(sql_createCourseEnroll_table)
            cursor.execute(sql_createSchedule_table)
            conn.commit()
        except Exception as e:
            conn.rollback()
        
        conn.close()

    def ImageUpdateSlot(self, Image):
        global isFeed
        if(isFeed):
            self.disp_main.setPixmap(QPixmap.fromImage(Image))
        else:
            self.disp_main.clear()
            self.disp_main.setText("Main Source")

    def show_student_list(self):
        if (not self.label_coCourse.text()):
            error_message = "Please set a course before proceeding."
            error_dialog = QMessageBox()
            icon = self.style().standardIcon(QStyle.SP_MessageBoxWarning)
            error_dialog.setWindowIcon(icon)
            error_dialog.setIcon(QMessageBox.Warning)
            error_dialog.setWindowTitle("Student List Error")
            error_dialog.setText(error_message)
            error_dialog.setStandardButtons(QMessageBox.Ok)
            error_dialog.exec_()
        else:
            if self.student_popup is None or not self.student_popup.isVisible():
                self.student_popup = StudentPopup(self.students)
                self.student_popup.show()
    
    def closeEvent(self, event):
        if self.student_popup:
            self.student_popup.close()
        if self.students_table:
            self.students_table.close()
        if self.teachers_table:
            self.teachers_table.close()
        if self.courses_table:
            self.courses_table.close()
        if self.course_enroll_table:
            self.course_enroll_table.close()
        if self.cv2Worker:
            self.cv2Worker.stop()
            self.cv2Worker.wait()
        
        event.accept()
    
    def StartFeed(self):
        if self.student_popup:
            self.student_popup.close()
        if self.students_table:
            self.students_table.close()
        if self.teachers_table:
            self.teachers_table.close()
        if self.courses_table:
            self.courses_table.close()
        if self.course_enroll_table:
            self.course_enroll_table.close()
        try:
            self.btn_stop.setEnabled(True)
            self.btn_start.setEnabled(False)
            self.btn_sendEmail.setEnabled(False)
            self.btn_coSetCourse.setEnabled(False)
            self.btn_studentsTable.setEnabled(False)
            self.btn_teachersTable.setEnabled(False)
            self.btn_coursesTable.setEnabled(False)
            self.btn_enrollsTable.setEnabled(False)

            global camIndex
            camIndex = self.camlist.currentIndex()
            self.cv2Worker = ThreadClass() 
            self.cv2Worker.ImageUpdate.connect(self.ImageUpdateSlot)
            self.cv2Worker.FPS.connect(self.getFPS)
            self.cv2Worker.start() 
            self.cv2Worker.finished.connect(self.ThreadClassStop)
    
        except Exception as e:
            pass
    
    def StartWebCam(self):
        global isFeed
        isFeed = True
        if (not self.label_coCourse.text()):
            error_message = "Please set a course from Schedule Overview before proceeding."
            error_dialog = QMessageBox()
            icon = self.style().standardIcon(QStyle.SP_MessageBoxWarning)
            error_dialog.setWindowIcon(icon)
            error_dialog.setIcon(QMessageBox.Warning)
            error_dialog.setWindowTitle("Webcam Error")
            error_dialog.setText(error_message)
            error_dialog.setStandardButtons(QMessageBox.Ok)
            error_dialog.exec_()
        else:
            if(os.path.isfile('./attendance.csv')):
                warning = QMessageBox.warning(self, "Attendance file found", "File attendance.csv found. Start webcam may delete the previous file. Do you want to proceed?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                if(warning == QMessageBox.Yes):
                    os.remove('./attendance.csv')
                    self.StartFeed()
            else:
                self.StartFeed()

    def StopWebCam(self):
        global isFeed
        isFeed = False
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.btn_sendEmail.setEnabled(True)
        self.btn_coSetCourse.setEnabled(True)
        self.btn_studentsTable.setEnabled(True)
        self.btn_teachersTable.setEnabled(True)
        self.btn_coursesTable.setEnabled(True)
        self.btn_enrollsTable.setEnabled(True)
        self.cv2Worker.stop()
        
    
    def ThreadClassStop(self):
        self.cv2Worker = None

    def getFPS(self, fps):
        global isFeed
        if(isFeed):
            self.Qlabel_fps.setText(str(fps))
            if fps > 5: self.Qlabel_fps.setStyleSheet("color: rgb(237, 85, 59);")
            if fps > 15: self.Qlabel_fps.setStyleSheet("color: rgb(60, 174, 155);")
            if fps > 25: self.Qlabel_fps.setStyleSheet("color: rgb(85, 170, 255);")
            if fps > 35: self.Qlabel_fps.setStyleSheet("color: rgb(23, 63, 95);")
        else:
            self.Qlabel_fps.setText("0.0")
            self.Qlabel_fps.setStyleSheet("color: black;")

    def getCPU_usage(self,cpu):
        self.Qlabel_cpu.setText(str(cpu) + " %")
        if cpu > 15: self.Qlabel_cpu.setStyleSheet("color: rgb(23, 63, 95);")
        if cpu > 25: self.Qlabel_cpu.setStyleSheet("color: rgb(32, 99, 155);")
        if cpu > 45: self.Qlabel_cpu.setStyleSheet("color: rgb(60, 174, 163);")
        if cpu > 65: self.Qlabel_cpu.setStyleSheet("color: rgb(246, 213, 92);")
        if cpu > 85: self.Qlabel_cpu.setStyleSheet("color: rgb(237, 85, 59);")
    
    def getRAM_usage(self,ram):
        self.Qlabel_ram.setText(str(ram[2]) + " %")
        if ram[2] > 15: self.Qlabel_ram.setStyleSheet("color: rgb(23, 63, 95);")
        if ram[2] > 25: self.Qlabel_ram.setStyleSheet("color: rgb(32, 99, 155);")
        if ram[2] > 45: self.Qlabel_ram.setStyleSheet("color: rgb(60, 174, 163);")
        if ram[2] > 65: self.Qlabel_ram.setStyleSheet("color: rgb(246, 213, 92);")
        if ram[2] > 85: self.Qlabel_ram.setStyleSheet("color: rgb(237, 85, 59);")
    
    def getGPU_usage(self,gpu):
        self.Qlabel_gpu.setText(str(gpu) + " %")
        if gpu > 15: self.Qlabel_gpu.setStyleSheet("color: rgb(23, 63, 95);")
        if gpu > 25: self.Qlabel_gpu.setStyleSheet("color: rgb(32, 99, 155);")
        if gpu > 45: self.Qlabel_gpu.setStyleSheet("color: rgb(60, 174, 163);")
        if gpu > 65: self.Qlabel_gpu.setStyleSheet("color: rgb(246, 213, 92);")
        if gpu > 85: self.Qlabel_gpu.setStyleSheet("color: rgb(237, 85, 59);")

    def set_rotate(self):
        global isRotate
        if(self.ckb_rotate.isChecked() == True):
            isRotate = True
        else:
            isRotate = False
    
    def set_alarm(self):
        global isAlarm
        if(self.ckb_alarm.isChecked() == False):
            isAlarm = True
        else:
            isAlarm = False
    
    def changeValue_face(self, value):
        global arcFace
        arcFace = value/100
        self.label_face.setText(str(value))

    def changeValue_students(self, value):
        global arcStudents
        arcStudents = value/100
        self.label_students.setText(str(value))
    
    def changeValue_clothes(self, value):
        global arcClothes
        arcClothes = value/100
        self.label_clothes.setText(str(value))
    
    def changeValue_pants(self, value):
        global arcPants
        arcPants = value/100
        self.label_pants.setText(str(value))
    
    def changeValue_card(self, value):
        global arcCard
        arcCard = value/100
        self.label_card.setText(str(value))
    
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

    def setSchedule(self, course_id):
        if (self.courselist.currentIndex() == -1):
            error_message = "Please select a course before proceeding."
            error_dialog = QMessageBox()
            icon = self.style().standardIcon(QStyle.SP_MessageBoxWarning)
            error_dialog.setWindowIcon(icon)
            error_dialog.setIcon(QMessageBox.Warning)
            error_dialog.setWindowTitle("Course Overview Error")
            error_dialog.setText(error_message)
            error_dialog.setStandardButtons(QMessageBox.Ok)
            error_dialog.exec_()
        else:
            conn = sqlite3.connect('database.db')
            cursor = conn.cursor()
            sql = """
            SELECT students.student_id, students.student_name, students.student_gender, students.student_major, students.student_email, courses.course_name, courses.course_credit, teachers.teacher_name, schedule.schedule_room, schedule.schedule_lesson, schedule.schedule_week
            FROM students JOIN CourseEnroll ON students.student_id = CourseEnroll.student_id
            JOIN courses ON CourseEnroll.course_id = courses.course_id
            JOIN teachers ON courses.teacher_id = teachers.teacher_id
            JOIN schedule ON CourseEnroll.enroll_id = schedule.enroll_id
            WHERE courses.course_id = ?;
            """
            rows = cursor.execute(sql, (course_id,))
            columns = [col[0] for col in rows.description]
            records = rows.fetchall()
            conn.close()
            self.students = []
            for record in records:
                students = {
                    "student_id": record[0],
                    "student_name": record[1],
                    "student_gender": record[2],
                    "student_major": record[3],
                    "student_email": record[4]
                }
                self.students.append(students)

            df = pd.DataFrame(records, columns=columns)
            global teacher, course, course_credits, room, courseID, STUDENTS
            courseID = course_id
            STUDENTS = {}
            try:
                teacher = df['teacher_name'][0]
                course = df['course_name'][0]
                course_credits = df['course_credit'][0]
                room = df['schedule_room'][0]
                lesson = df['schedule_lesson'][0]
                week = df['schedule_week'][0]
                self.label_coCourse.setText(course)
                self.label_coTeacher.setText(teacher)
                self.label_coCredits.setText(str(course_credits))
                self.label_coRoom.setText(room)
                self.label_coLesson.setText(lesson)
                self.label_coWeek.setText(week)
                for index, row in df.iterrows():
                    student_id = row['student_id']
                    student_name = row['student_name']
                    color = (np.random.randint(0, 255), np.random.randint(0, 255), np.random.randint(0, 255))
                    STUDENTS[student_id] = [student_name, color]
            except Exception as e:
                STUDENTS = {}
                self.label_coCourse.setText("")
                self.label_coTeacher.setText("")
                self.label_coCredits.setText("")
                self.label_coRoom.setText("")
                self.label_coLesson.setText("")
                self.label_coWeek.setText("")
    
    def send_emails(self, emails_to):
        load_dotenv()
        smtp_port = 587
        smtp_server = "smtp.gmail.com"
        email_from = os.getenv("EMAIL")
        pswd = os.getenv("PSWD")
        subject = "Monitoring Attendance and Checking School Uniforms of Students"
        for email in emails_to:
            body = f"""
            Hello,

            This is an email sent by the Monitoring Attendance and Checking School Uniforms of Students.

            Please check the attachment for the attendance list.
            """
            msg = MIMEMultipart()
            msg["From"] = email_from
            msg["To"] = email
            msg["Subject"] = subject

            msg.attach(MIMEText(body, "plain"))

            file = "attendance.csv"
            attachment = open(file, "rb")
            attachment_package = MIMEBase("application", "octet-stream")
            attachment_package.set_payload(attachment.read())
            encoders.encode_base64(attachment_package)
            attachment_package.add_header("Content-Disposition", f"attachment; filename= {file}")
            msg.attach(attachment_package)

            text = msg.as_string()
            try:
                TIE_server = smtplib.SMTP(smtp_server, smtp_port)
                TIE_server.starttls()
                TIE_server.login(email_from, pswd)
                TIE_server.sendmail(email_from, email, text)
                QMessageBox.information(self, "Email sent", "Emails have been sent successfully. Please check your inbox.")
                TIE_server.quit()
            except Exception as e:
                QMessageBox.critical(self, "Email Error", "An error occurred while sending the email. Please try again.\nError: " + str(e))

    def sendEmail(self):
        if(not os.path.isfile('./attendance.csv')):
            QMessageBox.critical(self, "Csv file not found", "No attendance.csv found. Consider running the webcam and check for attendance first.")
        elif(not self.btn_start.isEnabled()):
            QMessageBox.critical(self, "Webcam is running", "Please stop the webcam before proceeding.")
        else:
            email_text = self.textEditEmails.toPlainText()
            emails = re.findall(r'\S+@\S+', email_text)
            valid_emails = []
            for email in emails:
                if self.validate_email(email):
                    valid_emails.append(email)
            if valid_emails:
                confirmation = QMessageBox.question(
                    self,
                    "Confirmation",
                    f"Are you sure you want to proceed with the following emails?\n\n{', '.join(valid_emails)}",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )

                if confirmation == QMessageBox.Yes:
                    self.btn_sendEmail.setEnabled(False)
                    self.remaining_time = 10
                    self.update_timer()
                    self.cooldown_timer.start(1000)
                    self.send_emails(valid_emails)
                else:
                    pass
            else:
                QMessageBox.warning(self, "Invalid Emails", "No valid email addresses found.")

    def update_timer(self):
        if self.remaining_time > 0:
            self.btn_sendEmail.setText(f"{self.remaining_time} seconds")
            self.remaining_time -= 1
        else:
            self.cooldown_timer.stop()
            self.btn_sendEmail.setText("SEND")  # Clear the timer label
            self.btn_sendEmail.setEnabled(True)  # Re-enable the button
    
    def validate_email(self, email):
        pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
        return re.match(pattern, email)


if __name__ == "__main__":
    app = QApplication([])
    loadingscreen = LoadingScreen()
    loadingscreen.show()
    window = MainWindow()
    window.show()
    loadingscreen.finish(window)
    app.exec_()
