# Custom Install

*Skip this if you did the quick install.*

These instructions are for installing *ide49* from source. The installation is fully configurable, including modifying and adding/removing Docker containers - all from within *ide49*.

## Download Balena OS

Create an account on [balena.io](https://www.balena.io/) or login to your existing account.

Open the [*ide49* repository on github](https://github.com/iot49/ide49) and click the 
![Deploy with Balena](figures/deploy.svg) button. 

In the popup window, choose a name for your application (e.g. *ide49*). Click *advanced* and set the timezone (TZ) to the desired value. Click [here](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones) for a list of valid TZ names. 

Leave the other variables at their defaults (they can be changed later) and click `Create and Deploy`. The browser is redirected to the Balena dashboard for the ide49 application. Click `+ Add device`. You get another popup:

* under edition, select `Development`
* click the `Wifi + Ethernet` button and enter your WiFi credentials

Accept the defaults for everything else and hit the `Download balenaOS` button. Keep the browser window open for checking progress later.

## Install Balena OS

### Raspberry PI

Once the download finishes, start the [Balena Etcher](https://www.balena.io/etcher/) to flash the downloaded zip-file to an SD Card. Insert the card in your computer (laptop), click *Flash from file* and choose the *balena-cloud ... img.zip*, choose the SD Card as target and hit `Flash`. You may be asked to enter the administrator password to enable the flash.

Remove the SD Card from the host and insert it into the Raspberry Pi.

### Intel NUC

Intel NUC or compatibles typically install the OS from a thumb drive or other external medium to the internal disk. Detailed instructions are [here](https://www.balena.io/os/docs/intel-nuc/getting-started/).

## Install *ide49*

Power up the device. It will automatically configure the OS. Head back to the browser window with the *Balena dashboard* and wait a few minutes for the new device to appear.

![Balena dashboard](figures/device_dashboard.png)

The new device has some creative name (like *hidden-sun*). Click on the device name. The top of the page show poetic device name. Click the pencil to change it. Also listed are some statistics (memory usage, device temperature, local ip address, etc). 

![Balena device status](figures/device_stats.png)

Click the application name in the Balena dashboard and wait for the release to complete (about twenty minutes). Once it's complete, the Balena will automatically download *ide49*. You can see the progress in the device window with populates itself with a list of services. 

![Balena services](figures/balena_downloading.png)

After the download completes the application will automatically start.

```{toggle}
![Balena services](figures/services.png)
```

Follow the install in the *Balena dashboard*. Once all containers are downloaded connect to the IDE at http://iot49.local.

If this does not work, try http://LOCAL_IP_ADDRESS instead. Substitute the value *LOCAL_IP_ADDRESS* with the address shown on the device dashboard.
