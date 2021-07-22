# REPL prompt

To connect directly to the REPL of your microcontroller, launch a Terminal (click the blue `+` icon at the upper left of Jupyter Lab and then the Terminal icon). At the shell prompt type

```bash
picocom -b115200 /dev/ttyUSB0
```

```{toggle}
![REPL](figures/repl.png)
```