# WiFi Coprocessor

Some CPUs or breakout boards come with built-in WiFi. But what if the chosen processor, e.g. an STM32 or nrf52, does not and it's needed for your IoT project?

The solution is to add a WiFi radio. This project uses an economical ESP32 to add WiFi. To minimize software development and hardware complexity, we'll run MicroPython on the ESP32 and communicate over a serial port with just two wires.