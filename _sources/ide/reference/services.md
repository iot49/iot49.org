# Services

*ide49* is a [docker application](https://www.docker.com/products/docker-app) on [balenaOS](https://www.balena.io/docs/reference/OS/overview/2.x/). Each "service" shown in the Balena dashboard represents a separate container with its own copy of Linux.

![Balena services](../figures/services.png)

* [Jupyter](../micropython/iot-kernel.ipynb) is a [code execution environment](https://jupyter.org/) that is quite popular among datascientists and is also a great option for interacting with and programming microcontrollers.
* Editor is an Internet enabled version of [Microsoft Visual Studio Code](https://code.visualstudio.com/), a powerful coding environment.
* [Backup](services/backup.ipynb) does what the name says.
* [Nginx](services/nginx.ipynb) is a [webbrowser](https://www.nginx.com/). In *ide49* it acts as a reverse proxy forwarding requests on the external network (ports 80 and 443) to the internal network and handles encryption and password protection. Nginx also serves *ide49* the landing page.

The other options are more specialized.

* [Plotserver](services/plotserver.ipynb) plots data received via MQTT in a browser window. It is a convenient solution to monitor data produced by microcontrollers that implement an MQTT client.
* [Balena CLI](services/balena-cli.ipynb) is the tool used to create and modify applications such as *ide49*. It lets you change *ide49* right from *ide49* itself!

Additional services provided by *ide49*:

* [mosquitto](services/mosquitto.ipynb), an MQTT broker.
* [Samba/CIFS file server](services/samba.ipynb) that exports user data stored on the Raspberry Pi. It is disabled by default.
* [arm32](services/arm32.ipynb) used to compile MicroPython and other microcontroller applications written in C/C++.
* [esp-idf](services/esp-idf.ipynb): build MicroPython for ESP32.

Services communicate via shared data and over an internal network used by the `%%service%` magic of the [`IOT Kernel`](../micropython/iot-kernel.ipynb).
