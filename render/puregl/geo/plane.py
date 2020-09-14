from OpenGL.GL import *
import numpy as np
import logging
import functools


@functools.lru_cache(maxsize=128)
def plane():
    logging.debug("create plane geo")
    positions = np.array(
        [(-1.0, 0.0, +1.0),
         (+1.0, 0.0, +1.0),
         (-1.0, 0.0, -1.0),
         (+1.0, 0.0, -1.0)],
        dtype=np.float32
    )
    positions *= (3, 1, 3)

    uvs = np.array(
        [(0.0, 1.0),
         (1.0, 1.0),
         (0.0, 0.0),
         (1.0, 0.0)],
        dtype=np.float32
    )

    normals = np.array(
        [(0.0, 1.0, 0.0),
         (0.0, 1.0, 0.0),
         (0.0, 1.0, 0.0),
         (0.0, 1.0, 0.0)],
        dtype=np.float32
    )

    indices = np.array([
        (0, 1, 2), (1, 3, 2)
    ], dtype=np.uint).reshape((-1, 3))

    return positions, normals, uvs, indices
