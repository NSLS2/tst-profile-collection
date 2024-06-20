file_loading_timer.start_timer(__file__)


print(f"Loading file {__file__!r} ...")


import asyncio
from dataclasses import dataclass
from enum import Enum

from ophyd import EpicsSignalRO
from ophyd_async.core import (
    DEFAULT_TIMEOUT,
    DetectorControl,
    DetectorTrigger,
    DetectorWriter,
    DeviceCollector,
    HardwareTriggeredFlyable,
    ShapeProvider,
    SignalRW,
    TriggerInfo,
    TriggerLogic,
)
from ophyd_async.core.async_status import AsyncStatus
from ophyd_async.core.detector import StandardDetector
from ophyd_async.core.device import DeviceCollector
from ophyd_async.epics.areadetector.drivers.kinetix_driver import KinetixReadoutMode
from ophyd_async.epics.areadetector.kinetix import KinetixDetector

manta_trigger_logic = StandardTriggerLogic()


def instantiate_manta_async(manta_id):
    print(f"Connecting to manta device {manta_id}")
    with DeviceCollector():
        manta_path_provider = ProposalNumYMDPathProvder(default_filename_provider)
        manta_async = VimbaDriver(
            f"XF:31ID1-ES{{GigE-Cam:{manta_id}}}",
            manta_path_provider,
            name=f"manta-cam{manta_id}",
        )

    print("Done")
    return manta_async


manta1_async = instantiate_manta_asyncmanta_id(1)

manta_flyer = HardwareTriggeredFlyable(manta_trigger_logic, [], name="manta_flyer")


def manta_stage():
    yield from bps.stage(manta_standard_det)
    yield from bps.sleep(5)


def kinetix_stage(kinetix_detector):
    yield from bps.stage(kinetix_detector)
    yield from bps.sleep(5)


def inner_manta_collect(manta_detector):

    yield from bps.kickoff(manta_flyer)
    yield from bps.kickoff(manta_detector)

    yield from bps.complete(manta_flyer, wait=True, group="complete")
    yield from bps.complete(manta_detector, wait=True, group="complete")

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
            manta_detector,
            # stream=True,
            # return_payload=False,
            name=f"{manta_detector.name}_stream",
        )
        yield from bps.sleep(0.01)

    yield from bps.wait(group="complete")
    val = yield from bps.rd(manta_writer.hdf.num_captured)
    print(f"{val = }")


def manta_collect(manta_detector, num=10, exposure_time=0.1, software_trigger=True):

    manta_exp_setup = StandardTriggerSetup(
        num_images=num, exposure_time=exposure_time, software_trigger=software_trigger
    )

    yield from bps.open_run()

    yield from bps.stage_all(manta_detector, manta_flyer)

    yield from bps.prepare(manta_flyer, manta_exp_setup, wait=True)
    yield from bps.prepare(manta_detector, manta_flyer.trigger_info, wait=True)

    yield from inner_manta_collect()

    yield from bps.unstage_all(manta_flyer, manta_detector)

    yield from bps.close_run()


def _manta_collect_dark_flat(
    manta_detector, num=10, exposure_time=0.1, software_trigger=True
):

    manta_exp_setup = StandardTriggerSetup(
        num_images=num, exposure_time=exposure_time, software_trigger=software_trigger
    )

    yield from bps.open_run()

    yield from bps.stage_all(manta_detector, manta_flyer)

    yield from bps.prepare(manta_flyer, manta_exp_setup, wait=True)
    yield from bps.prepare(manta_detector, manta_flyer.trigger_info, wait=True)

    yield from inner_manta_collect()

    yield from bps.unstage_all(manta_flyer, manta_detector)

    yield from bps.close_run()


def manta_fly(
    num=10,
):  # Note: 724 points are specific for the "rotation_sim_04" panda config!
    yield from bps.stage_all(manta_standard_det, manta_flyer)
    assert manta_flyer._trigger_logic.state == TriggerState.stopping
    yield from bps.prepare(manta_flyer, num, wait=True)
    yield from bps.prepare(manta_standard_det, manta_flyer.trigger_info, wait=True)

    detector = manta_standard_det
    # detector.controller.disarm.assert_called_once  # type: ignore

    yield from bps.open_run()

    yield from bps.kickoff(manta_flyer)
    yield from bps.kickoff(detector)

    yield from bps.complete(manta_flyer, wait=True, group="complete")
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
            manta_standard_det,
            stream=True,
            return_payload=False,
            name="main_stream",
        )
        yield from bps.sleep(0.01)

    yield from bps.wait(group="complete")
    val = yield from bps.rd(manta_writer.hdf.num_captured)
    print(f"{val = }")
    yield from bps.close_run()

    yield from bps.unstage_all(manta_flyer, manta_standard_det)


file_loading_timer.stop_timer(__file__)
