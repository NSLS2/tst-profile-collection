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
