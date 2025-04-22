file_loading_timer.start_timer(__file__)


print(f"Loading file {__file__!r} ...")


import asyncio
from dataclasses import dataclass
from enum import Enum

from ophyd_async.epics.advimba import VimbaDetector


def instantiate_manta_async(manta_id):
    print(f"Connecting to manta device {manta_id}")
    with init_devices(mock=RUNNING_IN_NSLS2_CI):
        manta_async = VimbaDetector(
            f"XF:31ID1-ES{{GigE-Cam:{manta_id}}}",
            TSTPathProvider(RE.md),
            name=f"manta{manta_id}",
        )

    print("Done")
    return manta_async


manta1 = instantiate_manta_async(1)
manta2 = instantiate_manta_async(2)

# warmup_hdf_plugins([manta1, manta2])


file_loading_timer.stop_timer(__file__)
