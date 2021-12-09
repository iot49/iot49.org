# REPL prompt

## picocom

To connect directly to the REPL of your microcontroller, launch a Terminal (click the blue `+` icon at the upper left of Jupyter Lab and then the Terminal icon). At the shell prompt type

```bash
picocom -b115200 /dev/ttyUSB0
```

```{toggle}
![REPL](figures/repl.png)
```

**Hint:** If MicroPython displays no output, it may be in "raw repl" mode. Type `ctrl-B` at the console to return to the "friendly repl".


## rshell

You can also use David Hyland's [rshell]() in *ide49*:

```bash
iot@server:~$ rshell -p /dev/ttyUSB0
Using buffer-size of 32
Connecting to /dev/ttyUSB0 (buffer-size 32)...
Trying to connect to REPL  connected
Retrieving sysname ... esp32
Testing if ubinascii.unhexlify exists ... Y
Retrieving root directories ... /boot.py/ /lib/ /secrets.py/ /webrepl_cfg.py/
Setting time ... Jul 30, 2021 13:39:37
Evaluating board_name ... pyboard
Retrieving time epoch ... Jan 01, 2000
Welcome to rshell. Use Control-D (or the exit command) to exit rshell.
/home/iot> repl
Entering REPL. Use Control-X to exit.
>
MicroPython v1.16-78-ge3291e180 on 2021-07-22; 4MB/OTA module with ESP32
Type "help()" for more information.
>>> 
>>> for i in range(4):
...     print(i**10)   
... 
0
1
1024
59049
>>> 
MPY: soft reboot
WebREPL daemon started on ws://10.39.40.135:8266
Started webrepl in normal mode
MicroPython v1.16-78-ge3291e180 on 2021-07-22; 4MB/OTA module with ESP32
Type "help()" for more information.
>>> 
/home/iot> 
iot@server:~$ 
```