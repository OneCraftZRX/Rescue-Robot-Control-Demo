from flask import Response
from flask import Flask
from gevent import pywsgi
from flask import render_template
import threading
import argparse
import datetime
import imutils
import time
import cv2

outputFrame=None

lock=threading.Lock()


app=Flask(__name__)


cap = cv2.VideoCapture(0)  

@ app . route ( "/" ) 
def index():
    return render_template('index.html')

def showimage():
    global cap ,lock,outputFrame


    while True:
        frame = cap.read()
        frame   =   imutils . resize ( frame ,   width = 400 ) 
        gray   =   cv2 . cvtColor ( frame ,   cv2 . COLOR_BGR2GRAY ) 
        gray   =   cv2 . GaussianBlur ( gray ,   ( 7 ,   7 ) ,   0 )
        timestamp   =   datetime . datetime . now ()

        cv2 . putText ( frame ,   timestamp . strftime ( 
            "%A %d %B %Y %I:%M:%S%p" ) ,   ( 10 ,   frame . shape [ 0 ]   -   10 ) , 
            cv2 . FONT_HERSHEY_SIMPLEX ,   0.35 ,   ( 0 ,   0 ,   255 ) ,   1 ) 
        with   lock : 
            outputFrame   =   frame . copy ()

	
def   generate () : 
    # grab global references to the output frame and lock variables 
    global   outputFrame ,   lock 

    # loop over frames from the output stream 
    while   True : 
        # wait until the lock is acquired 
        with   lock : 
            # check if the output frame is available, otherwise skip 
            # the iteration of the loop 
            if   outputFrame  is   None : 
                continue 

            # encode the frame in JPEG format 
            ( flag ,   encodedImage )   =   cv2 . imencode ( ".jpg" ,   outputFrame ) 

            # ensure the frame was successfully encoded 
            if   not   flag : 
                continue 

        # yield the output frame in the byte format 
        yield (b'--frame\r\n'   b'Content-Type: image/jpeg\r\n\r\n'   +  
            bytearray ( encodedImage )   +   b'\r\n' ) 

	
@app.route ( "/video_feed" ) 
def   video_feed ( ) : 
    # return the response generated along with the specific media 
    # type (mime type) 
    return   Response ( generate ( ) , 
        mimetype   =   "multipart/x-mixed-replace; boundary=frame" ) 

	
# check to see if this is the main thread of execution 
if   __name__   ==   '__main__' : 
    # construct the argument parser and parse command line arguments 
    ap   =   argparse . ArgumentParser ( ) 
    
    ap . add_argument ( "-i" ,   "--ip" ,   type = str ,   required = True , 
        help = "ip address of the device" ) 

    ap . add_argument ( "-o" ,   "--port" ,   type = int ,   required = True , 
        help = "ephemeral port number of the server (1024 to 65535)" ) 
    args   =   vars ( ap . parse_args ( ) ) 

    # start a thread that will perform motion detection 
    t   =   threading . Thread ( target = showimage ,   args = () ) 
    t . daemon   =   True 
    t . start ( ) 

    # start the flask app 
    app . run ( host = args [ "ip" ] ,   port = args [ "port" ] ,   debug = True , 
        threaded = True ,   use_reloader = False ) 

    # server = pywsgi.WSGIServer(('192.168.43.62', 8000), app)
    # server.serve_forever()
# release the video stream pointer 
cap.release()



