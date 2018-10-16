import cv2
from darkflow.net.build import TFNet
import matplotlib.pyplot as plt
import numpy as np
import time
#import Person
import random
import pyodbc


FPS = 8
ExperimentId = 'test1'
#ROI_TL = 
#ROI_BR =


#####################
inputVideoPath = 'videos/overHead.mp4'
outputVideoPath = 'videos/output_overHead.avi'


#video feed
capture = cv2.VideoCapture(inputVideoPath)

#video output
frame_width = int(capture.get(3))
frame_height = int(capture.get(4))
out = cv2.VideoWriter(outputVideoPath,cv2.VideoWriter_fourcc('M','J','P','G'), 4, (frame_width,frame_height))

frame_tl = (50,100)
frame_br = (frame_width-50,frame_height-100)

active_tl = (120,120)
active_br = (frame_width-120,frame_height-120)

############### Utility Functions ######################
def cal_distance(p1,p2):
        return np.sqrt( (p2[0] - p1[0])**2 + (p2[1] - p1[1])**2 )

def shift_point(point,shift):
        return ( point[0] + shift[0], point[1] + shift[1] )

def cal_mid(p1,p2):
        return ((p1[0]+ p2[0])/2 , (p1[1]+ p2[1])/2)

def getArea(tl,br):
        return(abs((br[0]-tl[0]) * (br[1]-tl[1])))

def minMagnitude(p1,p2):
        p1_dist = np.sqrt( (p1[0])**2 + (p1[1])**2 )
        p2_dist = np.sqrt( (p2[0])**2 + (p2[1])**2 )
        if(p1_dist < p2_dist):
            return (p1)
        else: 
            return (p2)

def draw_people(image, persons):
        frame = image
        for p in persons:
                if(p.IsActive()):
                        color = (0,255,0)
                else :
                        color = (0,0,255)
                frame = cv2.rectangle(image,p.getTl(),p.getBr(),color,7)
                cv2.putText(frame, str(p.getPid()), (int(p.getMid()[0]),int(p.getMid()[1])), cv2.FONT_HERSHEY_COMPLEX, 1, (255,0,0), 8)
        return frame

def draw_region(image):
        frame = image
        frame = cv2.rectangle(image,frame_tl,frame_br,(255,0,0),3)
        #frame = cv2.rectangle(image,active_tl,active_br,(255,0,0),2)
        return frame


def IsInROI(mp):
        return(mp[0] > frame_tl[0] and mp[0] < frame_br[0] and mp[1] > frame_tl[1] and mp[1] < frame_br[1])


############# Classes ###########################

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


class MyPerson:
    tracks = []
    def __init__(self, pid, tl, br):
        self.pid = pid
        self.tl = tl
        self.br = br
        self.tl_track = []
        self.br_track = []
        self.tl_track.append(tl)
        self.br_track.append(br)
        self.offsets = []
        #self.R = randint(0,255)
        #self.G = randint(0,255)
        #self.B = randint(0,255)
        self.done = False
        self.state = '0'
        self.frameCount = 0
        self.frameLost = 0
        self.dir = None
        self.areas = []
        self.areas.append(getArea(tl,br))
        self.totalDistance = 0
        self.dffc = []
        self.inbound = False
        self.outbound = False
        self.active = False

    def setDirection(self,tl,br):
        frame_center = (frame_width,frame_height)
        mid_point = cal_mid(tl,br)
        self.dffc.append(cal_distance(mid_point,frame_center))
        if(len(self.dffc) >= 5):
                if(self.dffc[len(self.dffc)-1]>self.dffc[len(self.dffc)-5]):
                        self.inbound = True
                else:
                        self.outbound=True
    def activate(self):
        self.active = True
    def IsActive(self):
        return(self.active)
    def getRGB(self):
        return (self.R,self.G,self.B)
    def getPid(self):
        return (self.pid)
    def setPid(self,pid):
        self.pid = pid
    def getTracks(self):
        return self.tracks
    def getFrameLost(self):
        return self.frameLost
    def getState(self):
        return self.state
    def getFrameCount(self):
        return self.frameCount
    def getFrameLost(self):
        return self.frameLost
    def getDir(self):
        return self.dir
    def getTl(self):
        return self.tl
    def getBr(self):
        return self.br
    def IsInbound(self):
        return self.inbound
    def IsOutbound(self):
        return self.outbound
    def getMid(self):
        return ((self.tl[0]+ self.br[0])/2 , (self.tl[1]+ self.br[1])/2)
