def tomo_demo_01(theta0=10, n_proj=161, n_series=3):

    current_pos = yield from bps.rd(rot_motor)
    print(f"{current_pos = }")
    yield from bps.abs_set(
        rot_motor.user_setpoint, current_pos + (n_series + 10) * 360, wait=True
    )  # or user_setpoint
    yield from bps.abs_set(rot_motor.spmg, "Stop", wait=True)
    yield from bps.abs_set(rot_motor.spmg, "Go", wait=True)

    yield from bps.sleep(2)

    panda_flyer.n_series = n_series
    panda_flyer.n_proj = n_proj
    panda_flyer.theta0 = theta0

    yield from bp.fly([panda_flyer])

    yield from bps.abs_set(rot_motor.spmg, "Stop", wait=True)


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
