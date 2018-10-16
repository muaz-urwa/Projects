import cv2
import numpy as np
import dlib
import time
#import face_recognition
import pyodbc
import os
import pickle
from shutil import copyfile

#################

distanceThreshhold = 0.52
groupDirectory = "groups/"

def compareFolders(enc1, enc2):

    dist=[]
    for i in range(len(enc1)):
        for j in range(len(enc2)):
            dist.append(np.linalg.norm(np.array(enc1[i])-np.array(enc2[j])))
  
    dist = np.array(dist)

    if(len(dist) == 0):
        return (5, 5)

    return (np.mean(dist), np.min(dist))



class faceGroupClass:   
    
    def __init__(self, faceId,encodings,folder):
        self.encodings = encodings
        self.faceId = faceId
        self.folder = folder

    def addEncoding(self, enc):
        self.encodings.append(enc)

    def getFaceEncodings(self):
        return self.encodings

    def getFaceId(self):
        return self.faceId

    def getFolder(self):
        return self.folder 

class faceInstanceClass:   
    
    def __init__(self, instanceId,encodings,folder,times):
        self.encodings = encodings
        self.instanceId = instanceId
        self.folder = folder
        self.times=times

    def addEncoding(self, enc):
        self.encodings.append(enc)

    def getFaceEncodings(self):
        return self.encodings

    def getInstanceId(self):
        return self.instanceId

    def getFolder(self):
        return self.folder

    def getTimes(self):
        return self.times 


def getFaceGroupsDb():
    # Connect to db
    cnxn = pyodbc.connect("Driver={SQL Server Native Client 11.0};"
                          "Server=localhost;"
                          "Database=FaceDb;"
                          "Trusted_Connection=yes;")
    cursor = cnxn.cursor()

    command = 'Select PersonId,Encoding,Folder FROM PeopleTable'
    cursor.execute(command)
    faceIds = []
    encodings = []
    folders = []
    for row in cursor:
        faceIds.append(int(row.PersonId))
        encodings.append(np.fromstring(row.Encoding))
        folders.append(row.Folder)

    uniqueFaceids = list(set(faceIds))

    faceGroups = []
    for i in range(len(uniqueFaceids)):
        FaceId = uniqueFaceids[i]
        faceEncodings = []
        folder = None
        for j in range(len(faceIds)):
            if(faceIds[j]==FaceId):
                faceEncodings.append(encodings[j])
                folder = folders[j]
        #faceEncodings = [elem for elem in encodings if (faceIds[i]==FaceId  )]
        faceGroup = faceGroupClass(FaceId,faceEncodings,folder)
        faceGroups.append(faceGroup)
    cursor.close()
    del cursor
    cnxn.close()
    return faceGroups

def getFaceInstancesDb():
    # Connect to db
    cnxn = pyodbc.connect("Driver={SQL Server Native Client 11.0};"
                          "Server=localhost;"
                          "Database=FaceDb;"
                          "Trusted_Connection=yes;")
    cursor = cnxn.cursor()

    command = 'Select InstanceId,Encoding,Time FROM ImageTable Where IsProcessed = 0'
    cursor.execute(command)
    InstanceIds = []
    encodings = []
    Times = []
    for row in cursor:
        InstanceIds.append(int(row.InstanceId))
        encodings.append(np.fromstring(row.Encoding))
        Times.append(row.Time)

    command = '  Select Distinct Ins.InstanceId,Ins.FolderPath from InstanceTable Ins inner join ImageTable Img ON Ins.InstanceId=Img.InstanceId Where Img.IsProcessed=0'
    cursor.execute(command)
    UniqueInstanceIds = []
    paths = []
    for row in cursor:
        UniqueInstanceIds.append(int(row.InstanceId))
        paths.append(row.FolderPath)
    

    faceInstances = []
    for i in range(len(UniqueInstanceIds)):
        InstanceId = UniqueInstanceIds[i]
        path = paths[i]
        faceEncodings = []
        faceTimes = []
        for j in range(len(InstanceIds)):
            if(InstanceIds[j]==InstanceId):
                faceEncodings.append(encodings[j])
                faceTimes.append(Times[j])
        faceInstance = faceInstanceClass(InstanceId,faceEncodings,path,faceTimes)
        faceInstances.append(faceInstance)

    cursor.close()
    del cursor
    cnxn.close()
    
    return faceInstances

