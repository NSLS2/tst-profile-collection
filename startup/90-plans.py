import datetime


def rotation_plan(t_period=0.00002, theta0=30, n_proj=181, n_series=3):
    now = datetime.datetime.now()
    fl_path = PROPOSAL_DIR
    fl_name = "panda_rbdata_" + now.strftime("%Y%m%d_%H%M%S") + ".h5"

    pnd.clock1.period_units.set("s").wait()
    pnd.clock1.period.set(t_period).wait()

    steps_per_turn = 18000
    pnd.counter1.start.set(0).wait()
    pnd.counter1.min.set(0).wait()
    pnd.counter1.step.set(1).wait()
    pnd.counter1.max.set(steps_per_turn)

    steps_per_deg = steps_per_turn / 360
    theta0_steps = theta0 * steps_per_deg - 1000

    if theta0_steps < 0:
        theta0_steps += steps_per_turn
    elif theta0_steps >= steps_per_turn:
        theta0_steps -= steps_per_turn

    pnd.pcomp1.pre_start.set(0)
    pnd.pcomp1.start.set(theta0_steps)
    pnd.pcomp1.width.set(1)
    pnd.pcomp1.step.set(1000000)
    pnd.pcomp1.pulses.set(1)

    theta_proj_step = 180 / (n_proj - 1)
    proj_step_ = theta_proj_step * steps_per_deg
    proj_step = int(round(proj_step_))
    if abs(proj_step - proj_step_) > 1e-3:
        print(f"proj_step_ = {proj_step_}")
        raise ValueError("The step between projections is not integer")

    print(f"proj_step={proj_step} n_proj={n_proj}")

    pnd.pcomp2.pre_start.set(0)
    pnd.pcomp2.start.set(1000)
    pnd.pcomp2.width.set(1)
    pnd.pcomp2.step.set(proj_step)
    pnd.pcomp2.pulses.set(n_proj)

    def inner():
        print(f"Starting acquisition ...")

        pnd.bits.A.set(1).wait()

        pnd.data.hdf_directory.set(fl_path).wait()
        pnd.data.hdf_file_name.set(fl_name).wait()
        pnd.data.flush_period.set(0.5).wait()

        if not n_series:
            pnd.bits.B.set(1).wait()
            pnd.data.capture_mode.set("FOREVER").wait()
        else:
            pnd.bits.B.set(0).wait()
            pnd.counter3.start.set(0).wait()
            pnd.counter3.min.set(0).wait()
            pnd.counter3.step.set(1).wait()
            pnd.counter3.max.set(n_series)

            pnd.data.capture_mode.set("FIRST_N").wait()
            pnd.data.num_capture.set(n_proj * n_series).wait()

        # pnd.data.capture_mode.set("LAST_N").wait()
        # pnd.data.num_capture.set(n_total).wait()
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
        # yield from bps.sleep(3)
        pnd.data.capture.set(0).wait()

        print(f"Acquisition complete.")

        # print(f"HDF5 status: {pnd.hdf5.status.read()}")
        # print(f"HDF5 file path: {pnd.hdf5.file_path.read()}")

    yield from inner()
    bps.sleep(0.1)
