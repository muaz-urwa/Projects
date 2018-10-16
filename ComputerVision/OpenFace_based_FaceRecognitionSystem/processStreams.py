import cv2
import numpy as np
import dlib
import time
import face_recognition
import pyodbc
import os
import pickle

#################


FPS = 8
faceGroupIdleThreshhold = 5
faceGroupThreshHold = 0.45
minFaceInstanceLength = 2
instanceDirectory = "Instances"
minFaceSize = 100

# Set rtsp conn string here
rtspConnectionString = ''

face_detector = dlib.get_frontal_face_detector()
capture = cv2.VideoCapture(rtspConnectionString)


class faceGroupInstance:   
    
    def __init__(self, time, images):
        self.faceImages = []
        self.faceTimes = []
        for i in range(len(images)):
            self.faceImages.append(images[i])
            self.faceTimes.append(time)
        self.startTime = time
        self.lastTime = time

    def addFaces(self, time, images):
        for i in range(len(images)):
            self.faceImages.append(images[i])
            self.faceTimes.append(time)
        self.lastTime = time

    def getIdleTime(self):
        return (time.time()-self.lastTime)

    def getFaceImages(self):
        return self.faceImages

    def getFaceTimes(self):
        return self.faceTimes      
        

class faceInstance:

    def __init__(self, time, image, enc):
        self.faceImages = []
        self.faceTimes = []
        self.faceEncodings = []
        self.faceImages.append(image)
        self.faceTimes.append(time)
        self.faceEncodings.append(enc)

    def getDistance(self, enc):
        dist = []        
        for i in range(len(self.faceEncodings)):
            dist.append(np.linalg.norm(np.array(self.faceEncodings[i])-np.array(enc)))
        return np.mean(np.array(dist))

    def addFace(self, time, image, enc):
        self.faceImages.append(image)
        self.faceTimes.append(time)
        self.faceEncodings.append(enc)

    def getLength(self):
        return len(self.faceImages)

    def getFaceImages(self):
        return self.faceImages

    def getFaceTime(self):
        return np.min(np.array(self.faceTimes))

    def getFaceTimes(self):
        return self.faceTimes

    def getEncodings(self):
        return self.faceEncodings
            



def cropFaces(frame, faces):
    croppedFaces = []
    height, width, channels = frame.shape
    for i, face_rect in enumerate(faces):
        cropImage = frame[max(face_rect.top(),0):min(face_rect.bottom(),height), max(face_rect.left(),0):min(face_rect.right(),width)]
        croppedFaces.append(cropImage)
    return croppedFaces

def cropFrame(frame):
    height, width, channels = frame.shape
    cropImage = frame[260:min(1440,height), max(510,0):min(1460,width)]
    return cropImage

def processFaceGroup(faceGroup):
    faceImages = faceGroup.getFaceImages()
    faceTimes = faceGroup.getFaceTimes()
    encodings = []
    faceInstances = []
    print("N of Faces:"+str(len(faceImages)))
    for i in range(len(faceImages)):
        print("Face:"+str(i))
        img = faceImages[i]
        img = img[:, :, ::-1]
        face_locations =[]
        face_locations.append(  (0, img.shape[1], img.shape[0], 0))
        enc = face_recognition.face_encodings(img,face_locations)
        encodings.append(enc)
        print("N of Instances:"+str(len(faceInstances)))
        if(len(faceInstances) > 0):
            distances = []
            for j in range(len(faceInstances)):
                distances.append(faceInstances[j].getDistance(enc))
            minDist = np.min(distances)
            minIndex = np.argmin(distances)
            print("minDist:"+str(minDist))
            if(minDist < faceGroupThreshHold):
                faceInstances[minIndex].addFace(faceTimes[i], faceImages[i], encodings[i])
            else:
                print("Create Face instance")
                face = faceInstance(faceTimes[i], faceImages[i], encodings[i])
                faceInstances.append(face)           
        else:
            print("Create Face instance")
            face = faceInstance(faceTimes[i], faceImages[i], encodings[i])
            faceInstances.append(face)
    print("N of Instances:"+str(len(faceInstances)))        
    faceInstances = [elem for elem in faceInstances if elem.getLength() > minFaceInstanceLength]
    print("N of filtered Instances:"+str(len(faceInstances)))
    return faceInstances


