# Install

## Overview

*ide49* is a [Balena Cloud](https://www.balena.io/cloud) application, a Docker framework customized for iot devices with limited resources.

To install *ide49*, you need the following:

**Hardware:**

* Host device: one of
    * Raspberry Pi 4 (2GBytes suffice for *iot49*)
    * Raspberry Pi 3
    * Intel NUC or compatible
    
  Other 64-Bit ARM or Intel CPUs (`aarch64` or `amd64`) may work as well.
* SD Card with at least 16GBytes. A good quality card is highly recommended (Sandisk, Samsung, etc).
    * Not needed for installation on Intel NUC or compatible
* A networked computer (e.g. a laptop) with an SD Card slot (only used for installation)

**Software:**

* Web-browser (e.g. Chrome)
    * All access is from a browser
* [Balena Etcher](https://www.balena.io/etcher/), available for Mac, Window, and Linux
    * Used only for installation
    
You can either a "quick install" of the precompiled application or a "custom installation" from source code. The first approach, described below, is faster and recommended especially for new users. Alternatively, do a [custom installation](install-custom.ipynb) if you plan to modify *ide49*. 

You can also do a custom installation at a later stage. The Raspberry PI makes this particularly simple - just install to a different SD Card to quickly switch between the two versions.

## Quick Install

Go to https://hub.balena.io/balenalabs/ide49 and click "Get started". Select your device type and network connection. Then hit the download button. 

If you have a **Raspberry PI**, flash the downloaded OS image to the SD Card using [Balena Etcher](https://www.balena.io/etcher/). Insert the Card into the PI. 

**Intel NUC** or compatibles typically install the OS from a thumb drive or other external medium to the internal disk. Follow the [instructions](https://www.balena.io/os/docs/intel-nuc/getting-started) at the Balena website.

Once the OS is installed *ide49* will download and install automatically. Depending on the networks speed, this may take upwards of ten minutes (or an hour with my glacially slow Internet). After the download completes *ide49* starts automatically. Connect with a browser at http://iot49.local.

If this does not work, try http://LOCAL_IP_ADDRESS instead. Substitute the value *LOCAL_IP_ADDRESS* with the address shown on the device dashboard.

![ide49 Landing Page](figures/ide49_landing.png)

Click on `Jupyter`. You will get a warning similar to:

```{image} figures/browser_warning.png
:width: 500px
```

Click "Advanced" and then "proceed anyway". The page [https & certificates](config/https) has information about this warning and explains how to get rid of it.

At the login window, enter the default username and password (both *iot49*; [instructions for changing](config/password.ipynb)). 

<div style="font-size:15pt;font-weight:bold;text-align:center;color:green">Congratulations, you have completed the installation!</div>
</p>

![Jupyter](figures/jupyter.png)

Proceed to the next section, [Getting Started](getting-started).

## Shutdown

To turn off your computer don't just pull the power cord. Instead head to the dashboard on https://balena.io. At the top right is a button. Click it to get several options, including *shutdown*.