##    def getArea(self):
##        return np.mean(self.areas)
    def getArea(self):
        return np.max(self.areas)

    def setPosition(self, tl, br):
        self.frameCount += 1
        self.frameLost = 0
        self.setOffsetMid( self.tl, self.br, tl, br)
        self.tl = tl
        self.br = br
        self.tl_track.append(tl)
        self.br_track.append(br)      
        self.areas.append(getArea(tl,br))       
        #self.setTotalDistance()
        self.setDirection(tl,br)

    def setOffsetMin(self, old_tl, old_br, new_tl, new_br):
        tl_offset = (tl[0]-self.tl[0],tl[1]-self.tl[1])
        br_offset = (br[0]-self.br[0],br[1]-self.br[1])
        self.offsets.append(minMagnitude(tl_offset, br_offset))

    def setOffsetMid(self, old_tl, old_br, new_tl, new_br):
        old_mid = cal_mid(old_tl,old_br)
        new_mid = cal_mid(new_tl,new_br)
        mid_offset = (new_mid[0]-old_mid[0],new_mid[1]-old_mid[1])
        self.offsets.append(mid_offset)
    
    def updatePosition(self, tl, br):
        previous_tl = self.tl_track[len(self.tl_track)-2]
        previous_br = self.br_track[len(self.br_track)-2]
        self.setOffsetMid( self.tl, self.br, tl, br)
        self.tl = tl
        self.br = br
        self.tl_track[len(self.tl_track)-1] = tl
        self.br_track[len(self.br_track)-1] = br
        self.dffc.pop()
        self.setDirection(tl,br)
        #self.offsets[len(self.offsets)-1] = minMagnitude(tl_offset, br_offset)

    def revertPosition(self):
        tl = self.tl_track[len(self.tl_track)-2]
        br = self.br_track[len(self.br_track)-2]
        previous_tl = self.tl_track[len(self.tl_track)-2]
        previous_br = self.br_track[len(self.br_track)-2]
        del self.offsets[len(self.offsets)-1]
        self.setOffsetMid( previous_tl, previous_br, tl, br)
        self.tl = tl
        self.br = br
        self.tl_track[len(self.tl_track)-1] = tl
        self.br_track[len(self.br_track)-1] = br 
        
    def setDone(self):
        self.done = True
    def getDone(self):
        return self.done
    def getMissedFrames(self):
        return self.frameLost
    def getTrackLength(self):
        return len(self.tl_track)
    def projectMotion(self,f):
        offset = self.getPredictedOffset()
        p_tl = shift_point(self.tl,offset)
        p_br = shift_point(self.br,offset)
        setPosition(self, tl, br)        
    def getPredictedOffset(self,hist):
        offsetLength = len(self.offsets)
        if offsetLength == 0:
                return (0,0)
        if(hist > offsetLength):
            hist = offsetLength
        deltaX = 0
        deltaY = 0
        for i in range(hist):
            deltaX += self.offsets[offsetLength-1-i][0]
            deltaY += self.offsets[offsetLength-1-i][1]
        return (int((deltaX/hist)), int((deltaY/hist)))
    def setTotalDistance(self):
        l = self.getTrackLength()
        p2 = self.tracks[l-1]
        p1 = self.tracks[l-2]
        d = np.sqrt( (p2[0] - p1[0])**2 + (p2[1] - p1[1])**2 )
        self.totalDistance += d
    def timedOut(self):
        return self.done
    def missedFrame(self):
        self.frameLost +=1
        return True

############### Functions ######################

def PersonDetectorYolo(frame):
        detections = []
        result = tfnet.return_predict(frame)
        results = [t for t in result if t['label'] == 'person' and t['confidence']>detectionConfidenceThreshHold]
        for x in results:
                tl = (x['topleft']['x'],x['topleft']['y'])
                br = (x['bottomright']['x'],x['bottomright']['y'])
                cfd = (x['confidence'])
                detections.append(Detection(tl, br, cfd))
        return detections

def TrackPersons(personList, hist):
        for person in personList:
                shift = person.getPredictedOffset(hist)
                new_Tl = shift_point(person.getTl(),shift) 
                new_Br = shift_point(person.getBr(),shift)
                person.setPosition(new_Tl, new_Br)

def FindExistingPeople(detections,CurrentlyTrackedPeople):
        UndetectedPeople = []
        for p in CurrentlyTrackedPeople:
                                                       
                maxScore = 0
                score = 0
                overlap = False
                p_area = p.getArea()
                p_mp = cal_mid(p.getTl(), p.getBr())
                
                for d in detections:
                        if d.isFound() == False :                                
                                d_tl = d.getTl()
                                d_br = d.getBr()
                                d_mp = cal_mid(d_tl,d_br)
                                cfd = d.getCfd()
                                
                                mp_offset = cal_distance(p_mp, d_mp)
                                tl_offset = cal_distance(p.getTl(), d_tl)
                                br_offset = cal_distance(p.getBr(), d_br)                               
                                
                                score = scoreMinOffset(tl_offset, br_offset, p_area)
                                if score > maxScore:
                                        maxScore = score
                                        maxDetection = d
                if(maxScore > 0):
                                p.updatePosition(maxDetection.getTl(), maxDetection.getBr())
                                maxDetection.setFound()
                else:
                        UndetectedPeople.append(p)

        UntrackedDetections = [t for t in detections if t.isFound() == False]
        return (UndetectedPeople, UntrackedDetections)

