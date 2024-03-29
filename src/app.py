from flask import render_template, Flask, Response
import cv2
import time
import numpy as np
from typing import List

app = Flask(__name__, template_folder='templates')   #templates_folderはデフォルトで'templates'なので本来定義は不要

CAP_WIDTH   = 320                   #出力動画の幅
CAP_HEIGHT  = 240                   #出力動画の高さ
LAW_WIDTH   = 2304                  #カメラ内のraw画像の幅
LAW_HEIGHT  = 1296                  #カメラ内のraw画像の高さ

image_sensor = "IMX219"             #IMX219/IMX708
folder_path ="/tmp/img"
movie_length = 100                  #撮影するフレーム数
time_list = []
exposure_time = 5000                #イメージセンサの露出時間
analog_gain = 20.0                  #イメージセンサのgain

def gen_frames():
    print("gen_frames")
    count = 0

    # init camera
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    while True:
        print("count = ",count)
        start_time_frame = time.perf_counter()

        ret, frame = cap.read()

        #フレームデータをjpgに圧縮
        ret, buffer = cv2.imencode('.jpg',frame)
        # bytesデータ化
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

        elapsed_time_frame = time.perf_counter() - start_time_frame
        print("frame_number = " + str(count) + " / time = " + str(elapsed_time_frame))
        count +=1

@app.route('/video_feed')
def video_feed():
    #imgタグに埋め込まれるResponseオブジェクトを返す
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/')
@app.route('/index')
def index():
   
    user = {'username'      : 'Raspberry Pi zero2 W',
            'image sensor'  : image_sensor,
            'lens'          : ""}
    return render_template('index.html', title='home', user=user)