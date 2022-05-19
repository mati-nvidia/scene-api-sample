from typing import List

import carb
import omni.kit.viewport_legacy as vp
from omni.ui import scene as sc
import omni.usd
from pxr import Gf, Sdf, Tf, Usd, UsdGeom


class SelectionModel(sc.AbstractManipulatorModel):
    """A data model storing the current selected object.

    Tracks selection changes using omni.usd.StageEventType.SELECTION_CHANGED and position changes for the selected
    prim using Tf.Notice.
    """
    class PositionItem(sc.AbstractManipulatorItem):
        def __init__(self):
            super().__init__()
            self.value = [0, 0, 0]

    def __init__(self):
        super().__init__()

        self.position = SelectionModel.PositionItem()
        self._offset = 5
        self._current_path = ""
        usd_context = omni.usd.get_context()
        self._stage: Usd.Stage = usd_context.get_stage()

        if self._stage:
            self._stage_listener = Tf.Notice.Register(Usd.Notice.ObjectsChanged, self._notice_changed, self._stage)

        self._selection = usd_context.get_selection()
        self._events = usd_context.get_stage_event_stream()
        self._stage_event_sub = self._events.create_subscription_to_pop(self._on_stage_event, name="Selection Update")

    def _notice_changed(self, notice, stage):
        """Update model with the selected prim's latest position."""
        for p in notice.GetChangedInfoOnlyPaths():
            if self._current_path in str(p.GetPrimPath()):
                self.position.value = self._get_position()
                self._item_changed(self.position)

    def _on_stage_event(self, event):
        """Update model with the latest selected prim and its position.

        Only tracks the first selected prim. Not multi-selct.
        """
        if event.type == int(omni.usd.StageEventType.SELECTION_CHANGED):
            self._current_path = ""
            if not self._stage:
                return

            prim_paths = self._selection.get_selected_prim_paths()
            if not prim_paths:
                self.position.value = [0, 0, 0]
                self._item_changed(self.position)
                return

            prim = self._stage.GetPrimAtPath(prim_paths[0])
            if not prim.IsA(UsdGeom.Imageable):
                self._prim = None
                return

            self._prim = prim
            self._current_path = prim_paths[0]

            self.position.value = self._get_position()
            self._item_changed(self.position)

    def _get_position(self):
        if not self._current_path:
            return [0, 0, 0]

        prim = self._stage.GetPrimAtPath(self._current_path)
        box_cache = UsdGeom.BBoxCache(Usd.TimeCode.Default(), includedPurposes=[UsdGeom.Tokens.default_])
        bound = box_cache.ComputeWorldBound(prim)
        range_ = bound.ComputeAlignedBox()
        bboxMin = range_.GetMin()
        bboxMax = range_.GetMax()
        position = [(bboxMin[0] + bboxMax[0]) * 0.5, bboxMax[1] + self._offset, (bboxMin[2] + bboxMax[2]) * 0.5]
        return position

    def has_selection(self):
        return self._current_path != ""


class CameraModel(sc.AbstractManipulatorModel):
    def __init__(self):
        super().__init__()

        self._camera_prim = None
        self._camera_path = None
        self._stage_listener = None

        def on_usd_context_event(event: carb.events.IEvent):
            """Register/Re-register Tf.Notice callbacks on UsdContext changes."""
            event_type = event.type
            if event_type == int(omni.usd.StageEventType.OPENED) or event_type == int(omni.usd.StageEventType.CLOSING):
                if self._stage_listener:
                    self._stage_listener.Revoke()
                    self._stage_listener = None
                self._camera_prim = None
                self._camera_path = None
            if event_type == int(omni.usd.StageEventType.OPENED):
                stage = omni.usd.get_context().get_stage()
                self._stage_listener = Tf.Notice.Register(Usd.Notice.ObjectChanged, self._notice_changed, stage)
                self._get_camera()

        usd_ctx = omni.usd.get_context()
        self._stage_event_sub = usd_ctx.get_stage_event_stream().create_subscription_to_pop(on_usd_context_event, name="CameraModel stage event")
        stage = usd_ctx.get_stage()
        if stage:
            self._stage_listener = Tf.Notice.Register(Usd.Notice.ObjectsChanged, self._notice_changed, stage)

    def destroy(self):
        self._stage_event_sub = None
        if self._stage_listener:
            self._stage_listener.Revoke()
            self._stage_listener = None
        self._camera_prim = None
        self._camera_path = None
        super().destroy()

    def get_as_floats(self, item):
        if item == self.get_item("projection"):
            return self._get_projection()
        if item == self.get_item("view"):
            return self._get_view()

    def _notice_changed(self, notice, stage):
        for p in notice.GetChangedInfoOnlyPaths():
            if p.GetPrimPath() == self._camera_path:
                self._item_changed(None)

    @staticmethod
    def _flatten(transform):
        """Need to convert Gf.Matrix4d into a list for Scene API. This is the fastest way."""
        return [
            transform[0][0], transform[0][1], transform[0][2], transform[0][3],
            transform[1][0], transform[1][1], transform[1][2], transform[1][3],
            transform[2][0], transform[2][1], transform[2][2], transform[2][3],
            transform[3][0], transform[3][1], transform[3][2], transform[3][3],
        ]

    def _get_camera(self):
        if not self._camera_prim:
            viewport_window = vp.get_default_viewport_window()
            stage = omni.usd.get_context(viewport_window.get_usd_context_name()).get_stage()
            if stage:
                self._camera_path = Sdf.Path(viewport_window.get_active_camera())
                self._camera_prim = stage.GetPrimAtPath(self._camera_path)

        if self._camera_prim:
            return UsdGeom.Camera(self._camera_prim).GetCamera().frustum

    def _get_view(self) -> List[float]:
        frustum = self._get_camera()
        if frustum:
            view = frustum.ComputeViewMatrix()
        else:
            view = Gf.Matrix4d(1.0)
        return self._flatten(view)

    def _get_projection(self) -> List[float]:
        frustum = self._get_camera()
        if frustum:
            projection = frustum.ComputeProjectionMatrix()
        else:
            projection = Gf.Matrix4d(1.0)

        return self._flatten(projection)
