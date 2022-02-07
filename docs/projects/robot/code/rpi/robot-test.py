from example_robot import main
import stm32

stm32.hard_reset(quiet=False)
import time
time.sleep(0.5)
stm32.rsync()

main()