def copyContent(fromFol, ToFol):  
    files = os.listdir(fromFol)
    for i in range(len(files)):
        src = fromFol+"/"+files[i]
        dst = ToFol+"/"+str(len(os.listdir(ToFol))+1)+".png"
        copyfile(src, dst)

def savePeopleDB(faceId, faceInstance, folder):
    #folder = faceInstance.getFolder()
    cnxn = pyodbc.connect("Driver={SQL Server Native Client 11.0};"
                          "Server=localhost;"
                          "Database=FaceDb;"
                          "Trusted_Connection=yes;")
    cursor = cnxn.cursor()
    Encodings = faceInstance.getFaceEncodings()
    Times = faceInstance.getTimes()

    for i in range(len(Encodings)):
        command = "Insert into PeopleTable(PersonId,Encoding,Time,Folder) values (?,?,?,?)"
        cursor.execute(command,faceId,Encodings[i].tostring(),Times[i],folder)
        cnxn.commit()

    cursor.close()
    del cursor
    cnxn.close()

def generatefaceIdDB():
    cnxn = pyodbc.connect("Driver={SQL Server Native Client 11.0};"
                          "Server=localhost;"
                          "Database=FaceDb;"
                          "Trusted_Connection=yes;")
    cursor = cnxn.cursor()

    command = 'Select ISNULL(MAX(PersonId), 0) AS N FROM PeopleTable'
    cursor.execute(command)
    faceId = 1  
    for row in cursor:
        faceId=int(row.N)+1
    cursor.close()
    del cursor
    cnxn.close()
    return faceId

def createFolder(baseDir,folder):
    directory = baseDir+str(folder)
    if not os.path.exists(directory):
        os.makedirs(directory)
    else:
        print("direcotry already exists!")
    return directory


def markProcessedDB(faceInstances):
    cnxn = pyodbc.connect("Driver={SQL Server Native Client 11.0};"
                          "Server=localhost;"
                          "Database=FaceDb;"
                          "Trusted_Connection=yes;")
    cursor = cnxn.cursor()
    for i in range(len(faceInstances)):
        faceId = faceInstances[i].getInstanceId()
        command = "Update ImageTable Set IsProcessed = 1 WHERE InstanceId = ?"
        cursor.execute(command,faceId)
        cnxn.commit()
    cursor.close()
    del cursor
    cnxn.close()
    
while(True):
    print("Getting Face Instances...")
    faceInstances = getFaceInstancesDb()
    print("Getting Face Groups...")
    faceGroups = getFaceGroupsDb()
    for i in range(len(faceInstances)):
        print("Processing Instance "+str(i))
        distances = []
        for j in range(len(faceGroups)):
            avgDist,minDist = compareFolders(faceInstances[i].getFaceEncodings(), faceGroups[j].getFaceEncodings())
            distances.append(avgDist)
        minDist = 5
        minIndex = -1
        if(len(distances)>0):
            minDist = np.min(np.array(distances))
            minIndex = np.argmin(np.array(distances))
        if(minDist < distanceThreshhold):            
            facegroup = faceGroups[minIndex]
            faceId = facegroup.getFaceId()            
            fromFol = faceInstances[i].getFolder()
            ToFol = facegroup.getFolder()
            savePeopleDB(faceId,faceInstances[i],ToFol)
            copyContent(fromFol, ToFol)
            print("Instance: "+str(fromFol)+" merged with group: "+str(ToFol))
            enc = faceInstances[i].getFaceEncodings()
            for j in range(len(enc)):
                facegroup.addEncoding(enc[j])
        else :
            faceId = generatefaceIdDB()
            directory = createFolder(groupDirectory,faceId)           
            savePeopleDB(faceId,faceInstances[i],directory)
            fromFol = faceInstances[i].getFolder()
            ToFol = directory
            copyContent(fromFol, ToFol)
            print("Group: "+str(directory)+" created.")
            enc = faceInstances[i].getFaceEncodings()
            faceGroup = faceGroupClass(faceId,enc,directory)
            faceGroups.append(faceGroup)
    markProcessedDB(faceInstances)
    print("Sleep for a min.")
    time.sleep(1*60)

