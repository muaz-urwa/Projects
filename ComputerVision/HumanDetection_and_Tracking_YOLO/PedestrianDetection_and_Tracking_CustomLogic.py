import cv2
from darkflow.net.build import TFNet
import matplotlib.pyplot as plt
import numpy as np
import time
import Person
import random
from matplotlib.widgets import RectangleSelector
import matplotlib.patches as patches

#config InlineBackend.figure_format = 'svg'

#thresh-hold
threshHold = 0.05

#model parameters
options = {
    'model': 'cfg/yolo.cfg',
    'load': 'bin/yolo.weights',
    'threshhold': 0.15
}

#initialize model
tfnet = TFNet(options)


#video feed
capture = cv2.VideoCapture('videos/s4.avi')

#initialize persons
persons = []
rid = 1
regions = []
max_p_age = 5
pid = 1
offset_threshhold = 0.3
closeProgram = False

def cal_distance(p1,p2):
        return np.sqrt( (p2[0] - p1[0])**2 + (p2[1] - p1[1])**2 )

def shift_point(point,shift):
        return ( point[0] + shift[0], point[1] + shift[1] )

def cal_mid(p1,p2):
        return ((p1[0]+ p2[0])/2 , (p1[1]+ p2[1])/2)


def overlap_area(tl1, br1, tl2, br2):  # returns 0 if rectangles don't intersect
        
        dx = min(br1[0], br2[0]) - max(tl1[0], tl2[0])
        dy = min(br1[1], br2[1]) - max(tl[1], tl2[1])
        if (dx>=0) and (dy>=0):
                return dx*dy
        else:
                return 0

      

def find_all_persons(detections, frame):
        global pid
        for p in persons:
                if p.getDone() == False:
                        
                        p_offset = p.getPredictedOffset(frame)
                        p_tl = shift_point(p.getTl(),p_offset)
                        p_br = shift_point(p.getBr(),p_offset)
                        p_mp = shift_point(p.getMid(),p_offset)
                        p_area = p.getArea()
        
                        maxScore = 0
                        score = 0
                        overlap = False
                        
                        for d in detections:
                                        if d.isFound() == False :                                
                                                d_tl = d.getTl()
                                                d_br = d.getBr()
                                                d_mp = cal_mid(d_tl,d_br)
                                                cfd = d.getCfd()                                               
 
                                                mp_offset = cal_distance(p_mp, d_mp)
                                                tl_offset = cal_distance(p_tl, d_tl)
                                                br_offset = cal_distance(p_br, d_br)
                                                
                                                threshHold = np.sqrt(p_area)* offset_threshhold
                                                
                                                if (mp_offset < threshHold or tl_offset < threshHold or br_offset < threshHold):
                                                        score = 1/(1 + mp_offset + tl_offset + br_offset)
                                                        if score > maxScore:
                                                                maxScore = score
                                                                det = d

                        for d in detections:
                                        if d.isFound() == True:
                                                d_tl = d.getTl()
                                                d_br = d.getBr()

                                                oa = overlap_area(p_tl, p_br, d_tl, d_br)

                                                if oa >  p_area:
                                                        p.updateCoords(p_tl, p_br, frame)
                                                        overlap = True
                                                        
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

class Region:
        def __init__(self, tl, br, rid):
                self.tl = tl
                self.br = br
                self.rid = rid
        def getTl(self):
                return self.tl
        def getBr(self):
                return self.br
        def getTlInt(self):
                return (int(self.tl[0]),int(self.tl[1]))
        def getBrInt(self):
                return (int(self.br[0]),int(self.br[1]))
        def getId(self):
                return self.rid



def printPersons():
        print('pid: '+str(pid))
        for p in persons:
                print('top-left: '+str(p.getTl())+'top-right:'+str(p.getBr())+"__ area: "+str(p.getArea()))

def printRegions():
        for r in regions:
                print('ID: '+str(r.getTl())+'   top-left: '+str(r.getTl())+'   top-right:'+str(r.getBr()) )

                
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
                if p.getFrameLost() < 5:                        
                        frame = cv2.rectangle(image,p.getTl(),p.getBr(),(0,255,0),7)
                        cv2.putText(frame, str(p.getId()), (int(p.getMid()[0]),int(p.getMid()[1])), cv2.FONT_HERSHEY_COMPLEX, 1, (255,0,0), 8)
        return frame
                

##############################################

