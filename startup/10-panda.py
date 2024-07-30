print(f"Loading file {__file__!r} ...")

import asyncio
import datetime
import json
import time as ttime
from enum import Enum
from pathlib import Path
from threading import Thread
from typing import AsyncGenerator, AsyncIterator, Dict, List, Optional

import bluesky.plan_stubs as bps
import bluesky.preprocessors as bpp
from bluesky import RunEngine
from bluesky.utils import ProgressBarManager
from epics import caget, caput
from ophyd import Component as Cpt
from ophyd import Device, EpicsMotor, EpicsPathSignal, EpicsSignal, EpicsSignalWithRBV
from ophyd_async.core import (
    DEFAULT_TIMEOUT,
    DetectorControl,
    DetectorTrigger,
    DetectorWriter,
    HardwareTriggeredFlyable,
    SignalRW,
    SimSignalBackend,
    StaticDirectoryProvider,
    TriggerInfo,
    TriggerLogic,
    UUIDDirectoryProvider,
)
from ophyd_async.core.async_status import AsyncStatus
from ophyd_async.core.detector import StandardDetector
from ophyd_async.core.device import DeviceCollector
from ophyd_async.panda.panda import PandA
from ophyd_async.panda.panda_controller import PandaPcapController
from ophyd_async.panda.writers import PandaHDFWriter


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


##########################################################################
#                         _       ____                                   #
#                        | |     |___ \                                  #
#   _ __   __ _ _ __   __| | __ _  __) |_____ __ _ ___ _   _ _ __   ___  #
#  | '_ \ / _` | '_ \ / _` |/ _` ||__ <______/ _` / __| | | | '_ \ / __| #
#  | |_) | (_| | | | | (_| | (_| |___) |    | (_| \__ \ |_| | | | | (__  #
#  | .__/ \__,_|_| |_|\__,_|\__,_|____/      \__,_|___/\__, |_| |_|\___| #
#  | |                                                  __/ |            #
#  |_|                                                 |___/             #
#                                                                        #
##########################################################################


async def print_children(device):
    for name, obj in dict(device.children()).items():
        print(f"{name}: {await obj.read()}")


panda_trigger_logic = StandardTriggerLogic(trigger_mode=DetectorTrigger.constant_gate)
panda_flyer = HardwareTriggeredFlyable(panda_trigger_logic, [], name="panda_flyer")


def instantiate_panda_async(panda_id):
    print(f"Connecting to PandA #{panda_id}")
    with DeviceCollector():
        panda_path_provider = ProposalNumYMDPathProvider(default_filename_provider)
        panda_async = HDFPanda(
            f"XF:31ID1-ES{{PANDA:{panda_id}}}:",
            panda_path_provider,
            name=f"panda{panda_id}_async",
        )
        # print_children(panda_async)
    print("Done.")

    return panda_async


panda3_async = instantiate_panda_async(3)


@AsyncStatus.wrap
async def openw(writer):
    describe = await writer.open()


@AsyncStatus.wrap
async def closew(writer):
    await writer.close()


def panda_fly(panda, num=724):
    yield from bps.stage_all(panda, panda_flyer)
    yield from bps.prepare(panda_flyer, num, wait=True)
    yield from bps.prepare(
        panda, panda_flyer.trigger_logic.trigger_info(num), wait=True
    )

    detector = panda
    # detector.controller.disarm.assert_called_once  # type: ignore

    yield from bps.open_run()

    yield from bps.kickoff(panda_flyer)
    yield from bps.kickoff(detector)

    yield from bps.complete(panda_flyer, wait=True, group="complete")
    yield from bps.complete(detector, wait=True, group="complete")

    # Manually incremenet the index as if a frame was taken
    # detector.writer.index += 1

    done = False
    while not done:
        try:
            yield from bps.wait(group="complete", timeout=0.5)
        except TimeoutError:
            pass
        else:
            done = True
        yield from bps.collect(
            panda,
            # stream=False,
            # return_payload=False,
            name="main_stream",
        )
        yield from bps.sleep(0.01)
    yield from bps.wait(group="complete")
    val = yield from bps.rd(panda.data.num_captured)
    print(f"{val = }")
    yield from bps.close_run()

    yield from bps.unstage_all(panda_flyer, panda)


file_loading_timer.stop_timer(__file__)
