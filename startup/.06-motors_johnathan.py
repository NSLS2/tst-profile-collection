from ophyd_async.core import init_devices
from ophyd_async.epics.motor import Motor
from ophyd import EpicsMotor
from scanspec.specs import Spiral, Line
from bluesky.plans import list_scan
from ophyd.sim import det



x_motor = EpicsMotor("XF:31ID1-OP:1{CMT:1-Ax:X}Mtr", name="x_motor")
y_motor = EpicsMotor("XF:31ID1-OP:1{CMT:1-Ax:Y}Mtr", name="y_motor")
z_motor = EpicsMotor("XF:31ID1-OP:1{CMT:1-Ax:Z}Mtr", name="z_motor")
 
