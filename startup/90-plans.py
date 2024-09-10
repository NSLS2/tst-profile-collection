print(f"Loading file {__file__!r} ...")

import datetime


def tomo_demo_01(theta0=10, n_proj=161, n_series=3):

    current_pos = yield from bps.rd(rot_motor)
    target_pos = current_pos - (n_series + 10) * 360
    print(f"{current_pos = } {target_pos =}")

    rot_motor.set(target_pos)
    # yield from bps.abs_set(rot_motor, target_pos, wait=True)  # or user_setpoint
    # yield from bps.abs_set(rot_motor.user_setpoint, target_pos, wait=True)  # or user_setpoint
    # yield from bps.abs_set(rot_motor.spmg, "Stop", wait=True)
    # yield from bps.abs_set(rot_motor.spmg, "Go", wait=True)
    yield from bps.abs_set(rot_motor.spmg, "Move", wait=True)

    yield from bps.sleep(2)

    panda_flyer.n_series = n_series
    panda_flyer.n_proj = n_proj
    panda_flyer.theta0 = theta0

    yield from bp.fly([panda_flyer])

    yield from bps.abs_set(rot_motor.spmg, "Stop", wait=True)
    # current_pos = yield from bps.rd(rot_motor)
    # rot_motor.set(current_pos)
    # yield from bps.abs_set(rot_motor.spmg, "Move", wait=True)


def plot_data(scan_id=-1):
    hdr = db[scan_id]
    data = hdr.table(fill=True)

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(16, 9))
    fig.suptitle(f"scan_id={hdr.start['scan_id']}  uid={hdr.start['uid'][:8]}")

    ax1.plot(data["pcap_ts_trig"][1], data["fmc_in_val3"][1], "b.")
    ax1.set_xlabel("Relative time [s]")
    ax1.set_ylabel("Signal [arb.u.]")

    ax2.plot(data["inenc1_val"][1], data["fmc_in_val3"][1], "b.")
    ax2.set_xlabel("Relative time [s]")
    ax2.set_ylabel("Signal [arb.u.]")

    ax1.grid(True)
    ax2.grid(True)

    plt.show()


def rbuf_plan(t_period=0.00002, n_total=25000, n_after=10000):
    """
    rbuf_plan(t_period=0.00002, n_total=25000, n_after=10000)

    Use with acq_for_ring_buffer4.
    """

    now = datetime.datetime.now()
    fl_path = "/nsls2/data/tst/legacy/mock-proposals/2024-1/pass-000000"
    # fl_path = "/nsls2/users/dgavrilov/panda-test/ring-buffer/ioc-plan/data"
    fl_name = "panda_rbdata_" + now.strftime("%Y%m%d_%H%M%S") + ".h5"

    pnd.clock1.period_units.set("s").wait()
    pnd.clock1.period.set(t_period).wait()

    # Counter1 is used for error detection
    pnd.counter1.min.set(0).wait()
    pnd.counter1.max.set(1003).wait()

    def inner():
        print(f"Starting acquisition ...")

        pnd.bits.A.set(0).wait()

        pnd.counter2.min.set(0).wait()
        pnd.counter2.max.set(n_after).wait()

        pnd.data.hdf_directory.set(fl_path).wait()
        pnd.data.hdf_file_name.set(fl_name).wait()
        pnd.data.flush_period.set(0.5).wait()
        pnd.data.capture_mode.set("LAST_N").wait()
        pnd.data.num_capture.set(n_total).wait()
        pnd.data.capture.set(1).wait()
        pnd.pcap.arm.set(1).wait()

        yield from bps.sleep(1)
        try:
            while True:
                if not pnd.pcap.active.get():
                    break
                yield from bps.sleep(0.05)
        finally:
            pnd.pcap.arm.set(0).wait()

        pnd.pcap.arm.set(0).wait()
        pnd.data.capture.set(0).wait()

        print(f"Acquisition complete.")

    yield from inner()
    bps.sleep(0.1)


# Number of encoder counts for an entire revolution
COUNTS_PER_REVOLUTION = 8000
DEG_PER_REVOLUTION = 360
COUNTS_PER_DEG = COUNTS_PER_REVOLUTION / DEG_PER_REVOLUTION


