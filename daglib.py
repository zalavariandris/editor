"""
dag represented by an adjacency list
store all inputs for each node in a dict

these are helper functions
"""

def transpose(dag):
    raise NotImplementedError

def normalize(dag):
    """ gather all nodes in the graph and make sure each node are also keys in dictionary """
    nodes = set( dag.keys() )
    for key, inputs in list(dag.items()):
        for n in inputs:
            if n not in dag:
                dag[n] = []
    return dag

def nodes(dag):
    for n in dag.keys():
        yield n

def edges(dag):
    for src, adj in dag.items():
        for dst in adj:
            yield (src, dst)

def startNodes(dag):
    return set( nodes(dag) ) - {n for adj in dag.values() for n in adj}

def layout(dag):
    normalize(dag)
    rootNodes = startNodes(dag)

    if not len(rootNodes):
        raise Exception("not acyclic graph")

    # create stack
    stack = [rootNodes]
    visited = set()
    while stack[-1]:
        layer = []
        for node in stack[-1]:
            for child in dag[node]:
                if child not in visited:
                    visited.add(child)
                    layer.append(child)

        stack.append(layer)
    stack = stack[:-1]

    # position layers
    for y, layer in enumerate(stack):
        for x, node in enumerate(layer):
            xpos = x-(len(layer)-1)/2
            ypos = y
            yield (node, (xpos, ypos))

def longestPath(dag):
    pass

def niceLookingLayout(dag):
    pass


def plot(dag, size=(0.3,0.3), spacing=0.0):
    """ plot graph """
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle

    positions = dict( layouts(dag) )
    x = [x for x, y in positions.values()]
    y = [y for x, y in positions.values()]

    fi, ax = plt.subplots()
    ax.set_aspect(1.0)

    # draw nodes
    ax.scatter(x, y, s=100)
    for n in dag.keys():
        x, y = positions[n]
        ax.add_patch( Rectangle((x-size[0]/2-spacing/2, y-size[1]/2), 
                        size[0], size[1], 
                        fc ='grey',  
                        ec ='none', 
                        lw = 10) ) 

    for e in edges(dag):
        x1, y1 = positions[e[1]]
        x2, y2 = positions[e[0]]

        ax.arrow(x1, y1, x2-x1, y2-y1, width=0.03, length_includes_head=True, fc='k', ec='none')

    # draw labels
    for n in nodes(dag):
        x, y = positions[n]
        ax.annotate(str(n), (x, y))

    return ax

if __name__ == "__main__":
    dag = {
        "a": [],
        "b": ['a'],
        "c": [],
        'd': ['b', 'c'],
        'e': ['d'],
        'f': ['d'],
        'g': ['d'],
        'h': ['e', 'f'],
        'i': ['e', 'h'],
        'j': ['f', 'g']
    }
    import matplotlib.pyplot as plt
    ax = plot(dag)
    plt.show()