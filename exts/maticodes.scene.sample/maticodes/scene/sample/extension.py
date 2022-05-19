import omni.ext
import omni.kit.commands
import omni.ui as ui
from omni.ui import scene as sc
import omni.usd

from .models import CameraModel, SelectionModel
from .manipulators import SelectionMarker


# Any class derived from `omni.ext.IExt` in top level module (defined in `python.modules` of `extension.toml`) will be
# instantiated when extension gets enabled and `on_startup(ext_id)` will be called. Later when extension gets disabled
# on_shutdown() is called.
class SceneAPISampleExtension(omni.ext.IExt):
    # ext_id is current extension id. It can be used with extension manager to query additional information, like where
    # this extension is located on filesystem.
    def on_startup(self, ext_id):
        print("[maticodes.scene.sample] SceneAPISampleExtension startup")

        self._window = SampleWindow()

    def on_shutdown(self):
        print("[maticodes.scene.sample] SceneAPISampleExtension shutdown")
        self._window.destroy()
        self._window = None


class SampleWindow(ui.Window):
    def __init__(self, title: str = None, **kwargs):
        if title is None:
            title = "Viewport"
        if "width" not in kwargs:
            kwargs["width"] = 1200
        if "height" not in kwargs:
            kwargs["height"] = 480

        kwargs["flags"] = ui.WINDOW_FLAGS_NO_SCROLL_WITH_MOUSE | ui.WINDOW_FLAGS_NO_SCROLLBAR

        super().__init__(title, **kwargs)
        self.frame.set_build_fn(self.__build_window)

    def __build_window(self):
        scene_view = sc.SceneView(model=CameraModel(), 
                                  aspect_ratio_policy=sc.AspectRatioPolicy.PRESERVE_ASPECT_HORIZONTAL, 
                                  scene_aspect_ratio=1280 / 720)
        with scene_view.scene:
            SelectionMarker(model=SelectionModel())
