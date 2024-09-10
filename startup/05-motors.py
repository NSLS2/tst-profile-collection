file_loading_timer.start_timer(__file__)

from ophyd import Component as Cpt
from ophyd import EpicsMotor, EpicsSignal
from ophyd_async.epics.motor import Motor

# class EpicsMotorWithSPMG(EpicsMotor):
#     spmg = Cpt(EpicsSignal, ".SPMG")
#     velocity = Cpt(EpicsSignal, ".VELO")


# rot_motor = EpicsMotorWithSPMG("XF:31ID1-OP:1{CMT:1-Ax:X}Mtr", name="rot_motor")

with DeviceCollector():
    rot_motor = Motor("XF:31ID1-OP:1{CMT:1-Ax:Rot}Mtr", name="rot_motor")


file_loading_timer.stop_timer(__file__)
