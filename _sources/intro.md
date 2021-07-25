# MicroPython IDE

*ide49* offers a comprehensive set of tools & growing list of examples for developing applications for microcontrollers with special support for [MicroPython](https://micropython.org/). The IDE runs on a dedicated computer (Raspberry PI or generic Intel/AMD processor). Each feature runs in a separate [Docker](https://www.docker.com/) container. All features - including installation - are available through a standard web browser - no need to install and maintain complex software on your laptop!

* Jupyter environment
    * auto-discover and program MicroPython devices
    * powerful file synchronization between the host and microcontrollers
    * install packages (upip)
    * wireless access (webrepl)
* VisualStudio Code editor
* Backup (remote and local)
* MicroPython cross-compilation (ARM & ESP32)
* Mosquitto MQTT broker 
* Wireshark (analyze network traffic)
* Samba/CIFS server and client
* Update IDE from within (modify or add features, e.g. support for databases)
* Shell terminal window (with password free sudo)

Wouldn't the same software run on a laptop? Absolutely! Without Docker, compatibility could be an issue. For example, jupyter and the balena ide require different version of node. Docker solves this. However, in *ide49* most containers have to be run "privileged", giving them essentially root access. This may be an acceptable security risk on a dedicated device that does not store personal information, but a major concern on a computer used e.g. to do banking or store personal medical records. 

But isn't this slow? No. I moved all my MicroPython development (including compiling the interpreter) from an Intel I7 CPU to a Raspberry Pi 4 with 2 GB memory without noticing performance degradation relevant for my workflow. 