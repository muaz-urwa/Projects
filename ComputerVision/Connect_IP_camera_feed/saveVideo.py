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

# Video write FPS
fps = 20 
outputVideoPath = 'Output.avi'

#video output
frame = capture.read()
height , width , layers =  frame.shape
out = cv2.VideoWriter(outputVideoPath,cv2.VideoWriter_fourcc('M','J','P','G'), fps, (width,height))


while True:
	ret,frame = capture.read()
	if ret:          
          out.write(frame)
          cv2.imshow('frame',frame)
	if cv2.waitKey(1) & 0xFF == ord('q'):
          break
        
