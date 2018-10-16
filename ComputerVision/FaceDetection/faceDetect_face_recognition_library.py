import cv2
import numpy as np
import time
import face_recognition

# Set your rtsp conn string here
rtspConnectionString = '' 

capture = cv2.VideoCapture(rtspConnectionString)


while True:
	ret,frame = capture.read()
	if ret:

          t0 = time.time()
          
          
          detected_faces = face_recognition.face_locations(frame)
        
          
          print("Face Detections Frec:  %s seconds " % (time.time() - t0))
          t1 = time.time()
          
          # Loop through each face we found in the image
          for i, face_rect in enumerate(detected_faces):

                  # Draw a box around each face we found
                  #win.add_overlay(face_rect)
                  cv2.rectangle(frame, (face_rect[3], face_rect[0]), (face_rect[1], face_rect[2]), (0, 0, 255), 2)
          
          height , width , layers =  frame.shape
          new_h=int(height/2)
          new_w=int(width/2)
          resize = cv2.resize(frame, (new_w, new_h))
          #win.set_image(resize)
          cv2.imshow('frame',resize)
	else:
          break
	if cv2.waitKey(1) & 0xFF == ord('q'):
          break
        
