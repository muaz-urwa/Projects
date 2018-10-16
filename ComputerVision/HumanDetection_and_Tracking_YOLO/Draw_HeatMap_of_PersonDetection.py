import cv2
from darkflow.net.build import TFNet
import matplotlib.pyplot as plt
import numpy as np
import time
import Person

#config InlineBackend.figure_format = 'svg'

# set input video file

inputFile = ''
inputBaseImage = ''

#thresh-hold
threshHold = 0.7

#model parameters
options = {
    'model': 'cfg/yolo.cfg',
    'load': 'bin/yolo.weights',
    'threshhold': 0.15
}

#initialize model
tfnet = TFNet(options)


#video feed
capture = cv2.VideoCapture(inputFile)

#initialize persons
persons = []
max_p_age = 5
pid = 1

def cal_distance(p1,p2):
        return np.sqrt( (p2[0] - p1[0])**2 + (p2[1] - p1[1])**2 )

def shift_point(point,shift):
        return ( point[0] + shift[0], point[1] + shift[1] )

def cal_mid(p1,p2):
        return ((p1[0]+ p2[0])/2 , (p1[1]+ p2[1])/2)

def cal_score(tl1, br1, tl2, br2):
        displacement = cal_distance(tl1, tl2) 
        diag1 = cal_distance(tl1, br1)
        diag2 = cal_distance(tl2, br2) 
        sizeDiff = abs(diag2 - diag1)
        score = displacement + sizeDiff
        score = 1 / (1 + score)
        print('Score: '+str(score))
        return score



def add_detections(detections, img):
        for d in detections:
                height, width, _ = img.shape
                
                tl = d.getTl()
                br = d.getBr()
                mp = cal_mid(tl,br)
                mpX = int(mp[0])
                mpY = int(mp[1])
                
                spread = 20
                 
                s = list(range(2*spread+1))
                for t in range(len(s)):
                        s[t]-=spread
                        
                for y in range(len(s)):
                        for x in range(len(s)):
                                if mpY+y >=0 and mpY+y < height and mpX+x >=0 and mpX+x < width:
                                        img[mpY+y][mpX+x] += 1
                 


def scale_image(img):
        height, width,_ = img.shape
        maximum = np.max(img)
        minimum = np.min(img)
        for y in range(height):
                for x in range(width):
                        img[y][x] = int( (img[y][x]/maximum) * 255 )
                        



class Detection:
        def __init__(self, tl, br, cfd):
                self.tl = tl
                self.br = br
                self.confidence = cfd
                self.found= False
        def getTl(self):
                return self.tl
        def getBr(self):
                return self.br
        def getCfd(self):
                return self.confidence
        def setFound(self):
                self.found= True
        def isFound(self):
                return self.found

              
                                              
frameID = 0               


while(capture.isOpened()):
        stime = time.time()
        ret, frame = capture.read()
        frameID += 1


        detections = []
        if ret:
                height, width, channels = frame.shape
                if frameID ==1:
                        blank_image = np.zeros((height,width,1), np.uint8)
                result = tfnet.return_predict(frame)
                results = [t for t in result if t['label'] == 'person' and t['confidence']>threshHold]
                for x in results:
                        tl = (x['topleft']['x'],x['topleft']['y'])
                        br = (x['bottomright']['x'],x['bottomright']['y'])
                        cfd = (x['confidence'])
                        frame = cv2.rectangle(frame,tl,br,(0,255,0),7)
                        detections.append(Detection(tl, br, cfd))

                add_detections(detections, blank_image)

                cv2.imshow('frame', frame)
                if cv2.waitKey(1) & 0XFF == ord('q'):
                        break
        else:
                capture.release()

scale_image(blank_image)

colorimg = cv2.applyColorMap(blank_image, cv2.COLORMAP_JET)
cv2.imshow('mapColor', colorimg)
cv2.imshow('map', blank_image)
cv2.imwrite('heatmap.png',colorimg)

baseImg = cv2.imread(inputBaseImage,1)

fin = cv2.addWeighted(colorimg, 0.7, baseImg, 0.3, 0)
cv2.imshow('mapSI', fin)
cv2.imwrite('HeatmapSuperImposed.png',fin)

cv2.waitKey(0)
cv2.destroyAllWindows()

