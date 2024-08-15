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
    AsyncStatus,
    DetectorControl,
    DetectorTrigger,
    DetectorWriter,
    SignalRW,
    StandardDetector,
    StandardFlyer,
)
from ophyd_async.fastcs.panda import HDFPanda

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

    return panda_async


panda1 = instantiate_panda_async(1)


file_loading_timer.stop_timer(__file__)
