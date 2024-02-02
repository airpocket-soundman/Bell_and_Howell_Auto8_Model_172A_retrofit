# Raspberry Pi Zero2 W のmicroSDセットアップ方法

|項目|要件|
|-|-|
|SBC|Raspberry Pi Zero2 W|
|microSD|32GB以上|
|OS|Bullseye 64bit lite|

# OS version
OS:Raspberry Pi OS Bullseye 64bit lite

```
$ lsb_release -a
No LSB modules are available.
Distributor ID: Debian
Description:    Debian GNU/Linux 11 (bullseye)
Release:        11
Codename:       bullseye

$ getconf LONG_BIT
64
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

# setup
```
sudo apt update & sudo apt -y upgrade
sudo apt -y install python3-dev python3-pip
pip install picamera2
pip install opencv-python
sudo apt -y install libgl1-mesa-dev
```


## カメラ設定
### IMX219 (camera V2の場合)
```
sudo nano /boot/config.txt
```

dtoverlay=imx219


### IMX708 (camera V3の場合)

```
sudo nano /boot/config.txt
```

dtoverlay=imx708


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
tmpfs /tmp tmpfs defaults,size=64m,noatime,mode=1777 0 0
```
microSD上の/tmpを削除する
```
sudo rm -rf /tmp
```


## sambaサーバー　

## data保存フォルダをマウントする
FAT32もしくはexFATでフォルダをマウントすることで、Win上からも直接読み込めるデータフォルダを作成する。
