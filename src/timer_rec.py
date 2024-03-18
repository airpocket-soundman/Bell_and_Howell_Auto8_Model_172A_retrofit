# Copyright (c) 2024 yasuhiro yamashita
# Released under the MIT license.
# see http://opensource.org/licenses/MIT
#
# ========================================
# pathe motocamera digitlize mod controler
# controler program ver.0.0.0
# on Raspberry Pi Zero2W
# image sensor:IMX708
# ========================================
# GPIO検出ではなくてタイマーで画像を取得するテスト。
# IMX219使用　libcameraではない方


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

number_still        = 0
number_cut          = 0
number_frame        = 0
rec_size            = 1
rec_pix             = [[ 320,  240], [ 640, 480], [960, 720]]
time_log            = []
time_log2           = []
time_log3           = []
time_log4           = []
exposure_time       = 5000  # 1000-100000  defo:5000
analogue_gain       = 16	# 1.0-20.0    defo:2.0
shutter_delay_time  = 50 * 0.001   # シャッター動作を検出してから画像取得するまでの遅延時間 ms

threads             = []    #マルチスレッド管理用リスト
frame_list          = []    #動画用画像保存リスト
exposure_time_list  = []

camera_mode         = 0     #0:movie,   1:still
speed_mode          = 0     #0:nomal,   1:high speed
gain_mode           = 0     #-1,0,1
film_mode           = 0     #0:mono,    1:mono,     2:color,    3:color,
is_shooting         = False
recording_completed = True

buffers             = 1
time_interval       = 0.001
jpg_encode          = True


rec_finish_threshold_time    = 1        #sec  *detect rec button release
number_max_frame    = 50               #連続撮影可能な最大フレーム数　とりあえず16FPS x 60sec = 960フレーム
record_fps          = 16                #MP4へ変換する際のFPS設定値
share_folder_path   = os.path.expanduser("~/share/")
device_name         = "motocamera"
codec               = cv2.VideoWriter_fourcc(*'mp4v')
camera = cv2.VideoCapture(0)

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
    camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    print("rec_size :width ", rec_width, "height", rec_height)


# timerを受けて画像を取得する関数
def timer_shutter(text):
    global number_frame,time_log,time_log2,time_log3,is_shooting
    is_shooting = True
    print(number_frame)
    time_log.append(time.time())
    ret, frame = camera.read()
    #print(frame)
    time_log2.append(time.time())
    if jpg_encode:
        result, frame = cv2.imencode(".jpg", frame)
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

def repeat_n_times(n, interval, function, *args):
    """
    指定された回数n回、指定された間隔interval秒ごとに関数を呼び出します。

    Parameters:
    - n: 関数を呼び出す回数
    - interval: 関数を呼び出す間隔（秒）
    - function: 呼び出される関数
    - args: 関数に渡される引数
    """
    def func_wrapper(count):
        if count < n:  # 指定された回数まで関数を呼び出す
            function(*args)  # 関数を呼び出し
            count += 1  # 呼び出し回数をインクリメント
            threading.Timer(interval, func_wrapper, [count]).start()  # 次の呼び出しをスケジュール

    func_wrapper(0)  # 関数呼び出しを開始


# テスト関数
def print_message(message):
    global timelog
    print(message, "at", time.time() - timelog)
    timelog = time.time()

# メイン
if __name__ == "__main__":
    # シェアフォルダ内の動画、静止画ファイルの最大番号を取得
    find_max_number_in_share_folder()
    print("動画と静止画の最大番号は",number_cut,number_still)

    set_camera_mode()

    # 例: 3回、2秒ごとにprint_messageを呼び出し、「Test message」というメッセージを出力
    repeat_n_times(number_max_frame, time_interval, timer_shutter, "test")
    #repeat_n_times(20, 0.01, print_message, "Test message")

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
