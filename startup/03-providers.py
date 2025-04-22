file_loading_timer.start_timer(__file__)

import os
from pathlib import Path

from nslsii.ophyd_async.providers import NSLS2PathProvider
from ophyd_async.core import PathInfo


class TSTPathProvider(NSLS2PathProvider):

    def get_beamline_proposals_dir(self):
        """
        Function that computes path to the proposals directory based on TLA env vars
        """

        beamline_tla = os.getenv(
            "ENDSTATION_ACRONYM", os.getenv("BEAMLINE_ACRONYM", "")
        ).lower()
        beamline_proposals_dir = Path(
            f"/nsls2/data/{beamline_tla}/legacy/mock-proposals"
        )

        return beamline_proposals_dir

    def __call__(self, device_name: str = None) -> PathInfo:
        directory_path = self.generate_directory_path(device_name=device_name)

        return PathInfo(
            directory_path=directory_path,
            filename=self._filename_provider(),
            create_dir_depth=-7,
        )


file_loading_timer.stop_timer(__file__)
