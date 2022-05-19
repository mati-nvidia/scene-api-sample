from omni.ui import color as cl
from omni.ui import scene as sc


class SelectionMarker(sc.Manipulator):
    """A manipulator that adds a circle with crosshairs above the selected prim."""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._radius = 5
        self._thickness = 2
        self._half_line_length = 10

    def on_build(self):
        if not self.model:
            return

        if not self.model.has_selection():
            return

        with sc.Transform(transform=sc.Matrix44.get_translation_matrix(*self.model.position.value)):
            with sc.Transform(look_at=sc.Transform.LookAt.CAMERA):
                sc.Arc(self._radius, axis=2, color=cl.yellow)
                sc.Line([0, -self._half_line_length, 0], [0, self._half_line_length, 0],
                        color=cl.yellow, thickness=self._thickness)
                sc.Line([-self._half_line_length, 0, 0], [self._half_line_length, 0, 0],
                        color=cl.yellow, thickness=self._thickness)

    def on_model_updated(self, item):
        self.invalidate()
