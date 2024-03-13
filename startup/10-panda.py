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
    param_name = Cpt(EpicsSignal, "NAME", string=True)
    value = Cpt(EpicsSignal, "VAL")
    units = Cpt(EpicsSignal, "UNITS", string=True)
    scale = Cpt(EpicsSignal, "SCALE")
    offset = Cpt(EpicsSignal, "OFFSET")
    capture = Cpt(EpicsSignal, "CAPTURE", string=True)


class POSITIONS(Device):
    calc1 = Cpt(POSITION, "0:")
    calc2 = Cpt(POSITION, "1:")
    counter1 = Cpt(POSITION, "2:")
    counter2 = Cpt(POSITION, "3:")
    counter3 = Cpt(POSITION, "4:")
    counter4 = Cpt(POSITION, "5:")
    counter5 = Cpt(POSITION, "6:")
    counter6 = Cpt(POSITION, "7:")
    counter7 = Cpt(POSITION, "8:")
    counter8 = Cpt(POSITION, "9:")
    filter1 = Cpt(POSITION, "10:")
    filter2 = Cpt(POSITION, "11:")
    fmc_in1 = Cpt(POSITION, "12:")
    fmc_in2 = Cpt(POSITION, "13:")
    fmc_in3 = Cpt(POSITION, "14:")
    fmc_in4 = Cpt(POSITION, "15:")
    fmc_in5 = Cpt(POSITION, "16:")
    fmc_in6 = Cpt(POSITION, "17:")
    fmc_in7 = Cpt(POSITION, "18:")
    fmc_in8 = Cpt(POSITION, "19:")
    inenc1 = Cpt(POSITION, "20:")
    inenc2 = Cpt(POSITION, "21:")
    inenc3 = Cpt(POSITION, "22:")
    inenc4 = Cpt(POSITION, "23:")
    pgen1 = Cpt(POSITION, "24:")
    pgen2 = Cpt(POSITION, "25:")
    spf3_pos1 = Cpt(POSITION, "26:")
    spf3_pos2 = Cpt(POSITION, "27:")
    spf3_pos3 = Cpt(POSITION, "28:")
    spf3_pos4 = Cpt(POSITION, "29:")


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


print(f"Loading file {__file__!r} ...")


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


import asyncio

from ophyd_async.core import StaticDirectoryProvider
from ophyd_async.core.device import DeviceCollector
from ophyd_async.panda.panda import PandA
from ophyd_async.panda.writers import PandaHDFWriter


async def instantiate_panda_async():
    async with DeviceCollector():
        panda3_async = PandA("XF:31ID1-ES{PANDA:3}", name="panda3_async")

    async with DeviceCollector():
        dir_prov = StaticDirectoryProvider(PROPOSAL_DIR, "test-ophyd-async3")
        writer3 = PandaHDFWriter(
            "XF:31ID1-ES{PANDA:3}",
            dir_prov,
            lambda: "test-panda",
            panda_device=panda3_async,
        )

    for name, obj in dict(panda3_async.data.children()).items():
        print(f"{name}: {await obj.read()}")

    return panda3_async, writer3


panda3_async, writer3 = asyncio.run(instantiate_panda_async())


def count_async_panda(panda_device, writer):
    asyncio.wait(writer.open())
    yield from bps.mv(panda_device.pcap.arm, 1)
    yield from bps.sleep(5)
    yield from bps.mv(panda_device.pcap.arm, 0)
    yield from bps.sleep(1)
    asyncio.wait(writer.close())