def line_select_callback(clk,rls):    
    global r_x1
    global r_y1
    global r_x2
    global r_y2
    

    
    r_x1= clk.xdata
    r_y1= clk.ydata
    r_x2= rls.xdata
    r_y2= rls.ydata
      
    print('('+str(r_x1)+' , '+str(r_y1)+')'+'______'+'('+str(r_x2)+' , '+str(r_y2)+')')
    #analyze()


def save_region():        
        global rid
        print("saving region: "+str(rid))
        r = Region((r_x1,r_y1),(r_x2,r_y2), rid)
        regions.append(r)
        rid += 1
        cv2.rectangle(r_img,r.getTlInt(),r.getBrInt(),(0,255,0),7)        
        cv2.putText(r_img, str(r.getId()), (int(cal_mid(r.getTl(),r.getBr())[0]),r.getTlInt()[1]-10), cv2.FONT_HERSHEY_COMPLEX, 1, (255,0,0), 8)
        r_ax.imshow(r_img)


def toggle_selector(event):
    global closeProgram
    if event.key == 'p':
        printRegions()
    if event.key == 'i':
        save_region()
    if event.key == 'q':       
        closeProgram = True
    if event.key == 'b':       
        closeProgram = True
    #toggle_selector.RS.set_active(True)


def analyze():
        global r_traffic
        global r_avgFrames
        f_count = 0
        r_traffic = 0
        r_avgFrames = 0
        for p in persons:
                if len(p.getTracks()) > 16 :
                        
                        tracks = p.getTracks()
                        p_found = False
                
                        for t in tracks:
                                if t[0] > r_x1 and t[0] < r_x2 and t[1] > r_y1 and t[1] < r_y2:
                                        p_found = True
                                        f_count +=1
                        if p_found == True:
                                r_traffic+=1
        if r_traffic > 0:
                r_avgFrames = f_count / r_traffic

        kpi = 'Traffic: '+str(r_traffic)+'  Average Stay Frames: '+str(r_avgFrames)

        print(kpi)

        #cv2.putText(frame, kpi, (int(p.getMid()[0]),int(p.getMid()[1])), cv2.FONT_HERSHEY_COMPLEX, 1, (255,0,0), 8
                


def analyze_all():
        
        for r in regions:
                f_count = 0
                r_traffic = 0
                r_avgFrames = 0
                for p in persons:
                        if len(p.getTracks()) > 16 :
                        
                                tracks = p.getTracks()
                                p_found = False
                
                                for t in tracks:
                                        if t[0] > r.getTl()[0] and t[0] < r.getBr()[0] and t[1] > r.getTl()[1] and t[1] < r.getBr()[1]:
                                                p_found = True
                                                f_count +=1
                                if p_found == True:
                                        r_traffic+=1
                if r_traffic > 0:
                        r_avgFrames = f_count / r_traffic

                kpi = ' Traffic: '+str(r_traffic)+'  Average Stay Frames: '+str(r_avgFrames)
                cv2.putText(r_img, kpi, (int(cal_mid(r.getTl(),r.getBr())[0]),int(cal_mid(r.getTl(),r.getBr())[1])), cv2.FONT_HERSHEY_COMPLEX, 1, (255,0,0), 8)
                print('Region: '+str(r.getId())+kpi)
        
        r_ax.imshow(r_img)
        plt.show()

        #cv2.putText(frame, kpi, (int(p.getMid()[0]),int(p.getMid()[1])), cv2.FONT_HERSHEY_COMPLEX, 1, (255,0,0), 8

                                                           


############## Find Path ################                                                           
                                              


###############Define Regions#######################
r_fig, r_ax = plt.subplots(1)
r_img = cv2.imread('images/s4Pic.png',1)
#cv2.rectangle(r_img,(100,100),(300,300),(0,255,0),7)

r_ax.imshow(r_img)


toggle_selector.RS = RectangleSelector(
    r_ax, line_select_callback,
    drawtype='box', useblit=True,
    button=[1], minspanx=5, minspany=5,
    spancoords='pixels', interactive=True
)

bbox = plt.connect('key_press_event', toggle_selector)

plt.show(block=False)

while True:
    plt.pause(0.05)
    if(closeProgram == True):
            closeProgram = False
            break


##############Process Video#######################

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


                
                find_all_persons(detections, frameID)

                frame = draw_people(frame)

                cv2.imshow('frame', frame)
                if cv2.waitKey(1) & 0XFF == ord('q'):
                        break
        else:
                capture.release()





analyze_all()

cv2.waitKey(0)
cv2.waitKey(0)
cv2.destroyAllWindows()

