import numpy as np
import logging
import functools


@functools.lru_cache(maxsize=128)
def cube(flip=False):
    logging.debug("create cube geo")
    positions = np.array([
        # Front face
        -0.5, -0.5, 0.5,
        0.5, -0.5, 0.5,
        0.5, 0.5, 0.5,
        -0.5, 0.5, 0.5,

        # Back face
        -0.5, -0.5, -0.5,
        -0.5, 0.5, -0.5,
        0.5, 0.5, -0.5,
        0.5, -0.5, -0.5,

        # Top face
        -0.5, 0.5, -0.5,
        -0.5, 0.5, 0.5,
        0.5, 0.5, 0.5,
        0.5, 0.5, -0.5,

        # Bottom face
        -0.5, -0.5, -0.5,
        0.5, -0.5, -0.5,
        0.5, -0.5, 0.5,
        -0.5, -0.5, 0.5,

        # Right face
        0.5, -0.5, -0.5,
        0.5, 0.5, -0.5,
        0.5, 0.5, 0.5,
        0.5, -0.5, 0.5,

        # Left face
        -0.5, -0.5, -0.5,
        -0.5, -0.5, 0.5,
        -0.5, 0.5, 0.5,
        -0.5, 0.5, -0.5,
    ], dtype=np.float32).reshape((-1, 3))

    uvs = np.array([
        # Front
        0, 1,
        1, 1,
        1, 0,
        0, 0,

        # Back
        0, 0,
        0, 1,
        1, 1,
        1, 0,

        # Top
        0, 0,
        0, 1,
        1, 1,
        1, 0,

        # Bottom
        0, 1,
        1, 1,
        1, 0,
        0, 0,

        # Right
        1, 1,
        1, 0,
        0, 0,
        0, 1,

        # Left
        0, 1,
        1, 1,
        1, 0,
        0, 0,
    ], dtype=np.float32).reshape(-1, 2)

    normals = np.array([
        0.0, 0.0, 1.0,  # Front face
        0.0, 0.0, -1.0,  # Back face
        0.0, 1.0, 0.0,  # Top face
        0.0, -1.0, 0.0,  # Bottom face
        1.0, 0.0, 0.0,  # Right face
        -1.0, 0.0, 0.0,  # Left face
    ], dtype=np.float32).reshape((-1, 3)).repeat(4, axis=0)

    indices = np.array([
        0, 1, 2, 0, 2, 3,  # front
        4, 5, 6, 4, 6, 7,  # back
        8, 9, 10, 8, 10, 11,  # top
        12, 13, 14, 12, 14, 15,  # bottom
        16, 17, 18, 16, 18, 19,  # right
        20, 21, 22, 20, 22, 23,  # left
    ], dtype=np.uint).reshape((-1, 3))

    if flip:
        indices = np.flip(indices)
        normals *= (-1, -1, -1)

    return positions, normals, uvs, indices