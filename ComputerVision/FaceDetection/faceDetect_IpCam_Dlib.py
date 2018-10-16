import cv2
import numpy as np
import dlib
import time

# Set your rtsp conn string here
rtspConnectionString = '' 

face_detector = dlib.get_frontal_face_detector()
capture = cv2.VideoCapture(rtspConnectionString)
#win = dlib.image_window()


while True:
	ret,frame = capture.read()
	if ret:

          t0 = time.time()
          gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
          detected_faces = face_detector(gray, 0)
          #detected_faces, scores, idx = face_detector.run(frame, 0, 0)
          
          print("Dlib face Detection:  %s seconds " % (time.time() - t0))
          t1 = time.time()
          
          # Loop through each face we found in the image
          for i, face_rect in enumerate(detected_faces):

                  # Draw a box around each face we found
                  #win.add_overlay(face_rect)
                  cv2.rectangle(frame, (face_rect.left(), face_rect.top()), (face_rect.right(), face_rect.bottom()), (0, 0, 255), 2)
          
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
        
