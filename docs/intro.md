# MicroPython IDE

*ide49* offers a comprehensive set of tools & growing list of examples for developing applications for microcontrollers with special support for [MicroPython](https://micropython.org/). The IDE runs on a dedicated computer (Raspberry PI or generic Intel/AMD processor). Each feature runs in a separate [Docker](https://www.docker.com/) container. All features - including installation - are available through a standard web browser - no need to install and maintain complex software on your laptop!

* Interactive MicroPython coding (Jupyter notebook or rshell)
    * auto-discover and program MicroPython devices
    * powerful file synchronization between the host and microcontrollers
    * wireless access (webrepl)
    * Compile the MicroPython virtual machine
* VisualStudio Code editor
* Backup facility (to remote server or local)
* Mosquitto MQTT broker 
* Wireshark (analyze network traffic)
* Samba/CIFS server and client
* Update IDE from within (modify or add features, e.g. support for databases)
* Shell terminal window (with password free sudo)

Wouldn't the same software run on a laptop? Absolutely! Without Docker, compatibility could be an issue. For example, jupyter and the balena ide require different versions of node. Docker solves this. However, in *ide49* most containers must be run in "privileged" mode, giving them essentially root access. This is an acceptable security risk on a dedicated device that does not store personal information, but a major concern on a computer used e.g. to do banking or store personal data. 

But isn't this slow? Not in my experience. I moved all my MicroPython development from an Intel i7 CPU to a Raspberry Pi 4 with 2 GB memory without noticing a performance degradation relevant for my workflow. 