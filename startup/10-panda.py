import time as ttime
from datetime import datetime
from threading import Thread

import bluesky.plan_stubs as bps
import bluesky.preprocessors as bpp
from bluesky import RunEngine
from bluesky.utils import ProgressBarManager
from epics import caget, caput
from ophyd import Component as Cpt
from ophyd import Device, EpicsMotor, EpicsPathSignal, EpicsSignal, EpicsSignalWithRBV


class DATA(Device):
    hdf_directory = Cpt(EpicsSignal, "HDFDirectory", string=True)
    hdf_file_name = Cpt(EpicsSignal, "HDFFileName", string=True)
    num_capture = Cpt(EpicsSignal, "NumCapture")
    flush_period = Cpt(EpicsSignal, "FlushPeriod")
    capture = Cpt(EpicsSignal, "Capture")
    capture_mode = Cpt(EpicsSignal, "CaptureMode", string=True)
    status = Cpt(EpicsSignal, "Status", string=True)


class PCOMP(Device):
    pre_start = Cpt(EpicsSignal, "PRE_START")
    start = Cpt(EpicsSignal, "START")
    width = Cpt(EpicsSignal, "WIDTH")
    step = Cpt(EpicsSignal, "STEP")
    pulses = Cpt(EpicsSignal, "PULSES")


class PCAP(Device):
    arm = Cpt(EpicsSignal, "ARM")
    active = Cpt(EpicsSignal, "ACTIVE")


class CLOCK(Device):
    period = Cpt(EpicsSignal, "PERIOD")
    period_units = Cpt(EpicsSignal, "PERIOD:UNITS")


class COUNTER(Device):
    start = Cpt(EpicsSignal, "START")
    step = Cpt(EpicsSignal, "STEP")
    max = Cpt(EpicsSignal, "MAX")
    min = Cpt(EpicsSignal, "MIN")


class INENC(Device):
    val = Cpt(EpicsSignal, "VAL")


class POSITION(Device):
    units = Cpt(EpicsSignal, "UNITS", string=True)
    scale = Cpt(EpicsSignal, "SCALE")
    offset = Cpt(EpicsSignal, "OFFSET")


class POSITIONS(Device):
    inenc1 = Cpt(POSITION, "12:")
    inenc2 = Cpt(POSITION, "13:")


class PULSE(Device):
    delay_units = Cpt(EpicsSignal, "DELAY:UNITS", string=True)
    delay = Cpt(EpicsSignal, "DELAY")
    width_units = Cpt(EpicsSignal, "WIDTH:UNITS", string=True)
    width = Cpt(EpicsSignal, "WIDTH")


class BITS(Device):
    A = Cpt(EpicsSignal, "A")
    B = Cpt(EpicsSignal, "B")
    C = Cpt(EpicsSignal, "C")
    D = Cpt(EpicsSignal, "D")


class PandA_Ophyd1(Device):
    pcap = Cpt(PCAP, "PCAP:")
    data = Cpt(DATA, "DATA:")
    pcomp1 = Cpt(PCOMP, "PCOMP1:")
    pcomp2 = Cpt(PCOMP, "PCOMP2:")
    clock1 = Cpt(CLOCK, "CLOCK1:")
    clock2 = Cpt(CLOCK, "CLOCK2:")
    counter1 = Cpt(COUNTER, "COUNTER1:")
    counter2 = Cpt(COUNTER, "COUNTER2:")
    counter3 = Cpt(COUNTER, "COUNTER3:")
    inenc1 = Cpt(INENC, "INENC1:")
    inenc2 = Cpt(INENC, "INENC2:")
    pulse2 = Cpt(PULSE, "PULSE2:")
    pulse3 = Cpt(PULSE, "PULSE3:")
    positions = Cpt(POSITIONS, "POSITIONS:")
    bits = Cpt(BITS, "BITS:")


pnd = PandA_Ophyd1(r"XF:31ID1-ES{PANDA:3}:", name="pnd")
# pnd = PandA_Ophyd1("PANDA:3:", name="pnd")  # Panda IOC fails to work with colons (":") in the PV name
# pnd = PandA_Ophyd1("XF31ID1-ES-PANDA-3:", name="pnd")
