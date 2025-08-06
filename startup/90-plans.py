print(f"Loading file {__file__!r} ...")

import datetime

# Number of encoder counts for an entire revolution
COUNTS_PER_REVOLUTION = 8000
DEG_PER_REVOLUTION = 360
COUNTS_PER_DEG = COUNTS_PER_REVOLUTION / DEG_PER_REVOLUTION


from ophyd_async.core import TriggerInfo
from ophyd_async.epics.motor import FlyMotorInfo
# import pdb


def tomo_demo_async(
    detectors,
    panda,
    num_images=21,
    scan_time=9,
    start_deg=0,
    exposure_time=None,
):

    pcomp = panda.pcomp[1]

    step_width_counts = COUNTS_PER_REVOLUTION / (2 * (num_images - 1))
    if int(step_width_counts) != round(step_width_counts, 5):
        raise ValueError(
            "The number of encoder counts per pulse is not an integer value!"
        )

    step_time = scan_time / num_images
    if exposure_time is not None:
        if exposure_time > step_time:
            raise RuntimeError(
                f"Your configured exposure time is longer than the step size {step_time}"
            )
    else:
        exposure_time = step_time / 3

    all_detectors = [*detectors, panda]
    all_devices = [*all_detectors, rot_motor]

    det_trigger_info = TriggerInfo(
        number_of_triggers=num_images,
        livetime=exposure_time,
        deadtime=0.001,
        trigger=DetectorTrigger.EDGE_TRIGGER,
    )

    panda_trigger_info = TriggerInfo(
        number_of_triggers=num_images,
        livetime=exposure_time,
        deadtime=0.001,
        trigger=DetectorTrigger.CONSTANT_GATE,
    )

    rot_motor_fly_info = FlyMotorInfo(
        start_position=start_deg - 5,
        end_position=start_deg + DEG_PER_REVOLUTION / 2 + 5,
        time_for_move=scan_time,
    )

    start_encoder = start_deg * COUNTS_PER_DEG

    width_in_counts = (180 / scan_time) * COUNTS_PER_DEG * exposure_time
    if width_in_counts > step_width_counts:
        raise RuntimeError(
            f"Your specified exposure time of {exposure_time}s is too long! Calculated width: {width_in_counts}, Step size: {step_width_counts}"
        )
    print(f"Exposing camera for {width_in_counts} counts")

    # Set up the pcomp block
    yield from bps.mv(pcomp.start, int(start_encoder))

    # Uncomment if using gate trigger mode on camera
    # yield from bps.mv(
    #    panda3_pcomp_1.width, width_in_counts
    # )  # Width in encoder counts that the pulse will be high
    yield from bps.mv(pcomp.step, step_width_counts)
    yield from bps.mv(pcomp.pulses, num_images)

    yield from bps.open_run()

    # The setup below is happening in the VimbaController's arm method.
    # # Setup camera in trigger mode
    # yield from bps.mv(manta_async.trigger_mode, "On")
    # yield from bps.mv(manta_async.trigger_source, "Line1")
    # yield from bps.mv(manta_async.overlap, "Off")
    # yield from bps.mv(manta_async.expose_out_mode, "TriggerWidth")  # "Timed" or "TriggerWidth"

    # Stage All!
    yield from bps.stage_all(*all_devices)

    for det in detectors:
        yield from bps.prepare(det, det_trigger_info, group="prepare_all", wait=False)

    yield from bps.prepare(panda, panda_trigger_info, group="prepare_all", wait=False)

    yield from bps.prepare(
        rot_motor, rot_motor_fly_info, group="prepare_all", wait=False
    )

    yield from bps.wait(group="prepare_all")
    yield from bps.kickoff_all(*all_devices, wait=True)

    yield from bps.declare_stream(*all_detectors, name="tomo_stream")
    yield from bps.collect_while_completing(
        all_devices, all_detectors, flush_period=0.25, stream_name="tomo_stream"
    )

    yield from bps.unstage_all(*all_devices)

    yield from bps.close_run()

    panda_val = yield from bps.rd(panda.data.num_captured)
    print(f"{panda_val = } ")
    for det in detectors:
        manta_val = yield from bps.rd(det.fileio.num_captured)
        print(f"{det.name} = {manta_val} ")

    # Reset the velocity back to high.
    yield from bps.mv(rot_motor.velocity, 180 / 2)


# file_loading_timer.stop_timer(__file__)
