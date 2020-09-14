from OpenGL.GL import *
import logging
import glm
import numpy as np
from .helpers import buffer_offset
import functools
import math

def calculatePositionOnCurve(u, p, q, radius):
    cu = math.cos(u)
    su = math.sin(u)
    quOverP = q / p * u
    cs = math.cos(quOverP)

    position = glm.vec3(0)
    position.x = radius * (2 + cs) * 0.5 * cu
    position.y = radius * (2 + cs) * su * 0.5
    position.z = radius * math.sin(quOverP) * 0.5

    return position


@functools.lru_cache(maxsize=128)
def torusknot_geo(radius, tube, tubularSegments, radialSegments, p, q):
    logging.debug("create torusknot geo")

    indices = []
    vertices = []
    normals = []
    uvs = []

    for i in range(tubularSegments):

        # the radian "u" is used to calculate the position on the torus curve of the current tubular segement

        u = i / tubularSegments * p * math.pi * 2;

        # now we calculate two points. P1 is our current position on the curve, P2 is a little farther ahead.
        # these points are used to create a special "coordinate space",
        # which is necessary to calculate the correct vertex positions

        P1 = calculatePositionOnCurve(u, p, q, radius)
        P2 = calculatePositionOnCurve(u + 0.01, p, q, radius)

        # calculate orthonormal basis

        T = P2 - P1
        N = P2 + P1
        B = glm.cross(T, N)
        N = glm.cross(B, T)

        # normalize B, N. T can be ignored, we don't use it
        B = glm.normalize(B)
        N = glm.normalize(N)

        for j in range(radialSegments):

            # now calculate the vertices. they are nothing more than an extrusion of the torus curve.
            # because we extrude a shape in the xy-plane, there is no need to calculate a z-value.

            v = j / radialSegments * math.pi * 2
            cx = - tube * math.cos( v )
            cy = tube * math.sin( v )

            # now calculate the final vertex position.
            # first we orient the extrusion with our basis vectos, then we add it to the current position on the curve

            vertex = glm.vec3()
            vertex.x = P1.x + ( cx * N.x + cy * B.x )
            vertex.y = P1.y + ( cx * N.y + cy * B.y )
            vertex.z = P1.z + ( cx * N.z + cy * B.z )

            vertices.append( vertex )

            # normal (P1 is always the center/origin of the extrusion, thus we can use it to calculate the normal)

            normal = glm.normalize(vertex - P1)

            normals.append(normal)

            # uv

            uvs.append(i / tubularSegments)
            uvs.append(j / radialSegments)


    # generate indices
    for j in range(1, tubularSegments):
        for i in range(1, radialSegments):

            # indices
            a = (radialSegments + 1) * (j - 1) + (i - 1)
            b = (radialSegments + 1) * j + (i - 1)
            c = (radialSegments + 1) * j + i
            d = (radialSegments + 1) * (j - 1) + i

            # faces
            indices.append((a, b, d))
            indices.append((b, c, d))

    positions = np.array([(p.x, p.y, p.z) for p in vertices]).astype(np.float32)
    normals = np.array([(p.x, p.y, p.z) for p in normals]).astype(np.float32)
    uvs = np.array(uvs).astype(np.float32).reshape(-1, 2)
    indices = np.array(indices).astype(np.uint).reshape(-1, 3)

    return positions, normals, uvs, indices


@functools.lru_cache(maxsize=128)
def create_buffer(locations):

    positions, normals, uvs, indices = torusknot_geo(1.0, 0.2, 256, 32, 2, 3)

    logging.debug("create torusknot buffer")
    count = indices.size

    # setup VAO
    vao = glGenVertexArrays(1)
    
    pos_vbo, uv_vbo, normal_vbo = glGenBuffers(3) # FIXME: use single vbo for positions and vertices
    glBindVertexArray(vao)
    glBindBuffer(GL_ARRAY_BUFFER, pos_vbo)
    glBufferData(GL_ARRAY_BUFFER, positions.nbytes, positions, GL_STATIC_DRAW)

    position_location, uv_location, normal_location = locations

    # position_location = glGetAttribLocation(program, 'position')
    glVertexAttribPointer(position_location, 3, GL_FLOAT, False, 0, buffer_offset(0))
    glEnableVertexAttribArray(position_location)

    # uv_location = glGetAttribLocation(program, 'uv')
    if uv_location is not -1:
        glBindBuffer(GL_ARRAY_BUFFER, uv_vbo)
        glBufferData(GL_ARRAY_BUFFER, uvs.nbytes, uvs, GL_STATIC_DRAW)
        glVertexAttribPointer(uv_location, 2, GL_FLOAT, False, 0, buffer_offset(0))
        glEnableVertexAttribArray(uv_location)

    # normal_location = glGetAttribLocation(program, 'normal')
    if normal_location is not -1:
        glBindBuffer(GL_ARRAY_BUFFER, normal_vbo)
        glBufferData(GL_ARRAY_BUFFER, normals.nbytes, normals, GL_STATIC_DRAW)
        glVertexAttribPointer(normal_location, 3, GL_FLOAT, False, 0, buffer_offset(0))
        glEnableVertexAttribArray(normal_location)

    glBindBuffer(GL_ARRAY_BUFFER, 0)

    glBindVertexArray(0)

    # create ebo
    ebo = glGenBuffers(1)
    glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, ebo)
    glBufferData(GL_ELEMENT_ARRAY_BUFFER, indices.nbytes, indices, GL_STATIC_DRAW)
    glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, 0)

    return vao, ebo, count


def torusknot(prog):
    locations = tuple(glGetAttribLocation(prog, name) for name in ("position", 'uv', 'normal'))
    vao, ebo, count = create_buffer(locations)

    # draw
    glBindVertexArray(vao)
    glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, ebo)
    glDrawElements(GL_TRIANGLES, count, GL_UNSIGNED_INT, None)
    glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, 0)
    glBindVertexArray(0)
