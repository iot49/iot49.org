# WiFi Coprocessor

Some CPUs or breakout boards come with built-in WiFi. But what if the chosen target processor, e.g. an STM32 or nrf52, does not and it's needed for your IoT project?

The solution is to add a WiFi radio. This project uses an economical ESP32 to add WiFi to the target processor. To minimize software development and hardware complexity, we'll run MicroPython on the ESP32 and communicate with the target over a serial port with just two wires.


This project and code are located at `$IOT_PROJECTS/wifi-cop`.