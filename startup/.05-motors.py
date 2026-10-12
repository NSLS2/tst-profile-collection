file_loading_timer.start_timer(__file__)

from ophyd_async.core import init_devices
from ophyd_async.epics.motor import Motor

with init_devices(mock=RUNNING_IN_NSLS2_CI):
    rot_motor = Motor("XF:31ID1-OP:1{CMT:1-Ax:Rot}Mtr", name="rot_motor")
    x_motor = Motor("XF:31ID1-OP:1{CMT:1-Ax:X}Mtr", name="x_motor")
    y_motor = Motor("XF:31ID1-OP:1{CMT:1-Ax:Y}Mtr", name="y_motor")
    z_motor = Motor("XF:31ID1-OP:1{CMT:1-Ax:Z}Mtr", name="z_motor")


file_loading_timer.stop_timer(__file__)
