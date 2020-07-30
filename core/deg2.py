class DEG:
	def __init__(self):
		self.dependencies = {}
		self.dependents = {}

	def addNode(self, node):
		self.dependencies[node] = {}
		self.dependents[node] = {}

	def addLink(self, source, outlet, target, inlet):
		self.dependencies[target][inlet] = (source, outlet)
		self.dependents[source][outlet] = (target, inlet)

	def bfs(self, start):
		"""Breadth First Search"""
		explored = []
		queue = [start]

		while queue:
			node = queue.pop(0)
			if node not in explored:
				explored.append(node)
				neighbors = [_[0] for _ in graph.dependencies[add].values()]

				for neighbor in neighbors:
					queue.append(neighbor)

		return explored

	def evaluate(self, node):
		# print(self.dependencies)
		nodes = list(reversed(self.bfs(node)))

		results = {}
		for node in nodes:
			kwargs = self.dependencies
			print(kwargs)


class Operator:
	pass

class Identity(Operator):
	def __init__(self, value):
		self._cache = value

	def _evaluate(self):
		return self._cache

	def __repr__(self):
		return str(self._cache)


class Add(Operator):
	def __init__(self, a, b):
		if not isinstance(a, Operator):
			a = Identity(a)
		if not isinstance(b, Operator):
			b = Identity(b)
		self.a = a
		self.b = b

		self._cache = None

	def _evaluate(self):
		if self._cache is None:
			self._cache = self.__call__(self.a._evaluate(), self.b._evaluate())
		return self._cache

	def __call__(self, a, b):
		return a+b

	def __repr__(self):
		return "+"


if __name__ == "__main__":
	graph = DEG()

	x = Identity(5)
	y = Identity(20)

	z = Add(x,y)

	w = Add(Add(z, 2), Add(z, 3))

	res = w.evaluate()
	print(res)

