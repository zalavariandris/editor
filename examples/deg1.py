import uuid

class DEG:
    currentGraph = None
    def __enter__(self):
        DEG.currentGraph = self

    def __exit__(self, *args):
        DEG.currentGraph = None

    def addSource(self, name, data):
        pass

    def setSource(self, name, data):
        pass

    def addOperator(self, name, f):
        pass

    def evaluate(self, op):
        ???

class Operator:
    def __init__(self, *args, name=None, **kwargs):
        self.inputs = {}
        for i, op in enumerate(args):
            assert isinstance(op, Operator)
            self.inputs[i] = op
        for key, op in kwargs.items():
            assert isinstance(op, Operator)
            self.inputs[key] = op

        self.name = name or uuid.uuid4().hex

    def __call__(self, *args, **kwargs):
        """
        Inheriting operations should implement this function to evaluate the operation.
        """
        raise NotImplementedError

class Constant(Operator):
    def __init__(self, value, name=None):
        super().__init__(name=name)
        self._value = value

    def __call__(self):
        return self._value

    def __repr__(self):
        return str(self._value)


class Add(Operator):
    def __call__(self, a, b):
        return a+b

    def __repr__(self):
        return "+"


class Multiply(Operator):
    def __call__(self, a, b):
        return a*b

    def __repr__(self):
        return "*"

if __name__ == "__main__":
    x = 5
    y = 6
    z = x+y
    w = (z+z)*2

    print(w)

    graph = DEG()
    with graph:
        x = Constant(5)
        y = Constant(6)
        z = Add(x,y)
        w = Multiply(Add(z,z), Constant(2))

    print( graph.evaluate(w) )