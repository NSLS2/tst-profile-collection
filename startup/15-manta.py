file_loading_timer.start_timer(__file__)


print(f"Loading file {__file__!r} ...")


import asyncio
from dataclasses import dataclass
from enum import Enum

from ophyd import EpicsSignalRO
from ophyd_async.core import (
    DEFAULT_TIMEOUT,
    DetectorController,
    DetectorTrigger,
    DetectorWriter,
    DeviceCollector,
    SignalRW,
    TriggerInfo,
)
from ophyd_async.epics.advimba import VimbaDetector

manta_trigger_logic = StandardTriggerLogic()
manta_flyer = StandardFlyer(manta_trigger_logic, name="manta_flyer")


def instantiate_manta_async(manta_id):
    print(f"Connecting to manta device {manta_id}")
    with DeviceCollector():
        manta_path_provider = ProposalNumYMDPathProvider(default_filename_provider)
        manta_async = VimbaDetector(
            f"XF:31ID1-ES{{GigE-Cam:{manta_id}}}",
            manta_path_provider,
            name=f"manta-cam{manta_id}",
        )

    print("Done")
    return manta_async


manta1 = instantiate_manta_async(1)
manta2 = instantiate_manta_async(2)

# warmup_hdf_plugins([manta1, manta2])


file_loading_timer.stop_timer(__file__)
