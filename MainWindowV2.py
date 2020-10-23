# -*- coding: utf-8 -*-
"""
Created on Tue Aug 18 15:59:10 2020
##登入ui Exp https://www.itread01.com/content/1550086415.html
@author: 2007020
"""
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import RPi.GPIO as GPIO
import cv2
import matplotlib.pyplot as plt
import sys
import pandas as pd
import numpy as np
from ui_MainWindow import Ui_MainWindow
import threading
import time
# 影片檔案
videoFile = 0
input_pin = 18  # BCM pin 18, BOARD pin 12
LED_G=17         # BCM pin 17, BOARD pin 11
LED_R=27        # BCM pin 27, BOARD pin 13
# 開啟影片檔
GPIO.setmode(GPIO.BCM)  # 設置為BCM模式（您也可以自行改為BOARD模式）
GPIO.setup(input_pin, GPIO.IN)  # 設置輸入的腳位為input_pin
GPIO.setup(LED_R, GPIO.OUT)  # 設置輸入的腳位為input_pin
GPIO.setup(LED_G, GPIO.OUT)  # 設置輸入的腳位為input_pin
GPIO.output(LED_R,GPIO.LOW)
GPIO.output(LED_G,GPIO.LOW)
n = 0
spec = 890

def BigYellow(self,imgR):
 img = cv2.cvtColor(imgR,cv2.COLOR_BGR2HSV)
 lower = np.array([0,0,50])
 upper = np.array([50,255,255])
 # 获得指定颜色范围内的掩码
 mask = cv2.inRange(img,lower,upper)
 # 对原图图像进行按位与的操作，掩码区域保留
 imgResult = cv2.bitwise_and(img,img,mask=mask)
 cv2.imwrite("Resulhsv2.jpg", imgResult)
 #轉灰階＆二值化
 img2 = cv2.cvtColor(imgResult,cv2.COLOR_BGR2GRAY)
 ret,thresh = cv2.threshold(img2,100,255,cv2.THRESH_BINARY)
 contours, _ = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
 area = []
 for k in range(len(contours)):
  area.append((k,contours[k].shape[0]))
 np.argmax(area,1)
 area.sort(key=lambda score: score[1])
 index,_ = area[-4]
 #cv2.contourArea(contours[-1])
 temp = np.zeros(img.shape,np.uint8)*255
 #畫出輪廓：temp是白色幕布，contours是輪廓，-1表示全畫，然後是顏色，厚度
 mask2 = cv2.drawContours(temp, contours, index, (1,1,1), cv2.FILLED)
 GRAY = cv2.cvtColor(mask2,cv2.COLOR_BGR2GRAY)
 #垂直投影
 Xlist = []
 XAxis = []
 for h in range(0,GRAY.shape[0]):
  Xlist.append(np.sum(GRAY[h,:]))
  if np.sum(GRAY[h,:]) > 1:
   XAxis.append(h)
 #水平投影
 Ylist = []
 YAxis = []
 for w in range(0,GRAY.shape[1]):
  Ylist.append(np.sum(GRAY[:,w]))
  if np.sum(GRAY[:,w]) > 1:
   YAxis.append(w)
 yy = np.argmax(Xlist)
 xx = np.argmax(Ylist)
 Rels2 = imgR.copy()
 yValue = Xlist[yy]
 xValue = Ylist[xx]
 ##cv2.line(影像, 開始座標, 結束座標, 顏色, 線條寬度)
 cv2.line(Rels2,(YAxis[1],yy) , (YAxis[-1],yy), (0, 0, 255), 5)
 cv2.line(Rels2,(xx,XAxis[1]) , (xx,XAxis[-1]), (0, 255, 0), 5)
 ###cv2.putText(影像, 文字, 座標, 字型, 大小, 顏色, 線條寬度, 線條種類)
 text = 'R:%i G:%i'%(yValue,xValue)
 cv2.putText(Rels2, text, (50, 50), cv2.FONT_HERSHEY_PLAIN,5, (0, 255, 255), 5, cv2.LINE_AA)
 cv2.imwrite("Result.jpg", Rels2)
 return(yValue+xValue)
class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super(MainWindow,self).__init__()
        Ui_MainWindow.__init__(self)
        self.setupUi(self)
        self.n = 1
        # 執行緒自定義訊號連線的槽函式
        self.work = WorkThread()
        self.work.start()
        self.work.changePixmap.connect(self.img_output.setPixmap)
        
        self.start_btn.clicked.connect(self.execute)
#        self.close_btn.clicked.connect(QCoreApplication.instance().quit)
        self.close_btn.clicked.connect(self.Checkstop)

    def execute(self):
        # 啟動執行緒
        self.thread = Check()
        self.thread.file_changed_signal.connect(self.update_file_list)
        self.start_btn.setEnabled(False)
        self.thread.start()

    def Checkstop(self):
        self.start_btn.setEnabled(True)
        self.thread.stop()
      
    def update_file_list(self, file_inf):
        self.VALUE.setText(str(file_inf))
        SW = GPIO.input(18)
        if file_inf >= 3 and SW == GPIO.HIGH :
         Value = BigYellow(self,self.work.getframe())
         if Value >= spec:
          self.RGB.setPixmap(QPixmap('RED.jpg'))
          self.RGB.setScaledContents(True)
         else:
          self.RGB.setPixmap(QPixmap('GREED.jpg'))
          self.RGB.setScaledContents(True)
         self.img_output_2.setPixmap(QPixmap('Result.jpg'))
         self.img_output_2.setScaledContents(True)

class Check(QThread):
    file_changed_signal = pyqtSignal(int) # 信号类型：str
    
    def __init__(self, sec=0, parent=None):
        super().__init__(parent)
        self.working = True
        self.sec = sec
        
    def __del__(self):
        self.working = True
        self.wait()
        
    def run(self):
        while self.working == True:
            self.file_changed_signal.emit(self.sec)
            self.sleep(1)
            SW = GPIO.input(18)
            if SW == GPIO.HIGH :
             self.sec += 1
            if SW == GPIO.LOW :
             self.sec = 0
             GPIO.output(LED_G,GPIO.LOW)
             GPIO.output(LED_R,GPIO.LOW)

class WorkThread(QThread):
    # 自定義訊號物件。引數str就代表這個訊號可以傳一個字串
    changePixmap = pyqtSignal(QPixmap)
    
    def __int__(self):
        # 初始化函式
        super(WorkThread, self).__init__()
        
    def getframe(self):
        return self.frame


    def run(self):
        #重寫執行緒執行的run函式
        #觸發自定義訊號
        cap = cv2.VideoCapture(videoFile)

        while True:
            ret, self.frame = cap.read()
            rgbImage = cv2.cvtColor(self.frame, cv2.COLOR_BGR2RGB)
            convertToQtFormat = QImage(rgbImage.data, rgbImage.shape[1], rgbImage.shape[0], QImage.Format_RGB888)
            convertToQtFormat = QPixmap.fromImage(convertToQtFormat)
            p = convertToQtFormat.scaled(640, 480, Qt.KeepAspectRatio)
            self.changePixmap.emit(p)
     
        
    
if __name__=='__main__':
    app=QApplication(sys.argv)
    window=MainWindow()
    window.show()
    sys.exit(app.exec())