def saveFaceInstances(faceInstances):
    folderPaths = []
    for i in range(len(faceInstances)):
        folderName = str(len(os.listdir(instanceDirectory))+1)
        folderpath = instanceDirectory+"/"+folderName
        os.makedirs(folderpath)
        folderPaths.append(folderpath)
        images = faceInstances[i].getFaceImages()
        for j in range(len(images)):
            imageName = str(len(os.listdir(instanceDirectory+"/"+folderName))+1)+".png"
            fullname = instanceDirectory+"/"+folderName+"/"+imageName
            cv2.imwrite(fullname, images[j])
    return folderPaths

def storeFaceInstancesDb(faceInstances,folderPaths):
    # Connect to db
    cnxn = pyodbc.connect("Driver={SQL Server Native Client 11.0};"
                          "Server=localhost;"
                          "Database=FaceDb;"
                          "Trusted_Connection=yes;")
    cursor = cnxn.cursor()

    command = 'Select Count(*) AS N FROM InstanceTable'
    cursor.execute(command)
    instanceId = 1
    for row in cursor:
        instanceId=int(row.N)+1

    for i in range(len(faceInstances)):
        images = faceInstances[i].getFaceImages()
        times = faceInstances[i].getFaceTimes()
        encodings = faceInstances[i].getEncodings()
        facetime = faceInstances[i].getFaceTime()
        command = "Insert into InstanceTable(InstanceId,ImageCount,FolderPath,Time) values (?,?,?,?)"
        cursor.execute(command,instanceId,len(images),folderPaths[i],time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(facetime)))
        cnxn.commit()
        for j in range(len(images)):
            command = "Insert into ImageTable(InstanceId,Encoding,ImageId,Time,IsProcessed) values (?,?,?,?,?)"
            cursor.execute(command,instanceId,np.array(encodings[j]).tostring(),j+1,time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(times[j])),False)
            cnxn.commit()           
        instanceId += 1



def filterFacesbySize(faces):
    faces = [elem for elem in faces if ( elem.bottom()-elem.top() > minFaceSize and elem.right()-elem.left() > minFaceSize )]
    return faces

def showFaces(images):
    print("show Faces")
    for i in range(len(images)):
        cv2.imshow(str(i),images[i])


faceGroup = None
faceDetected = False
frameId = 0

while True:
    ret,frame = capture.read()    
    if ret and (frameId % (2) == 0 or faceDetected):
                print("frame:"+str(frameId))
                startTime = time.time()

                frame = cropFrame(frame)
                #cv2.imshow("frame",frame)
                # Convert the image from BGR color (which OpenCV uses) to RGB color (which face_recognition uses)
                #rgb_frame = frame[:, :, ::-1]
                #t0 = time.strftime('%Y-%m-%d %H:%M:%S')

                frameName = "frames"+"/"+time.strftime('%Y-%m-%d%H-%M-%S')+".png"
                #cv2.imwrite(frameName, frame)

                #Face Detection
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                detected_faces = face_detector(gray, 0)

                #print("Faces: "+str(len(detected_faces)))
                detected_faces = filterFacesbySize(detected_faces)
                print("Faces: "+str(len(detected_faces)))
                
                if len(detected_faces) > 0:

                    faceDetected = True                 
                    croppedFaces = cropFaces(frame, detected_faces)
                    
                    if(faceGroup == None):
                        faceGroup = faceGroupInstance(startTime,croppedFaces)
                    else:
                        faceGroup.addFaces( startTime, croppedFaces)

                else:
                    if(faceGroup != None):
                        idleTime = faceGroup.getIdleTime()
                        if (idleTime >faceGroupIdleThreshhold):
                            print("process facesgroup")
                            faceInstances = processFaceGroup(faceGroup)
                            
                            print("save faceInstances:"+str(len(faceInstances)))
                            if(len(faceInstances)>0):
                                folderPaths = saveFaceInstances(faceInstances)
                                print("store DB faceInstances:"+str(len(faceInstances)))
                                storeFaceInstancesDb(faceInstances,folderPaths)
                           
                            faceGroup = None
                    faceDetected = False
                print("time: "+str(time.time()-startTime)) 
                    
                                       
    frameId+=1
    if cv2.waitKey(1) & 0xFF == ord('q'):
          break







        

        
