import uuid
class Operation:
    def __init__(self):
        self._name = None
        self.name = name or uuid.uuid4().hex

    def evaluate(self, a, b):
        pass


class DEG:
    def __init__(self):
        self.dependencies = {}
        self.dependents = {}

    def addNode(self, node):
        self.dependencies[node] = {}
        self.dependents[node] = {}

    def addEdge(self, sourceNode, outlet, targetNode, inlet):
        assert sourceNode in self.dependencies
        assert targetNode in self.dependencies

        self.dependencies[targetNode][inlet] = (sourceNode, outlet)
        self.dependents[sourceNode][outlet] = (targetNode, inlet)




# operators
class Constant:
    def __init__(self, value):
        self._value = value

    def value(self):
        return self._value

if __name__ == "__main__":
    deg = DEG()
    deg.addNode("x")
    deg.addNode("y")
    deg.addNode("add")

    deg.addEdge('x', 'value', 'add', "a")
    deg.addEdge('y', 'value', 'add', "b")

    result = deg.evaluate('add')
    print(result)
