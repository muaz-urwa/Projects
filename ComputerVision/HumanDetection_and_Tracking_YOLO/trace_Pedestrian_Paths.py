import cv2
from darkflow.net.build import TFNet
import matplotlib.pyplot as plt
import numpy as np
import time
import Person
import random

#config InlineBackend.figure_format = 'svg'

#thresh-hold
threshHold = 0.1

#model parameters
options = {
    'model': 'cfg/yolo.cfg',
    'load': 'bin/yolo.weights',
    'threshhold': 0.15
}

#initialize model
tfnet = TFNet(options)


#video feed
capture = cv2.VideoCapture('s5.avi')

#initialize persons
persons = []
max_p_age = 5
pid = 1
offset_threshhold = 0.00001
offset_threshhold2 = 0.4

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


def find_person(tl, br):     
        maxScore = 0
        score = 0
        for p in persons:
                dist = cal_distance(p.getMid(), cal_mid(tl,br))
                if dist < 40 :
                        score = 1/(1+dist)
                        if score > maxScore:
                                maxScore = score
                                existingPerson = p
        if(maxScore > 0):
                return (True , existingPerson)
        else:               
                return (False , None)


#if(tl[0] > p.getTl()[0] and tl[0] < p.getBr()[0] and tl[1] > p.getTl()[1] and tl[1] < p.getBr()[1]
#                or p.getTl()[0] > tl[0] and p.getTl()[0] < br[0] and p.getTl()[1] > tl[1] and p.getTl()[1] < br[1]):
      

def find_all_persons(detections, frame):
        global pid
        for p in persons:
                if p.getDone() == False:
                        maxScore = 0
                        score = 0
                        for d in detections:
                                if d.isFound() == False:                                
                                        tl = d.getTl()
                                        br = d.getBr()
                                        cfd = d.getCfd()
                                        m_offset = cal_distance(p.getMid(), cal_mid(tl,br))
                                        tl_offset = cal_distance(p.getTl(), tl)
                                        br_offset = cal_distance(p.getBr(), br)
                                        th = np.sqrt(p.getArea())* offset_threshhold
                                        if (m_offset < th or tl_offset < th or br_offset < th):
                                                score = 1/(1+m_offset+tl_offset+br_offset)
                                                if score > maxScore:
                                                        maxScore = score
                                                        det = d
                        #print(str(maxScore))
                        if(maxScore <= 0):
                                for d in detections:
                                        if d.isFound() == False:                                
                                                tl = d.getTl()
                                                br = d.getBr()
                                                cfd = d.getCfd()
                                                m_offset = cal_distance(shift_point(p.getMid(),p.getPredictedOffset(frame)), cal_mid(tl,br))
                                                tl_offset = cal_distance(shift_point(p.getTl(),p.getPredictedOffset(frame)), tl)
                                                br_offset = cal_distance(shift_point(p.getBr(),p.getPredictedOffset(frame)), br)
                                                th = np.sqrt(p.getArea())* offset_threshhold2
                                                if (m_offset < th or tl_offset < th or br_offset < th):
                                                        score = 1/(1+m_offset+tl_offset+br_offset)
                                                        if score > maxScore:
                                                                maxScore = score
                                                                det = d
                        
                        if(maxScore > 0):
                                p.updateCoords(det.getTl(), det.getBr(), frame)
                                det.setFound()
                        else:
                                p.age_one()
        for d in detections:
                        if d.isFound()== False and d.getCfd() > 0.7:
                                p = Person.MyPerson(pid,d.getTl(), d.getBr(), frame)
                                persons.append(p)
                                pid += 1 
                                


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


def printPersons():
        print('pid: '+str(pid))
        for p in persons:
                print('top-left: '+str(p.getTl())+'top-right:'+str(p.getBr()))

                
def print_paths(image):
        for p in persons:
                if len(p.getTracks()) > 16 :
                        temp = p.getTracks()[0]
                        a = random.randint(0,254)
                        b = random.randint(0,254)
                        c = random.randint(0,254)
                        cv2.putText(image, str(p.getId()), (int(temp[0]),int(temp[1])), cv2.FONT_HERSHEY_COMPLEX, 1, (a,b,c), 8)
                        for point in p.getTracks():
                                cv2.line(image,(int(temp[0]),int(temp[1])),(int(point[0]),int(point[1])),(a,b,c),3) # draw line between former and present pixel
                                temp = point
                                cv2.imshow('path', image)
                                cv2.waitKey(100)
        cv2.imwrite('path.png',image)


def draw_people(image):
        frame = image
        for p in persons:
                frame = cv2.rectangle(image,p.getTl(),p.getBr(),(0,255,0),7)
                cv2.putText(frame, str(p.getId()), (int(p.getMid()[0]),int(p.getMid()[1])), cv2.FONT_HERSHEY_COMPLEX, 1, (255,0,0), 8)
        return frame
                
                                                            
                                              
frameID = 0               

while(capture.isOpened()):
        stime = time.time()
        ret, frame = capture.read()
        frameID += 1

        

        printPersons()
        
        #cv2.waitKey(0)

        detections = []
        if ret:
                height, width, channels = frame.shape
                result = tfnet.return_predict(frame)
                results = [t for t in result if t['label'] == 'person' and t['confidence']>threshHold]
                for x in results:
                        tl = (x['topleft']['x'],x['topleft']['y'])
                        br = (x['bottomright']['x'],x['bottomright']['y'])
                        cfd = (x['confidence'])
                        #frame = cv2.rectangle(frame,tl,br,(0,255,0),7)
                        detections.append(Detection(tl, br, cfd))
                        #found,p = find_person(tl, br)
                        #print('box#####  tl: '+str(tl)+' br: '+str(br)+' isFound: '+str(found))
                        #if found:
                        #        p.updateCoords(tl, br, frameID)

                        #else:
                        #        p = Person.MyPerson(pid,tl,br,frameID, max_p_age)
                        #        persons.append(p)
                        #        pid += 1 

                        #for i in persons:

                
                find_all_persons(detections, frameID)

                frame = draw_people(frame)

                cv2.imshow('frame', frame)
                if cv2.waitKey(1) & 0XFF == ord('q'):
                        break
        else:
                capture.release()
                #height, width, channels = frame.shape
                #blank_image = np.zeros((height,width,channels), np.uint8)
                #cv2.imshow('path', blank_image)
                #print_paths(blank_image)
                #cv2.waitkey(0)
                #cv2.destroyAllWindows()


blank_image = np.zeros((height,width,channels), np.uint8)
cv2.imshow('path', blank_image)
print_paths(blank_image)

baseImg = cv2.imread('s5Pic.png',1)

fin = cv2.addWeighted(blank_image, 0.6, baseImg, 0.4, 0)
cv2.imshow('pathSI', fin)
cv2.imwrite('pathSI.png',fin)

cv2.waitKey(0)
cv2.waitKey(0)
cv2.destroyAllWindows()

