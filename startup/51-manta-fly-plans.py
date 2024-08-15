def inner_manta_collect(manta_detector, flyer):

    yield from bps.kickoff(flyer)
    yield from bps.kickoff(manta_detector)

    yield from bps.complete(flyer, wait=True, group="complete")
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


def manta_collect(
    manta_detector, flyer, num=10, exposure_time=0.1, software_trigger=True
):

    manta_exp_setup = StandardTriggerSetup(
        num_images=num, exposure_time=exposure_time, software_trigger=software_trigger
    )

    yield from bps.open_run()

    yield from bps.stage_all(manta_detector, flyer)

    yield from bps.prepare(flyer, manta_exp_setup, wait=True)
    yield from bps.prepare(manta_detector, flyer.trigger_info, wait=True)

    yield from inner_manta_collect(manta_detector, flyer)

    yield from bps.unstage_all(flyer, manta_detector)

    yield from bps.close_run()


def _manta_collect_dark_flat(manta_detector, num=10, exposure_time=0.1):

    manta_exp_setup = gen_software_trigger_setup(num, exposure_time)

    yield from bps.open_run()

    yield from bps.stage_all(manta_detector)

    yield from bps.prepare(
        manta_detector, default_trigger_logic.trigger_info(manta_exp_setup), wait=True
    )

    yield from inner_manta_collect()

    yield from bps.unstage_all(manta_detector)

    yield from bps.close_run()


def manta_fly(
    num=10,
):  # Note: 724 points are specific for the "rotation_sim_04" panda config!
    yield from bps.stage_all(manta_standard_det, flyer)
    assert flyer._trigger_logic.state == TriggerState.stopping
    yield from bps.prepare(flyer, num, wait=True)
    yield from bps.prepare(manta_standard_det, flyer.trigger_info, wait=True)

    detector = manta_standard_det
    # detector.controller.disarm.assert_called_once  # type: ignore

    yield from bps.open_run()

    yield from bps.kickoff(flyer)
    yield from bps.kickoff(detector)

    yield from bps.complete(flyer, wait=True, group="complete")
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

    yield from bps.unstage_all(flyer, manta_standard_det)
