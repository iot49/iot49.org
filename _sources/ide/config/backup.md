# Backup

All your files on the Raspberry PI are stored on the SD Card. These cards sometimes fail, or you may inadvertently delete a file. It's important to keep backups.

*ide49* makes this easy. It comes with [Duplicati](https://www.duplicati.com/), a versatile backup solution. Access it at https://iot49.local/duplicati or from the dashboard at https://iot49.local.

The first time you access Duplicati, you are asked


```{image} figures/duplicati_start.png
:width: 500px
```

Choose "No, my machine ..." to get to the home screen

```{image} figures/duplicati.png
:width: 500px
```

Click `+ Add backup` and configure a new backup. Choose Encryption and a Passphrase if you like (I do not bother as I don't keep personal information on the Raspberry PI).

Duplicati offers many backup destinations. Under `Storage Type` you find all the popular online services (Dropbox, Google Cloud, etc). 

Alternatively you can backup to local storage. Insert a USB thumb drive into the Raspberry PI. It will show up under `Folder path` in the `mnt` folder. 

```{image} figures/duplicati_dest.png
:width: 500px
```

If the drive does not show up, hit *Previous* and then again *Next*.

On the next screen, under `Computer`, choose the folder `service-config` as backup source. This will backup all user data on the Raspberry PI, but not the operating system and *ide49* application which can easily be reinstalled if lost or damaged.

```{image} figures/duplicati_src.png
:width: 350px
```

You can either run backups manually, or, preferably, automatically at a set schedule. This is my choice:

```{image} figures/duplicati_schedule.png
:width: 500px
```

That's it! If you ever loose data, come back to https://iot49.local/duplicati and run `Restore`. 