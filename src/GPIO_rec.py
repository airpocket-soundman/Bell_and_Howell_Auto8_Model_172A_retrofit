# Copyright (c) 2024 yasuhiro yamashita
# Released under the MIT license.
# see http://open source.org/licenses/MIT
#
# ========================================
# pathe motocamera digitlize mod controler
# controler program ver.0.0.0
# on Raspberry Pi Zero2W
# image sensor:IMX708
# ========================================
# timer_rec.pyを改変してGPIO割り込みで撮影するようにする
# IMX219使用、libcameraではない方


import cv2
import os
import subprocess
import time
import RPi.GPIO as GPIO
import sys
import threading
import re
import numpy as np

timelog = time.time()

camera              = 0       # 0:172A  1:motocamera    2:Bolex C-8
number_still        = 0
number_cut          = 0
number_frame        = 0
rec_size            = 3
rec_pix             = [[ 320,  240], [ 640, 480], [960, 720], [1280, 720], [1280, 960]]
time_log            = []
time_log2           = []
time_log3           = []
time_log4           = []
exposure_time       = 1000  # 1000-100000  defo:5000
analogue_gain       = 16	# 1.0-20.0    defo:2.0
shutter_delay_time  = 0 * 0.001   # シャッター動作を検出してから画像取得するまでの遅延時間 ms

threads             = []    #マルチスレッド管理用リスト
frame_list          = []    #動画用画像保存リスト
exposure_time_list  = []

camera_mode         = 0     #0:movie,   1:still
speed_mode          = 0     #0:nomal,   1:high speed
gain_mode           = 0     #-1,0,1
film_mode           = 0     #0:mono,    1:mono,     2:color,    3:color,
is_shooting         = False
recording_completed = True

buffers             = 4
jpg_encode          = False

rec_finish_threshold_time    = 1        #sec  *detect rec button release
number_max_frame    = 200               #連続撮影可能な最大フレーム数　とりあえず16FPS x 60sec = 960フレーム
record_fps          = 16                #MP4へ変換する際のFPS設定値
tmp_folder_path     = "/tmp/img/"
share_folder_path   = os.path.expanduser("~/share/")

codec               = cv2.VideoWriter_fourcc(*'mp4v')

if camera == 0:
    # Bell & Howell 172A
    pin_shutter         = 12 
    pin_led_red         = 20
    pin_led_green       = 26
    pin_shutdown        = 16
    pin_dip1            = 2
    pin_dip2            = 3
    pin_dip3            = 4
    pin_dip4            = 14
    pin_dip5            = 15
    pin_dip6            = 0
    device_name         = "BH172A"

elif camera == 1:
    # motocamera
    pin_shutter         = 23    # shutter timing picup 
    pin_led_red         = 24
    pin_led_green       = 25
    pin_shutdown        =  8
    pin_dip1            =  7
    pin_dip2            =  1
    pin_dip3            = 12
    pin_dip4            = 16
    pin_dip5            = 20
    pin_dip6            = 21
    device_name         = "motocamera"

elif camera == 2:
    # Bolex
    pin_shutter         = 25    # shutter timing picup 
    pin_led_red         = 15
    pin_led_green       = 18
    pin_shutdown        = 14
    pin_dip1            =  8
    pin_dip2            =  7
    pin_dip3            =  1
    pin_dip4            = 12
    pin_dip5            = 16
    pin_dip6            = 20
    device_name         = "BolexC-8"

# GPIO設定
GPIO.setmode(GPIO.BCM)
GPIO.setup(pin_shutter,     GPIO.IN, pull_up_down = GPIO.PUD_UP)
GPIO.setup(pin_shutdown,    GPIO.IN, pull_up_down = GPIO.PUD_UP)
GPIO.setup(pin_dip1,        GPIO.IN, pull_up_down = GPIO.PUD_UP)
GPIO.setup(pin_dip2,        GPIO.IN, pull_up_down = GPIO.PUD_UP)
GPIO.setup(pin_dip3,        GPIO.IN, pull_up_down = GPIO.PUD_UP)
GPIO.setup(pin_dip4,        GPIO.IN, pull_up_down = GPIO.PUD_UP)
GPIO.setup(pin_dip5,        GPIO.IN, pull_up_down = GPIO.PUD_UP)
GPIO.setup(pin_dip6,        GPIO.IN, pull_up_down = GPIO.PUD_UP)
GPIO.setup(pin_led_red,     GPIO.OUT)
GPIO.setup(pin_led_green,   GPIO.OUT)



camera = cv2.VideoCapture(0,cv2.CAP_V4L2)

# shareフォルダの動画と静止画のファイル番号を読み取る
def find_max_number_in_share_folder():
    global number_still, number_cut
    # ファイル名の数字部分を抽出する正規表現パターン
    pattern_mp4 = re.compile(r'motocamera(\d{3})\.mp4$')
    pattern_jpg = re.compile(r'motocamera(\d{3})\.jpg$')
    number_cut   = -1  # 存在する数字の中で最も大きいものを保持する変数
    number_still = -1
    # 指定されたフォルダ内のすべてのファイルに対してループ
    for filename in os.listdir(share_folder_path):
        match_mp4 = pattern_mp4.match(filename)
        match_jpg = pattern_jpg.match(filename)
        if match_mp4:
            # ファイル名から抽出した数字を整数として取得
            number = int(match_mp4.group(1))
            # 現在の最大値と比較して、必要に応じて更新
            if number > number_cut:
                number_cut = number
        if match_jpg:
            number = int(match_jpg.group(1))
            if number > number_still:
                number_still = number
    
    number_still += 1
    number_cut   += 1

