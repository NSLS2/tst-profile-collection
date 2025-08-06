print(f"Loading file {__file__!r} ...")

import datetime


def xas_demo_async(
    panda,
    detectors,
    npoints,
    total_time,
    start_e,
    end_e
):

    start_deg = start_e
    end_deg = end_e

    panda_pcomp1 = panda.pcomp[1]
    # panda_pcap1 = panda.pcap
    panda_clock1 = panda.clock[1]

    reset_time = 0.001  # [ms], 1 us difference is usually enough
    
    clock_period_ms = total_time * 1000 / npoints  # [ms]
    clock_width_ms = clock_period_ms - reset_time 
    
    target_velocity = (end_deg-start_deg) / total_time  # [deg/s]
 
    # PRE_START -> 0
    # START     -> prestart_cnt
    # WIDTH     -> end_cnt - start_cnt

    pre_start_deg = 5.  # [deg], we are working in relative mode, zero is the position where pcomp was enabled
    pre_start_cnt = pre_start_deg * COUNTS_PER_DEG

    start_cnt = pre_start_cnt 
    width_deg = end_deg - start_deg
    width_cnt = width_deg * COUNTS_PER_DEG

    print(f"{pre_start_cnt=}, {width_deg=}, {width_cnt=}")

    all_detectors = [*detectors, panda]
    all_devices = [*all_detectors, rot_motor]

    det_trigger_info = TriggerInfo(
        number_of_triggers=npoints,
        livetime=clock_width_ms*0.001,
        deadtime=reset_time*0.001,
        trigger=DetectorTrigger.EDGE_TRIGGER,
    )

    panda_trigger_info = TriggerInfo(
        number_of_triggers=npoints,
        livetime=clock_width_ms*0.001,
        deadtime=reset_time*0.001,
        trigger=DetectorTrigger.CONSTANT_GATE,
    )

    rot_motor_fly_info = FlyMotorInfo(
        start_position=start_deg - 5,
        end_position=start_deg + DEG_PER_REVOLUTION / 2 + 5,
        time_for_move=total_time,
    )


    yield from bps.mv(
        rot_motor.velocity, 180 / 2
    )  # Make it fast to move to the start position
    yield from bps.mv(rot_motor, start_deg - pre_start_deg)
    yield from bps.mv(
        rot_motor.velocity, target_velocity #180 / scan_time
    )  # Set the velocity for the scan
 
    yield from bps.mv(panda_pcomp1.enable, "ZERO")  # disabling pcomp, we'll enable it right before the start

    # Set up the pcomp block
    yield from bps.mv(panda_pcomp1.start, int(start_cnt))
    yield from bps.mv(panda_pcomp1.width, int(width_cnt))

    # print("READY TO GO", datetime.datetime.now().strftime("%H:%M:%S"))

    yield from bps.mv(panda_clock1.period, clock_period_ms)
    yield from bps.mv(panda_clock1.period_units, "ms")
    yield from bps.mv(panda_clock1.width, clock_width_ms)
    yield from bps.mv(panda_clock1.width_units, "ms")
    # print("000: panda clock configured, ", datetime.datetime.now().strftime("%H:%M:%S"))
    yield from bps.open_run()

    # Stage All!
    yield from bps.stage_all(*all_devices)
    # print("003: staging complete, ", datetime.datetime.now().strftime("%H:%M:%S"))
 
    for det in detectors:
        yield from bps.prepare(det, det_trigger_info, group="prepare_all", wait=False)

    yield from bps.prepare(panda, panda_trigger_info, group="prepare_all", wait=False)

    yield from bps.prepare(
        rot_motor, rot_motor_fly_info, group="prepare_all", wait=False
    )

    yield from bps.wait(group="prepare_all")
    yield from bps.kickoff_all(*all_devices, wait=True)

    yield from bps.declare_stream(*all_detectors, name="xas_stream")
    yield from bps.collect_while_completing(
        all_devices, all_detectors, flush_period=0.25, stream_name="xas_stream"
    )

    yield from bps.unstage_all(*all_devices)
    yield from bps.mv(panda_pcomp1.enable, "ZERO")
    yield from bps.close_run()

    panda_val = yield from bps.rd(panda.data.num_captured)
    print(f"{panda_val = } ")
    for det in detectors:
        manta_val = yield from bps.rd(det.fileio.num_captured)
        print(f"{det.name} = {manta_val} ")


    # Reset the velocity back to high.
    yield from bps.mv(rot_motor.velocity, 180 / 2)