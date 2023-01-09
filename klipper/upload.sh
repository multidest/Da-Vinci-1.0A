scp printer.cfg pi@octopi:/home/pi/Da-Vinci-1.0A/klipper/printer.cfg
ssh pi@octopi -f 'echo FIRMWARE_RESTART > /tmp/printer'