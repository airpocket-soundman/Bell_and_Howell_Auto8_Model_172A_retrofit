import cv2
import time
# カメラデバイスを開く
cap = cv2.VideoCapture(0) # 0は通常、システムのデフォルトカメラです

# 解像度を設定する
# ビニングモードでの解像度1640x1232を設定
cap.set(cv2.CAP_PROP_FRAME_WIDTH,  1280)         #1640
cap.set(cv2.CAP_PROP_FRAME_HEIGHT,  960)         #1232
start_time = time.time()
# 画像をキャプチャする
ret, frame = cap.read()
finish_time = time.time()

if ret:
    # 画像をファイルに保存

    cv2.imwrite('captured_image.jpg', frame)

else:
    print("画像のキャプチャに失敗しました")

print(finish_time-start_time)
# カメラデバイスを解放
cap.release()