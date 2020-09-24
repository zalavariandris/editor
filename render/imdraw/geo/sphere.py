import numpy as np
import logging
import functools
import math

@functools.lru_cache(maxsize=128)
def sphere():
    """
    reference: [http://www.songho.ca/opengl/gl_sphere.html]
    """
    logging.debug('create sphere geometry')

    vertices = []
    normals = []
    texCoords = []

    radius = 0.5
    origin = (0, 0, 0)
    sectorCount = 36
    stackCount = 36

    #
    sectorStep = 2 * math.pi / sectorCount
    stackStep = math.pi / stackCount

    lengthInv = 1 / radius

    for i in range(0, stackCount + 1):
        stackAngle = math.pi / 2 - i * stackStep  # starting from pi/2 to -pi/2
        xy = radius * math.cos(stackAngle)  # r * cos(u)
        y = radius * math.sin(stackAngle)  # r * sin(u)

        # add (sectorCount+1) vertices per stack
        # the first and last vertices have same position and normal, but different tex coords
        for j in range(0, sectorCount + 1):
            sectorAngle = j * sectorStep  # starting from 0 to 2pi

            # vertex position (x, y, z)
            x = xy * math.cos(sectorAngle)  # r * cos(u) * cos(v)
            z = xy * math.sin(sectorAngle)  # r * cos(u) * sin(v)
            vertices.append(x)
            vertices.append(y)
            vertices.append(z)

            # normalized vertex normal (nx, ny, nz)
            nx = x * lengthInv
            ny = y * lengthInv
            nz = z * lengthInv
            normals.append(nx)
            normals.append(ny)
            normals.append(nz)

            # vertex tex coord (s, t) range between [0, 1]
            s = j / sectorCount
            t = i / stackCount
            texCoords.append(s)
            texCoords.append(t)

    indices = []
    for i in range(0, stackCount):
        k1 = i * (sectorCount + 1)  # beginning of current stack
        k2 = k1 + sectorCount + 1  # beginning of next stack

        for j in range(0, sectorCount):
            # 2 triangles per sector excluding first and last stacks
            # k1 => k2 => k1+1
            if i != 0:
                indices.append(k1 + 1)
                indices.append(k2)
                indices.append(k1)

            # k1+1 => k2 => k2+1
            if i != (stackCount - 1):
                indices.append(k2 + 1)
                indices.append(k2)
                indices.append(k1 + 1)

            k1 += 1
            k2 += 1

    positions = np.array(vertices, dtype=np.float32).reshape((-1, 3))

    magnitudes = np.sqrt((positions ** 2).sum(-1))[..., np.newaxis]
    normals = positions / magnitudes
    positions -= origin
    uvs = np.array(texCoords, dtype=np.float32).reshape((-1, 2))
    indices = np.array(indices, dtype=np.uint)
    return positions, normals, uvs, indices