print(f"Loading file {__file__!r} ...")

import datetime

# Number of encoder counts for an entire revolution
COUNTS_PER_REVOLUTION = 8000
DEG_PER_REVOLUTION = 360
COUNTS_PER_DEG = COUNTS_PER_REVOLUTION / DEG_PER_REVOLUTION


from ophyd_async.core import TriggerInfo
from ophyd_async.epics.motor import FlyMotorInfo


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


def xas_demo_async(
    panda,
    detector,
    npoints,
    total_time,
    start_e,
    end_e,
    #    num_images=21,
    #    scan_time=9,
    #    start_deg=0,
    #    exposure_time=None,
):

    start_deg = start_e
    end_deg = end_e

    panda_pcomp1 = panda.pcomp[1]
    panda_pcap1 = panda.pcap
    panda_clock1 = panda.clock[1]

    reset_time = 0.001  # [ms], 1 us difference is usually enough

    clock_period_ms = total_time * 1000 / npoints  # [ms]
    clock_width_ms = clock_period_ms - reset_time

    target_velocity = (end_deg - start_deg) / total_time  # [deg/s]

    # PRE_START -> 0
    # START     -> prestart_cnt
    # WIDTH     -> end_cnt - start_cnt

    pre_start_deg = 5.0  # [deg], we are working in relative mode, zero is the position where pcomp was enabled
    pre_start_cnt = pre_start_deg * COUNTS_PER_DEG

    start_cnt = pre_start_cnt
    width_deg = end_deg - start_deg
    width_cnt = width_deg * COUNTS_PER_DEG

    print(f"{pre_start_cnt=}, {width_deg=}, {width_cnt=}")

    # step_width_counts = COUNTS_PER_REVOLUTION / (2 * (num_images - 1))
    # if int(step_width_counts) != round(step_width_counts, 5):
    # raise ValueError(
    # "The number of encoder counts per pulse is not an integer value!"
    # )

    #    step_time = scan_time / num_images
    #    if exposure_time is not None:
    #        if exposure_time > step_time:
    #            raise RuntimeError(
    #                f"Your configured exposure time is longer than the step size {step_time}"
    #            )

    panda_devices = [panda, panda_flyer]
    all_devices = panda_devices

    if detector:
        detector_devices = [detector, manta_flyer]
        all_devices = panda_devices + detector_devices
    # TODO: DO WE NEED THIS?
    det_exp_setup = StandardTriggerSetup(
        num_frames=npoints,  # num_images,
        exposure_time=clock_width_ms,  # exposure_time,
        trigger_mode=DetectorTrigger.edge_trigger,
    )

    panda_exp_setup = StandardTriggerSetup(
        num_frames=npoints,  # num_images,
        exposure_time=clock_width_ms,  # exposure_time,
        trigger_mode=DetectorTrigger.constant_gate,
    )

    yield from bps.mv(
        rot_motor.velocity, 180 / 2
    )  # Make it fast to move to the start position
    yield from bps.mv(rot_motor, start_deg - pre_start_deg)
    yield from bps.mv(
        rot_motor.velocity, target_velocity  # 180 / scan_time
    )  # Set the velocity for the scan
    # start_encoder = start_deg * COUNTS_PER_DEG

    # width_in_counts = (180 / scan_time) * COUNTS_PER_DEG * exposure_time
    # if width_in_counts > step_width_counts:
    # raise RuntimeError(
    # f"Your specified exposure time of {exposure_time}s is too long! Calculated width: {width_in_counts}, Step size: {step_width_counts}"
    # )
    # print(f"Exposing camera for {width_in_counts} counts")

    yield from bps.mv(
        panda_pcomp1.enable, "ZERO"
    )  # disabling pcomp, we'll enable it right before the start

    # print("SEETING UP PCOMP")

    # print("Current PCOMP start:", panda_pcomp1.start)
    # print("Current PCOMP width:", panda_pcomp1.width)
    # Set up the pcomp block
    yield from bps.mv(panda_pcomp1.start, int(start_cnt))
    yield from bps.mv(panda_pcomp1.width, int(width_cnt))

    print("READY TO GO", datetime.datetime.now().strftime("%H:%M:%S"))

    # Uncomment if using gate trigger mode on camera
    # yield from bps.mv(
    #    panda3_pcomp_1.width, width_in_counts
    # )  # Width in encoder counts that the pulse will be high
    # yield from bps.mv(panda_pcomp1.step, step_width_counts)
    # yield from bps.mv(panda_pcomp1.pulses, num_images)  # TODO: CHECK

    yield from bps.mv(panda_clock1.period, clock_period_ms)
    yield from bps.mv(panda_clock1.period_units, "ms")
    yield from bps.mv(panda_clock1.width, clock_width_ms)
    yield from bps.mv(panda_clock1.width_units, "ms")
    print("000: panda clock configured, ", datetime.datetime.now().strftime("%H:%M:%S"))
    yield from bps.open_run()
    print("001: run open,", datetime.datetime.now().strftime("%H:%M:%S"))
    if detector:
        detector._writer._path_provider._filename_provider.set_frame_type(
            TomoFrameType.proj
        )
    print("002: detector filename set, ", datetime.datetime.now().strftime("%H:%M:%S"))
    # The setup below is happening in the VimbaController's arm method.
    # # Setup camera in trigger mode
    # yield from bps.mv(manta_async.trigger_mode, "On")
    # yield from bps.mv(manta_async.trigger_source, "Line1")
    # yield from bps.mv(manta_async.overlap, "Off")
    # yield from bps.mv(manta_async.expose_out_mode, "TriggerWidth")  # "Timed" or "TriggerWidth"

    # Stage All!
    yield from bps.stage_all(*all_devices)
    print("003: staging complete, ", datetime.datetime.now().strftime("%H:%M:%S"))
    if detector:
        yield from bps.mv(detector._writer.hdf.num_capture, npoints)
        yield from bps.prepare(manta_flyer, det_exp_setup, wait=True)
        yield from bps.prepare(
            detector, manta_flyer.trigger_logic.trigger_info(det_exp_setup), wait=True
        )
        print(
            "004: manta flyer prepare complete, ",
            datetime.datetime.now().strftime("%H:%M:%S"),
        )
    yield from bps.prepare(panda_flyer, npoints, wait=True)
    yield from bps.prepare(
        panda, panda_flyer.trigger_logic.trigger_info(panda_exp_setup), wait=True
    )
    print(
        "005: panda flyer prepare complete, ",
        datetime.datetime.now().strftime("%H:%M:%S"),
    )

    for device in all_devices:
        yield from bps.kickoff(device)
    print("007: kickoff complete, ", datetime.datetime.now().strftime("%H:%M:%S"))

    # yield from bps.sleep(0.1)
    yield from bps.mv(panda_pcomp1.enable, "ONE")
    yield from bps.mv(
        rot_motor, end_deg + pre_start_deg
    )  # Aiming beyond the end point to maintain constant veolcity
    print("006: motor mv start, ", datetime.datetime.now().strftime("%H:%M:%S"))

    for flyer_or_panda in panda_devices:
        yield from bps.complete(flyer_or_panda, wait=True, group="complete_panda")
    print("008: panda complete, ", datetime.datetime.now().strftime("%H:%M:%S"))
    if detector:
        for flyer_or_det in detector_devices:
            yield from bps.complete(flyer_or_det, wait=True, group="complete_detector")
        print("009: detector complete, ", datetime.datetime.now().strftime("%H:%M:%S"))
    # Manually incremenet the index as if a frame was taken
    # detector.writer.index += 1
    print("ACQUISITION COMPLETE", datetime.datetime.now().strftime("%H:%M:%S"))

    # Wait for completion of the PandA HDF5 file saving.
    done = False
    while not done:
        try:
            yield from bps.wait(group="complete_panda", timeout=0.5)
        except TimeoutError:
            pass
        else:
            done = True

        panda_stream_name = f"{panda.name}_stream"
        yield from bps.declare_stream(panda, name=panda_stream_name)

        yield from bps.collect(
            panda,
            # stream=True,
            # return_payload=False,
            name=panda_stream_name,
        )
    print("PANDA FILE SAVING COMPLETE")
    yield from bps.unstage_all(*panda_devices)
    yield from bps.mv(panda_pcomp1.enable, "ZERO")
    print("PANDA UNSTAGING COMPLETE")

    # Wait for completion of the AD HDF5 file saving.
    done = False if detector else True
    while not done:
        try:
            yield from bps.wait(group="complete_detector", timeout=0.5)
        except TimeoutError:
            pass
        else:
            done = True

        detector_stream_name = f"{detector.name}_stream"
        yield from bps.declare_stream(detector, name=detector_stream_name)

        yield from bps.collect(
            detector,
            # stream=True,
            # return_payload=False,
            name=detector_stream_name,
        )
        yield from bps.sleep(0.01)
        print("AD HDF5 SAVED")
    yield from bps.close_run()

    panda_val = yield from bps.rd(panda.data.num_captured)
    print(f"{panda_val = }")
    if detector:
        manta_val = yield from bps.rd(detector._writer.hdf.num_captured)
        print(f"{manta_val = }")

        yield from bps.unstage_all(*detector_devices)

    # Reset the velocity back to high.
    yield from bps.mv(rot_motor.velocity, 180 / 2)


# file_loading_timer.stop_timer(__file__)
