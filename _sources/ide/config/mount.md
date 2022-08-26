# Mount USB Drive

## Warning

**The Duplcati backup service** auto-mounts compatible drives. Data corruption will occur if the same drive is accessed from several services simultaneously.


## Find Device Name

Plug the drive into an available USB port. Then run

```bash
sudo fdisk -l 
```

and take note of the device name, e.g. `/dev/sdb1`.

## Mount Device

```bash
sudo mount  -t exfat -o rw /dev/sdb1 /mnt
```

Replace the device type (`exfat`) with the appropriate value for your drive and substitute the  device name obtained in the previous step. `/mnt` is the directory under which the contents of the drive will be available. You can specify a different value, but the directory must exist.

## Copy Contents

To copy contents from one drive (or location) to another, use `rsync`. E.g.

```bash
rsync -au --progress --exclude=".*" /src/ /dst/
```

where `/src/` (e.g. `/mnt/`) and `/dst/` are the source and destination directories. If `rsync` is interrupted or the contents on `/src/`, run `rsync` again to make `/dst/` an exact copy of `/src/`.

The optional `--exclude=".*"` excludes all files starting with a dot. Use the `--dry-run` flag to only see the actions to be performed without actually making any changes.