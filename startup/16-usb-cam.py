from pathlib import PurePath

from nslsii.ad33 import SingleTriggerV33
from ophyd import Component as C
from ophyd.areadetector import AreaDetector, ImagePlugin
from ophyd.areadetector.filestore_mixins import (
    FileStoreIterativeWrite,
    FileStorePluginBase,
)
from ophyd.areadetector.plugins import JPEGPlugin_V33


class TSTFileStoreJPEG(FileStorePluginBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.filestore_spec = "AD_JPEG"  # spec name stored in resource doc
        self.stage_sigs.update(
            [
                ("file_template", "%s%s_%6.6d.jpeg"),
                ("file_write_mode", "Single"),
            ]
        )
        # 'Single' file_write_mode means one image : one file.
        # It does NOT mean that 'num_images' is ignored.

    def get_frames_per_point(self):
        return self.parent.cam.num_images.get()

    def stage(self):
        super().stage()
        # this over-rides the behavior is the base stage
        self._fn = self._fp + "/" + self.file_name.get()

        resource_kwargs = {
            "template": "_{:06d}.jpeg",
            "filename": self.file_name.get(),
            "frame_per_point": self.get_frames_per_point(),
        }
        self._generate_resource(resource_kwargs)


class TSTJPEGPlugin(JPEGPlugin_V33, TSTFileStoreJPEG, FileStoreIterativeWrite):
    pass


class TSTUVC(AreaDetector):
    image = C(ImagePlugin, "image1:")
    jpeg = C(
        TSTJPEGPlugin,
        "JPEG1:",
        write_path_template="/nsls2/data/tst/legacy/mock-proposals/2024-1/pass-000000/uvc-cam1/%Y/%m/%d/",
        read_path_template="/nsls2/data/tst/legacy/mock-proposals/2024-1/pass-000000/uvc-cam1/%Y/%m/%d/",
        read_attrs=[],
        root="/nsls2/data/tst/legacy/mock-proposals/2024-1/pass-000000/uvc-cam1/",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.stage_sigs.update([(self.cam.trigger_mode, "Internal")])

    def make_data_key(self):
        source = "PV:{}".format(self.prefix)
        # This shape is expected to match arr.shape for the array.
        shape = (
            self.cam.array_size.array_size_y.get(),
            self.cam.array_size.array_size_x.get(),
            3,  # Always save in color
        )
        return dict(
            shape=shape,
            source=source,
            dtype="array",
            dtype_str="|u1",
            external="FILESTORE:",
        )


class TSTUVCSingleTrigger(SingleTriggerV33, TSTUVC):
    pass


def display_last_image_usb_cam():
    from PIL import Image

    Image.fromarray(
        tiled_client.values().last().primary["external"]["usb1_image"].read()[0]
    ).show()


usb1_pv_prefix = "XF:31ID1-ES{UVC-Cam:1}"

usb1 = TSTUVCSingleTrigger(usb1_pv_prefix, name="usb1", read_attrs=["jpeg"])
