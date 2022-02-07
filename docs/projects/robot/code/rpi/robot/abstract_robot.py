import asyncio, json, os, math
from asyncio_mqtt import Client
from abc import ABC
from struct import pack
from .comm import Comm
from .remote import Remote
from . import state as state_module
from . import pid as pid_module


MQTT_BROKER = os.getenv("HOST_IP")
TOPIC_ROOT = "public/vis"


class AbstractRobot(ABC):
    
    def __init__(self, enable_remote=False):
        self._comm = Comm(self._state_listener)
        self._remote = None
        self._mqtt_plot = None
        self.stop = False
        if enable_remote: self._remote = Remote(self.ble_event)

    #############################################################################
    # commands

    async def start(self, control='no_control'):
        await self._comm.start(control)

    async def stop(self):
        await self._comm.stop()

    async def ping_test(self):
        await self._comm.ping_test()

    async def echo_test(self, msg=bytearray(os.urandom(30))):
        await self._comm.echo_test(msg)

    #############################################################################
    # mqtt plot

    async def new_plot(self):
        return None

    async def update_plot(self):
        pass

    #############################################################################
    # state changes

    async def state_updated(self):
        pass

    async def _state_listener(self):
        await self.state_updated()
        if self._mqtt_plot:
            data = await self.update_plot()
            await self._mqtt_plot.publish(
                f"{TOPIC_ROOT}/bin", 
                pack(f'!{len(data)}f', *data)
            )


    #############################################################################
    # state

    async def set(self, name, value):
        """Set parameter value. See state_module.py for field names.
        
        Example: 
            set('FS', 100)
        """
        if name.isupper() and hasattr(state_module, name):
            idx = getattr(state_module, name)
            await self._comm.set(idx, value)      
            state_module.STATE[idx] = value
        else:
            raise NameError(f"state {name} does not exist")
            
    async def get(self, name):
        """Get state/parameter value. See state_module.py for field names.
        
        Example: 
            get('ODO_CM')
        """
        if name.isupper() and hasattr(state_module, name):
            return state_module.STATE[getattr(state_module, name)]
        else:
            raise NameError(f"state {name} does not exist")
            
    async def set_pid(self, pid_name, param_name, value):
        """Set PID parameter. See state_module.py / pid.py for field names.
        
        Example: 
            set('TACH_CM', 'KI', 2.1)
        """
        idx = self._pid_idx(pid_name, param_name)
        fs = state_module.STATE[state_module.FS]
        if param_name == 'KI': value /= fs
        if param_name == 'KD': value *= fs
        await self._comm.set(idx, value)      
        state_module.STATE[idx] = value
                            
    async def get_pid(self, pid_name, param_name):
        """Get PID parameter. See state_module.py / pid.py for field names.
        
        Example: 
            get('TACH_DIFF', 'U_MIN')
        """
        idx = self._pid_idx(pid_name, param_name)
        value = state_module.STATE[idx]
        fs = state_module.STATE[state_module.FS]
        if param_name == 'KI': value *= fs
        if param_name == 'KD': value /= fs
        return value
    
    async def check_state(self):
        """Verify that state on stm32 and rpi are equal"""
        for i, v_pi in enumerate(state_module.STATE):
            v_stm = await self._comm.get(i)
            assert math.isclose(v_pi, v_stm, rel_tol=1e-6, abs_tol=1e-6), f"state mismatch: {v_pi} != {v_stm}"

    async def get_all(self):
        """Update local state with state on stm32"""
        await self._comm.get_all()

    def _pid_idx(self, pid_name, param_name):
        pid_n = f"PID_{pid_name}"
        if not pid_n.isupper() or not hasattr(state_module, pid_n):
            raise NameError(f"pid {pid_name} does not exist")
        if not param_name.isupper() or not hasattr(pid_module, param_name):
            raise NameError(f"pid field {param_name} does not exist")
        fs = state_module.STATE[state_module.FS]
        assert not math.isnan(fs), "FS not set"
        return getattr(state_module, pid_n) + getattr(pid_module, param_name)        
                                                            

    #############################################################################
    # context handler

    async def __aenter__(self):
        self._comm = await self._comm.__aenter__()
        await self._comm.ping_test()
        await self._comm.get_all()
        # BLE remote
        if self._remote: await self._remote.__aenter__()
        # plotting
        plot = await self.new_plot()
        if plot and 'columns' in plot:
            self._mqtt_plot = await Client(MQTT_BROKER).__aenter__()
            await self._mqtt_plot.publish(f"{TOPIC_ROOT}/new", json.dumps(plot))
        return self

    async def __aexit__(self, *args):
        if self._remote:
            while not self._remote.stop:
                await asyncio.sleep(0.2)
        # exit services
        await self._comm.__aexit__(*args)
        if self._remote: await self._remote.__aexit__(*args)
        if self._mqtt_plot: await self._mqtt_plot.__aexit__(*args)