def tomo_demo_async(
    panda=panda1,
    detector=manta1,
    num_images=21,
    scan_time=9,
    start_deg=0,
    exposure_time=None,
):

    panda_pcomp1 = panda.pcomp[1]

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

    panda_devices = [panda, panda_flyer]
    detector_devices = [detector, manta_flyer]
    all_devices = panda_devices + detector_devices

    det_exp_setup = StandardTriggerSetup(
        num_frames=num_images,
        exposure_time=exposure_time,
        trigger_mode=DetectorTrigger.edge_trigger,
    )

    panda_exp_setup = StandardTriggerSetup(
        num_frames=num_images,
        exposure_time=exposure_time,
        trigger_mode=DetectorTrigger.constant_gate,
    )

    yield from bps.mv(
        rot_motor.velocity, 180 / 2
    )  # Make it fast to move to the start position
    yield from bps.mv(rot_motor, start_deg - 20)
    yield from bps.mv(
        rot_motor.velocity, 180 / scan_time
    )  # Set the velocity for the scan
    start_encoder = start_deg * COUNTS_PER_DEG

    width_in_counts = (180 / scan_time) * COUNTS_PER_DEG * exposure_time
    if width_in_counts > step_width_counts:
        raise RuntimeError(
            f"Your specified exposure time of {exposure_time}s is too long! Calculated width: {width_in_counts}, Step size: {step_width_counts}"
        )
    print(f"Exposing camera for {width_in_counts} counts")

    # Set up the pcomp block
    yield from bps.mv(panda_pcomp1.start, int(start_encoder))

    # Uncomment if using gate trigger mode on camera
    # yield from bps.mv(
    #    panda3_pcomp_1.width, width_in_counts
    # )  # Width in encoder counts that the pulse will be high
    yield from bps.mv(panda_pcomp1.step, step_width_counts)
    yield from bps.mv(panda_pcomp1.pulses, num_images)

    yield from bps.open_run()

    detector._writer._path_provider._filename_provider.set_frame_type(
        TomoFrameType.proj
    )

    # The setup below is happening in the VimbaController's arm method.
    # # Setup camera in trigger mode
    # yield from bps.mv(manta_async.trigger_mode, "On")
    # yield from bps.mv(manta_async.trigger_source, "Line1")
    # yield from bps.mv(manta_async.overlap, "Off")
    # yield from bps.mv(manta_async.expose_out_mode, "TriggerWidth")  # "Timed" or "TriggerWidth"

    # Stage All!
    yield from bps.stage_all(*all_devices)
    yield from bps.mv(detector._writer.hdf.num_capture, num_images)

    yield from bps.prepare(manta_flyer, det_exp_setup, wait=True)
    yield from bps.prepare(
        detector, manta_flyer.trigger_logic.trigger_info(det_exp_setup), wait=True
    )

    yield from bps.prepare(panda_flyer, num_images, wait=True)
    yield from bps.prepare(
        panda, panda_flyer.trigger_logic.trigger_info(panda_exp_setup), wait=True
    )

    yield from bps.mv(rot_motor, start_deg + DEG_PER_REVOLUTION / 2 + 5)

    for device in all_devices:
        yield from bps.kickoff(device)

    for flyer_or_panda in panda_devices:
        yield from bps.complete(flyer_or_panda, wait=True, group="complete_panda")

    for flyer_or_det in detector_devices:
        yield from bps.complete(flyer_or_det, wait=True, group="complete_detector")

    # Manually incremenet the index as if a frame was taken
    # detector.writer.index += 1

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

    yield from bps.unstage_all(*panda_devices)

    # Wait for completion of the AD HDF5 file saving.
    done = False
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

    yield from bps.close_run()

    panda_val = yield from bps.rd(panda.data.num_captured)
    manta_val = yield from bps.rd(detector._writer.hdf.num_captured)
    print(f"{panda_val = }    {manta_val = }")

    yield from bps.unstage_all(*detector_devices)

    # Reset the velocity back to high.
    yield from bps.mv(rot_motor.velocity, 180 / 2)


file_loading_timer.stop_timer(__file__)