# 撮影モードに応じてpicameraのconfigを設定する
def set_camera_mode():
    global rec_width, rec_height, shutter_delay_time, camera

    rec_width   = rec_pix[rec_size][0]
    rec_height  = rec_pix[rec_size][1]
    camera.set(cv2.CAP_PROP_FRAME_WIDTH,  rec_width)
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, rec_height)
    camera.set(cv2.CAP_PROP_BUFFERSIZE, buffers)
    camera.set(cv2.CAP_PROP_FPS,90)

    #os.system('v4l2-ctl -d /dev/video0 -c brightness=100')               #0-100
    #os.system('v4l2-ctl -d /dev/video0 -c contrast=30')                  #-100-100
    #os.system('v4l2-ctl -d /dev/video0 -c saturation=0')                #-100-100    
    #os.system('v4l2-ctl -d /dev/video0 -c red_balance=900')            #1-7999
    #os.system('v4l2-ctl -d /dev/video0 -c blue_balance=1000')           #1-7999
    #os.system('v4l2-ctl -d /dev/video0 -c sharpness=0')                 #0-100
    #os.system('v4l2-ctl -d /dev/video0 -c color_effects=0')             #0:None 1:Mono 2:Sepia 3:Negative 14:Antique 15:set cb/cr
    os.system('v4l2-ctl -d /dev/video0 -c rotate=180')                  #0-360
    #os.system('v4l2-ctl -d /dev/video0 -c video_bitrate_mode=0')        #0:variable 1:Constant
    #os.system('v4l2-ctl -d /dev/video0 -c video_bitrate=10000000')      #25000-25000000 2500step
    os.system('v4l2-ctl -d /dev/video0 -c auto_exposure=1')
    os.system('v4l2-ctl -d /dev/video0 -c exposure_time_absolute=30')
    #os.system('v4l2-ctl -d /dev/video0 -c iso_sensitivity_auto=1')      #0:manual 1:auto
    #os.system('v4l2-ctl -d /dev/video0 -c iso_sensitivity=4')           #0:0 1:100000 2:200000 3:400000 4:800000


    print("rec_size :width ", rec_width, "height", rec_height)

# 画像を取得する関数
def shutter(text):
    global number_frame,time_log,time_log2,time_log3,is_shooting
    
    if number_frame < number_max_frame:
        is_shooting = True
        print(number_frame)
        time_log.append(time.time())
        #time.sleep(shutter_delay_time)
        ret, frame = camera.read()
        time_log2.append(time.time())
        if jpg_encode:
            ret, frame = cv2.imencode(".jpg", frame)
        frame_list.append(frame)
        time_log3.append(time.time())	
        number_frame += 1

# ムービー撮影後、画像を連結してムービーファイルを保存する。
def movie_save():
    global number_frame, number_cut, recording_completed,frame_list
    recording_completed = False
    print("save movie")
    movie_file_path = share_folder_path + device_name + "{:03}".format(number_cut) + ".mp4"

    if film_mode == "mono":
        video = cv2.VideoWriter(movie_file_path, codec, record_fps, (rec_width, rec_height), isColor = False)
    else:      
        video = cv2.VideoWriter(movie_file_path, codec, record_fps, (rec_width, rec_height))

    if not video.isOpened():
        print("can't be opened")
        sys.exit()
    for i in range(number_frame):
        if jpg_encode:
            frame = cv2.imdecode(np.frombuffer(frame_list[i], dtype = np.uint8), cv2.IMREAD_COLOR)
        else:
            frame = frame_list[i]
        if film_mode == "mono":
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        video.write(frame)
    print("movie rec finished")
    video.release()
    recording_completed = True
    number_cut += 1
    number_frame = 0
    frame_list = []

# メイン
if __name__ == "__main__":

    # シェアフォルダ内の動画、静止画ファイルの最大番号を取得
    find_max_number_in_share_folder()
    print("動画と静止画の最大番号は",number_cut,number_still)

    set_camera_mode()
    
    # シャッター動作検出時のコールバック関数
    GPIO.add_event_detect(pin_shutter,  GPIO.RISING,    callback = shutter, bouncetime = 5)


    while(True):
        time.sleep(1)

        if is_shooting:
            if time.time() - time_log[-1] >= rec_finish_threshold_time:
                is_shooting = False
        
        else:
            if number_frame > 0:
                movie_save()
                for i in range(len(time_log)-1):
                    print((time_log[i + 1] - time_log[i]) * 1000,":",(time_log2[i]-time_log[i])* 1000,(time_log3[i]-time_log[i])* 1000)
                
                time_log    = []
                time_log2   = []
                time_log3   = []
                time_log4   = []
