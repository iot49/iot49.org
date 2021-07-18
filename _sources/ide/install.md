# Install

To install *ide49*, you need the following:

**Hardware:**

* Host device: one of
    * Raspberry Pi 4 (2GBytes suffice for *iot49*)
    * Raspberry Pi 3
    * Intel NUC or compatible
    
  Other devices supporting the 64-Bit ARM or Intel instruction set (`aarch64` or `amd64`) may work as well.
* SD Card with at least 16GBytes. A good quality card is highly recommended (Sandisk, Samsung, etc).
* A networked computer (e.g. a laptop) with an SD Card slot (only used for installation)

**Software:**

* Web-browser (e.g. Chrome)
* [Balena Etcher](https://www.balena.io/etcher/), available for Mac, Window, and Linux

## Download Balena OS

Create an account on [balena.io](https://www.balena.io/) or login to your existing account.

Open the [*ide49* repository on github](https://github.com/iot49/ide49) and click the 
![Deploy with Balena](figures/deploy.svg) button. 

In the popup window, choose a name for your application (e.g. *ide49*). Click *advanced* and set the timezone (TZ) to the desired value. Click [here](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones) for a list of valid TZ names. 

Leave the other variables at their defaults (they can be changed later) and click `Create and Deploy`. The browser is redirected to the Balena dashboard for the ide49 application. Click `+ Add device`. You get another popup:

* under edition, select `Development`
* click the `Wifi + Ethernet` button and enter your WiFi credentials

Accept the defaults for everything else and hit the `Download balenaOS` button. Keep the browser window open for checking progress later.

## Flash Balena OS to SD Card

Once the download finishes, start the [Balena Etcher](https://www.balena.io/etcher/) to flash the downloaded zip-file to an SD Card. Insert the card in your computer (laptop), click *Flash from file* and choose the *balena-cloud ... img.zip*, choose the SD Card as target and hit `Flash`. You may be asked to enter the administrator password to enable the flash.

## Install *ide49* on the Raspberry Pi

Remove the SD Card from the host and insert it into the Raspberry Pi, power up the device. It will automatically configure the OS. Head back to the browser window with the *Balena dashboard* and wait a few minutes for the new device to appear.

![Balena dashboard](figures/device_dashboard.png)

The new device has some creative name (like *hidden-sun*). Click on the device name. The top of the page show poetic device name. Click the pencil to change it. Also listed are some statistics of your Raspberry Pi (memory usage, device temperature, local ip address, etc). 

![Balena device status](figures/device_stats.png)

Click the application name in the Balena dashboard and wait for the release to complete (about twenty minutes). Once it's complete, the Raspberry Pi will automatically download it. You can see the progress in the device window with populates itself with a list of services. 

![Balena services](figures/balena_downloading.png)

After the download completes the application will automatically start.

```{toggle}
![Balena services](figures/services.png)
```

## Connect to the Raspberry Pi

Once the download completes and the application started (as indicated in the device dashboard), connect to the Raspberry Pi at http://iot49.local.

If this does not work, try http://LOCAL_IP_ADDRESS instead. Substitute the value *LOCAL_IP_ADDRESS* with the address shown on the device dashboard.

![ide49 Landing Page](figures/ide49_landing.png)

Click on `Jupyter`. You will get a warning similar to:

```{image} figures/browser_warning.png
:width: 500px
```

Click "Advanced" and then "proceed anyway". The page about [https & certificates](config/https) has information about this warning and explains how to eliminated it.

At the login window, enter the default username and password are (both *iot49*; [instructions for changing](config/password.ipynb)). 

<div style="font-size:15pt;font-weight:bold;text-align:center;color:green">Congratulations, you have completed the installation!</div>
</p>

![Jupyter](figures/jupyter.png)

Proceed to the next section, [Getting Started](getting-started).

## Turning off the Raspberry Pi

To turn off your Raspberry Pi don't just pull the power cord. Instead head to the dashboard on https://balena.io. At the top right is a button. Click it to get several options, including *shutdown*.
