file_loading_timer.start_timer(__file__)


import asyncio
from dataclasses import dataclass
from enum import Enum

from ophyd_async.core import (
    DEFAULT_TIMEOUT,
    DetectorControl,
    DetectorTrigger,
    DetectorWriter,
    DeviceCollector,
    SignalRW,
    TriggerInfo,
    TriggerLogic,
)


class TomoFrameType(Enum):
    dark = "dark"
    flat = "flat"
    proj = "proj"


class StandardTriggerState(str, Enum):
    null = "null"
    preparing = "preparing"
    starting = "starting"
    completing = "completing"
    stopping = "stopping"


@dataclass
class StandardTriggerSetup:
    num_frames: int
    exposure_time: float
    trigger_mode: DetectorTrigger


def gen_software_trigger_setup(num_frames, exp_time):
    return StandardTriggerSetup(
        num_frames=num_frames,
        exposure_time=exp_time,
        trigger_mode=DetectorTrigger.internal,
    )


class StandardTriggerLogic(TriggerLogic[int]):
    def __init__(self):
        self.state = StandardTriggerState.null

    def trigger_info(self, setup) -> TriggerInfo:
        exposure = 0.1
        trigger = DetectorTrigger.internal
        num_images = setup
        if isinstance(setup, StandardTriggerSetup):
            trigger = setup.trigger_mode
            exposure = setup.exposure_time
            num_images = setup.num_frames
        return TriggerInfo(
            number=num_images,
            trigger=trigger,
            deadtime=0.1,
            livetime=exposure,
        )

    async def prepare(self, value: int):
        self.state = StandardTriggerState.preparing
        return value

    async def kickoff(self):
        self.state = StandardTriggerState.starting

    async def complete(self):
        self.state = StandardTriggerState.completing

    async def stop(self):
        self.state = StandardTriggerState.stopping


async def print_children(device):
    for name, obj in dict(device.children()).items():
        print(f"{name}: {await obj.read()}")


file_loading_timer.stop_timer(__file__)
