# Raspberry Pi Zero2 W のmicroSDセットアップ方法

|項目|要件|
|-|-|
|SBC|Raspberry Pi Zero2 W|
|microSD|32GB以上|
|OS|Bullseye 32bit lite|
|sensor|IMX219|

# OS version

OS:Raspberry Pi OS Buster 32bit lite
https://downloads.raspberrypi.org/raspios_lite_armhf/images/raspios_lite_armhf-2021-05-28/





OS:Raspberry Pi OS Bullseye 32bit lite

```

$ lsb_release -a
No LSB modules are available.
Distributor ID: Raspbian
Description:    Raspbian GNU/Linux 11 (bullseye)
Release:        11
Codename:       bullseye

$ getconf LONG_BIT
32
```

# USB SSHの有効化
config.txtに追記
dtoverlay=dwc2

commandline.txtのrootwait とquietの間に[]の中を追記
rootwait [modules-load=dwc2,g_ether] quiet



USB SSH化推奨

USB OTGするときは左側のmicro USBコネクタ

windowsにドライバインストールすること

# wifi setting
```
sudo raspi-config
```
1 System Options -> S1 Wireless LAN
SSIDとPassphraseを入力

# networkの設定
sudo raspi-config
 1 System Options -> S1 Wireless Lan

sudo reboot


# setup

bullseye
```
sudo apt-get update
sudo apt-get upgrade
sudo apt-get -y install python3-dev
sudo apt-get -y install python3-pip
sudo apt-get -y install libgl1-mesa-dev
sudo apt-get -y install libopenjp2-7-dev 
sudo apt-get -y install libavcodec-extra58 
sudo apt-get -y install libavformat58 
sudo apt-get -y install libswscale5 
sudo apt-get -y install libgtk-3-dev 
sudo apt-get -y install liblapack3 
sudo apt-get -y install libatlas-base-dev
sudo pip install opencv-python==4.6.0.66
sudo pip install opencv-contrib-python
sudo pip install -U numpy
```

buster
```
sudo apt-get update
sudo apt-get upgrade
sudo apt install libhdf5-dev libqt4-test libqtgui4 libjasper1 libatlas-base-dev
sudo apt-get -y install libopenexr23
sudo apt-get -y install ffmpeg
sudo apt-get -y install python3-dev
sudo apt-get -y install python3-pip
sudo pip3 install opencv-python==4.1.0.25
sudo pip3 install opencv-contrib-python==4.1.0.25
```
```
vcgencmd get_camera
```

## カメラ設定
https://yasuraka.dns04.com/raspberry-pi-camera-%E3%82%92%E6%9C%89%E5%8A%B9%E5%8C%96%E3%81%99%E3%82%8B

IMX219 (camera V2) の設定
libcameraモードではなく、Legacyモードを使用する！！

bullseyeの場合
```
sudo raspi-config
```
3 Interface Options -> I1 Legacy Camera -> No

※/boot/config.txtのdtoverlay=imx219は無効化しておくこと！

```
vcgencmd get_camera
```
で
```
```
supported=1 detected=1, libcamera interfaces=0
```
とひょうじされればOK



## swap無効化とtempのRAMディスク化
```
sudo systemctl stop dphys-swapfile
sudo systemctl disable dphys-swapfile
```
ファイルシステムの設定を書き換えて/tmpをRAM上にマウントする
```
sudo nano /etc/fstab
```
以下の行を追加
```
tmpfs /tmp tmpfs defaults,size=128m,noatime,mode=1777 0 0
```
microSD上の/tmpを削除する
```
sudo rm -rf /tmp
```
```
$ free -m
               total        used        free      shared  buff/cache   available
Mem:             419          73         193           0         151         292
Swap:              0           0           0
df -h
Filesystem      Size  Used Avail Use% Mounted on
/dev/root        29G  1.9G   26G   7% /
devtmpfs         80M     0   80M   0% /dev
tmpfs           210M     0  210M   0% /dev/shm
tmpfs            84M  928K   83M   2% /run
tmpfs           5.0M  4.0K  5.0M   1% /run/lock
tmpfs           128M     0  128M   0% /tmp
/dev/mmcblk0p1  255M   31M  225M  13% /boot
tmpfs            42M     0   42M   0% /run/user/1000
```
## Flaskのインスト―ル
```
pip install flask
```
flaskでapp.pyを実行するには
```
flask run --host=0.0.0.0
```

## sambaサーバー
```
sudo apt install samba
mkdir /home/[user]/share
sudo chmod 777 /home/[user]/share
sudo nano /etc/samba/smb.confy
```
追記
```
[share]
   comment = user file space
   path = /home/[user]/share
   force user = [user]
   guest ok = yes
   create mask = 0777
   directory mask = 0777
   read only = no

```
sudo systemctl restart smbd

## vim
sudo apt install vim

vim ~/.vimrc

set number
syntax enable
set expandtab
set tabstop=4
set shiftwidth=4

## data保存フォルダをマウントする
FAT32もしくはexFATでフォルダをマウントすることで、Win上からも直接読み込めるデータフォルダを作成する。
