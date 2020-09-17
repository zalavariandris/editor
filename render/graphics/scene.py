from . import Mesh


class Scene:
    def __init__(self, children=[]):
        self._children = children

    def add_child(self, child: Mesh) -> None:
        assert isinstance(child, Mesh)
        self._children.append(child)

    @property
    def children(self) -> [Mesh]:
        return self._children

    def _setup(self):
        for child in self._children:
            child.geometry._setup()

