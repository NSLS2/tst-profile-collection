print(f"Loading file {__file__!r} ...")

import asyncio
import datetime
import itertools
import time as ttime
from collections import deque
from enum import Enum
from pathlib import Path
from pprint import pprint
from typing import AsyncGenerator, AsyncIterator, Dict, List, Optional

from event_model import compose_resource
from ophyd.status import SubscriptionStatus


def panda_fly(panda, flyer=default_flyer, num=724):
    yield from bps.stage_all(panda, flyer)
    yield from bps.prepare(flyer, num, wait=True)
    yield from bps.prepare(panda, flyer.trigger_logic.trigger_info(num), wait=True)

    yield from bps.open_run()

    yield from bps.kickoff_all([panda, flyer])

    yield from bps.complete_all([panda, flyer], wait=True, group="complete")

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
            panda,
            # stream=False,
            # return_payload=False,
            name="main_stream",
        )
        yield from bps.sleep(0.01)
    yield from bps.wait(group="complete")
    val = yield from bps.rd(panda.data.num_captured)
    print(f"{val = }")
    yield from bps.close_run()

    yield from bps.unstage_all(panda, flyer)
