# Copyright (c) 2022 yasuhiro yamashita
# Released under the MIT license.
# see http://open source.org/licenses/MIT
#
# ============================
# spring loaded digital camera
#
# controler program ver.2.0.0
# camera:Bell & Howell auto 8 model 172A
# image sensor:IMX219
# board:test board V1.0
# ============================

import cv2
import os
import subprocess
import time
import datetime
import RPi.GPIO as GPIO
import sys
from picamera2 import Picamera2
import threading
import shutil
import re

pin_shutter         = 12    # shutter timing picup 
pin_led_red         = 20
pin_led_green       = 26
pin_shutdown        = 16
pin_dip1            = 2
pin_dip2            = 3
pin_dip3            = 4
pin_dip4            = 14
pin_dip5            = 15
pin_dip6            = 0

number_still        = 0
number_cut          = 0
number_frame        = 0
raw_size            = 0     #0:1640 x 1232      1:2304 x 1296      2:3280 x 2464   3:4608 x 2592  4:320 x 240   0:IMX219 cine, 1:IMX708 cine 2:IMX219 still 3:IMX708 still
raw_pix             = [[1640, 1232], [2304, 1296], [3280, 2464], [4608, 2592], [320, 240]]
cap_size            = 0     #0: 640 x  480      1: 640 x  480      2:3280 x 2464   3:4608 x 2592  4:320 x 240   4:high speed cine
cap_pix             = [[ 640,  480], [ 640,  480], [3208, 2464], [4608, 2592], [320, 240]]
timeLog             = []
exposure_time       = 5000  # 1000-100000  defo:5000
analog_gain         = 10.0	# 1.0-20.0    defo:5.0
threads = []

rec_finish_threshold_time    = 0.1   #sec  *detect rec button release
number_max_frame    = 960        #連続撮影可能な最大フレーム数　とりあえず16FPS x 60sec = 960フレーム
record_fps          = 16                    #MP4へ変換する際のFPS
tmp_folder_path     = "/tmp/img/"
share_folder_path   = "~/share/"
movie_file_name     = "test.mp4"
movie_file_path     = os.path.expanduser(share_folder_path + movie_file_name)

codec               = cv2.VideoWriter_fourcc(*'mp4v')

# GPIO設定
GPIO.setmode(GPIO.BCM)
GPIO.setup(pin_shutter,     GPIO.IN, pull_up_down = GPIO.PUD_UP)
GPIO.setup(pin_shutdown,    GPIO.IN, pull_up_down = GPIO.PUD_UP)
GPIO.setup(pin_dip1,        GPIO.IN, pull_up_down = GPIO.PUD_UP)
GPIO.setup(pin_dip2,        GPIO.IN, pull_up_down = GPIO.PUD_UP)
GPIO.setup(pin_dip3,        GPIO.IN, pull_up_down = GPIO.PUD_UP)
GPIO.setup(pin_dip4,        GPIO.IN, pull_up_down = GPIO.PUD_UP)
GPIO.setup(pin_dip5,        GPIO.IN, pull_up_down = GPIO.PUD_UP)
GPIO.setup(pin_led_red,     GPIO.OUT)
GPIO.setup(pin_led_green,   GPIO.OUT)

# シャッター開を検出した場合の処理
def on_shutter_open():
    global timeLog, threads, number_frame
    if (number_frame <= number_max_frame):
#        print(len(imgMem))
        timeLog.append(time.time())
        t = threading.Thread(target = get_images, args=(number_frame, camera))    
        t.start()
        threads.append(t)
        number_frame += 1

# シャットダウンボタンが押されたとき
def on_shutdown_button_pressed():
    command = ["sudo", "shutdown", "-h", "now"]
    subprocess.run(command)

#カメラ入力インスタンス定義
def get_images(image_index, camera):
    frame = camera.capture_array()	
    cv2.imwrite(tmp_folder_path + "image_" + str(image_index) + ".jpg", frame)	

def movie_save():
    video = cv2.VideoWriter(movie_file_path, codec, record_fps, (cap_width, cap_height))
    if not video.isOpened():
        print("can't be opened")
        sys.exit()
    for i in range(number_frame):
        frame = cv2.imread(tmp_folder_path + "image_" + str(i) + ".jpg")
        video.write(frame)
    number_frame = 0
    video.release()

# ***.mp4と言うファイル名の最も大きい値を検出する
def find_largest_number_in_filenames(folder_path):
    # ファイル名から数値を抽出するための正規表現パターン
    pattern = re.compile(r'^(\d{3})\.mp4$')
    
    # 最大の数値を格納する変数
    max_number = -1
    
    # 指定されたフォルダのファイルをループ処理
    for filename in os.listdir(folder_path):
        # 正規表現を使ってファイル名から数値を抽出
        match = pattern.match(filename)
        if match:
            # 数値部分を整数として取得
            number = int(match.group(1))
            # 現在の最大値と比較して、必要に応じて更新
            if number > max_number:
                max_number = number

if __name__ == "__main__":
    GPIO.add_event_detect(pin_shutter,  GPIO.RISING,  callback = on_shutter_open, bouncetime = 5)
    GPIO.add_event_detect(pin_shutdown, GPIO.FALLING, callback = on_shutdown_button_pressed, bouncetime = 100)
    GPIO.output(pin_led_red, False)
    GPIO.output(pin_led_green, False)

    camera = Picamera2
    cap_width   = cap_pix[cap_size][0]
    cap_height  = cap_pix[cap_size][1]
    raw_width   = raw_pix[raw_size][0]
    raw_height  = raw_pix[raw_size][1]
    config  = camera.create_preview_configuration(main={"format": 'RGB888', "size":(cap_width, cap_height)}, raw   ={"size":(raw_width, raw_height)}) 
    capture = cv2.VideoCapture(camera, cv2.CAP_V4L2)
    camera.set_controls({"ExposureTime": exposure_time, "AnalogueGain": analog_gain})
    camera.start()

    timeStart = time.time()
    print("ok")

    while(True):
        GPIO.output(pin_led_green, True)
        GPIO.output(pin_led_red, False)
        time.sleep(1.0)  
        print(GPIO.input(pin_shutter))

        if number_frame >0:
            if time.time() - timeLog[-1] >= rec_finish_threshold_time:
                movie_save()
                number_cut += 1

    capture.release()
    #cv2.destroyAllWindows()




