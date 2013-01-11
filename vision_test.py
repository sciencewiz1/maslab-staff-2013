import cv
import numpy
import serial
import scipy
import time
'''image1=cv.LoadImage("C:/Users/David G. Goehring/Desktop/test4.jpg")
template=cv.LoadImage("C:/Users/David G. Goehring/Desktop/template.jpg")
width = abs(image1.width - template.width)+1
height = abs(image1.height - template.height)+1
print width
print height
result_image = cv.CreateImage((width, height), cv.IPL_DEPTH_32F, 1)
cv.Zero(result_image)
cv.MatchTemplate(image1, template,result_image,cv.CV_TM_SQDIFF)
result= cv.MinMaxLoc(result_image)
#CV_TM_SQDIFF
#cv.ShowImage('a_window', image)
#g_capture = cv.CreateFileCapture('somevideo.avi')
#img=cv.QueryFrame(g_capture) 
print result
(x,y)=result[2]
(x2,y2)=(x+template.width,y+template.height)
print (x,y)
print (x2,y2)
center=(int(image1.width/float(2)),int(image1.height/float(2)))
centerEnd=(int(image1.width/float(2)+template.width),int(image1.height/float(2)+template.height))
print center
print centerEnd
print "x dist from center:"+str(image1.width/float(2)-x)
print "y dist from center:"+str(image1.height/float(2)-y)
cv.NamedWindow('win1', cv.CV_WINDOW_NORMAL)
cv.MoveWindow('win1', 100,100)
#time.sleep(10)
#cv.DestroyWindow('win1')
#cv.SetImageROI(image1,(x-1000,y-500,1500,1500)) #only look at part of image
cv.Rectangle(image1,(x,y),(x2,y2),(255,0,0),1,0)
cv.Rectangle(image1,center,centerEnd,(0,0,255),1,0)
cv.ShowImage('win1', image1)
cv.WaitKey(0)
#font = cv.InitFont(cv.CV_FONT_HERSHEY_SIMPLEX, 1, 1, 0, 3, 8)
#x=100
#y=100
#cv.PutText(frame,"Hello World!!!", (x,y),font, 255) #Draw the text
#cv.ShowImage('a_window', image) #Show the image
#cv.Waitkey(10000)
#cv.SaveImage('C:/Users/David G. Goehring/Desktop/image.png', image) #Saves the image
'''
'''#Load the haar cascade
cv.NamedWindow("t")
cv.WaitKey(0)
hc = cv.Load("haarcascade_frontalface_alt.xml")
#Detect face in image
face = cv.HaarDetectObjects('t', hc, cv.CreateMemStorage(), 1.2,2, cv.CV_HAAR_DO_CANNY_PRUNING, (0,0) )
for (x,y,w,h) in face:
    print 'face found at: '+str(w)+','+str(h)
'''
'''#when modifying image, need to create image container to hold new image
#need to convert image to binary and greyscale before contour search can begin
image=cv.LoadImage("test2.jpg")
clone=cv.CloneImage(image)
grey=cv.CreateImage(cv.GetSize(clone),8,1)
cv.CvtColor(clone,grey,cv.CV_BGR2GRAY)
cv.Threshold(grey,grey,100,255,cv.CV_THRESH_BINARY)
cv.NamedWindow("test",cv.CV_WINDOW_NORMAL)
cv.ShowImage("test",grey)
cv.WaitKey(0)
#contours, hierarchy=cv.FindContours(clone, cv.CreateMemStorage(), cv.CV_RETR_LIST, cv.CV_CHAIN_APPROX_SIMPLE, (0, 0))
storage = cv.CreateMemStorage(0)
contours = cv.FindContours (grey, storage, method = cv.CV_CHAIN_APPROX_SIMPLE)
cv.DrawContours(grey, contours, 0, cv.RGB(255, 0, 0),0)
cv.ShowImage("test",grey)
cv.WaitKey(0)'''
image=cv.LoadImage("test.jpg")
hue=cv.CreateImage(cv.GetSize(image),8,1)
sat=cv.CreateImage(cv.GetSize(image),8,1)
val=cv.CreateImage(cv.GetSize(image),8,1)
hsv=cv.CreateImage(cv.GetSize(image),8,3)
cv.CvtColor(image,hsv,cv.CV_RGB2HSV)
cv.Split(hsv, hue, sat, val, None)
thresholded = cv.CreateImage(cv.GetSize(image), cv.IPL_DEPTH_8U, 1)
hsv_min = cv.Scalar(0, 105, 255)
hsv_max = cv.Scalar(255, 255, 255)
cv.InRangeS(hsv, (0, 105, 255), (140, 255, 255), thresholded)
#cv.InRangeS(hsv, hsv_min, hsv_max, thresholded)
#canny=cv.CreateImage(cv.GetSize(image),8,1)
#cv.Canny (image, canny, 100, 255)
#cv.NamedWindow("test")
#cv.ShowImage("test",canny)
cv.ShowImage("test",hsv)
cv.ShowImage("test1",thresholded)
cv.WaitKey(0)