def ProcessUntrackedDetections(CurrentlyTrackedPeople,UntrackedDetections):
        global pid
        for d in UntrackedDetections:
                        if d.getCfd() > 0.7 and IsInROI(cal_mid(d.getTl(), d.getBr())):# (v3) and not IsInActiveRegionMp(cal_mid(d.getTl(), d.getBr())): ## and IsEnteringFrame(d.getTl(), d.getBr())
                                person = MyPerson(pid, d.getTl(), d.getBr())
                                CurrentlyTrackedPeople.append(person)
                                pid += 1 

def ProcessUndetectedPeople(CurrentlyTrackedPeople,UndetectedPeople):
        for p in UndetectedPeople:
                p.missedFrame()
                #p.revertPosition()   
                if p.getMissedFrames() > UndetectedFramesThreshhold:
                        CurrentlyTrackedPeople.remove(p)
                        SavePersonTrack(p)

                                
def ProcessExitingPeople(CurrentlyTrackedPeople):
        for p in CurrentlyTrackedPeople:
                if  IsInROI(cal_mid(p.getTl(), p.getBr()))==False:
                        CurrentlyTrackedPeople.remove(p)
                        SavePersonTrack(p)                     
                      
def SavePersonTrack(person):
        print (str(person.getPid())+" saved!")
        time = int(person.getFrameCount()/FPS)
        # Connect to db
        cnxn = pyodbc.connect("Driver={SQL Server Native Client 11.0};"
                          "Server=localhost;"
                          "Database=DwellDb;"
                          "Trusted_Connection=yes;")
        cursor = cnxn.cursor()

        command = "Insert into ExperimentOne(ExpID,PersonID,Time) values (?,?,?)"
        cursor.execute(command,ExperimentId,person.getPid(),time)
        cnxn.commit()
        

def TrackByDetection(detections,CurrentlyTrackedPeople):
        UndetectedPeople, UntrackedDetections = FindExistingPeople(detections,CurrentlyTrackedPeople)
        ProcessUntrackedDetections(CurrentlyTrackedPeople,UntrackedDetections)
        #ProcessInactivePeople(CurrentlyTrackedPeople)
        ProcessExitingPeople(CurrentlyTrackedPeople)
        ProcessUndetectedPeople(CurrentlyTrackedPeople,UndetectedPeople)

def scoreMinOffset(tl_offset, br_offset, p_area):
        offset = min(tl_offset, br_offset)
        threshHold = np.sqrt(p_area)* offset_threshhold
        if (offset < threshHold):
                score = 1/(1 + offset + 0.1 * max(tl_offset, br_offset))
        else:
                score = 0
        return score

def scoreTwoOffset(tl_offset, br_offset, p_area):
        threshHold = np.sqrt(p_area)* offset_threshhold
        if (tl_offset < threshHold or br_offset < threshHold):
                score = 1/(1 + tl_offset + br_offset)
        else:
                score = 0
        return score

def scoreThreeOffset(tl_offset, br_offset, mp_offset, p_area):       
        threshHold = np.sqrt(p_area)* offset_threshhold
        if (mp_offset < threshHold or tl_offset < threshHold or br_offset < threshHold):
                score = 1/(1 + tl_offset + br_offset + mp_offset)
        else:
                score = 0
        return score

#model parameters
options = {
    'model': 'cfg/yolo.cfg',
    'load': 'bin/yolo.weights',
    'threshhold': 0.15
}


hist = 8
skipFrames = 1
detectionConfidenceThreshHold = 0.05
offset_threshhold = 0.5
creationConfidenceThreshhold = 0.7
pid = 1
UndetectedFramesThreshhold = FPS


#initialize model
tfnet = TFNet(options)

############### Variables ###############
frameID = -1
CurrentlyTrackedPeople = []
#CandidatePeople = []
#KnownfalsePositives = []
#Employees = []




while(capture.isOpened()):
        frameID += 1
        #print(frameID)
        stime = time.time()
        ret, frame = capture.read()
        detectionFrame = (frameID % (skipFrames+1) == 0)
        
        if ret:
                if(detectionFrame):
                        detections = PersonDetectorYolo(frame)
                        TrackPersons(CurrentlyTrackedPeople, hist)
                        TrackByDetection(detections,CurrentlyTrackedPeople)
                else:
                        TrackPersons(CurrentlyTrackedPeople, hist)
                draw_people(frame,CurrentlyTrackedPeople)
                draw_region(frame)
                out.write(frame)
                cv2.imshow('frame', frame)
                cv2.waitKey(1)
        else:
                capture.release()
