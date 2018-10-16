import cv2
import numpy as np

# Replace following with correct credentials and network information
username = 'USERNAME'
password = 'Pass'
ipAdress = '10.10.1.100'
port = '554'

#rtsp connection string
rtspConn = "rtsp://"+username+":"+password+"@"+ipAdress+":"+port

#
capture = cv2.VideoCapture(camConn)

while True:
	ret,frame = capture.read()
	if ret:
          height , width , layers =  frame.shape                   
          cv2.imshow('frame',frame)
	if cv2.waitKey(1) & 0xFF == ord('q'):
          break
        
