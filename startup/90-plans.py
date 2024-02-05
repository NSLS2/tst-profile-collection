def tomo_demo_01():

    current_pos = yield from bps.rd(rot_motor)
    print(f"{current_pos = }")
    yield from bps.abs_set(
        rot_motor.user_setpoint, current_pos + 3600, wait=True
    )  # or user_setpoint
    yield from bps.abs_set(rot_motor.spmg, "Stop", wait=True)
    yield from bps.abs_set(rot_motor.spmg, "Go", wait=True)

    yield from bps.sleep(1)
    yield from bp.fly([panda_flyer])

    yield from bps.abs_set(rot_motor.spmg, "Stop", wait=True)
