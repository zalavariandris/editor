from OpenGL.GL import *
import numpy as np

def buffer_offset(itemsize):
    import ctypes
    return ctypes.c_void_p(itemsize)

def quad(program):
    try:
        vao = quad.cache
    except AttributeError:
        positions = np.array(
            # positions        # texture Coords
            [(-1.0, 1.0, 0.0),
            (-1.0,  -1.0, 0.0),
            ( 1.0,  1.0, 0.0),
            ( 1.0,  -1.0, 0.0)],
            dtype=np.float32
        )

        uvs = np.array(
            # positions        # texture Coords
            [(0.0, 1.0),
            (0.0, 0.0),
            (1.0, 1.0),
            (1.0, 0.0)],
            dtype=np.float32
        )

        # setup VAO
        vao = glGenVertexArrays(1)

        pos_vbo, uv_vbo = glGenBuffers(2) # FIXME: use single vbo for positions and vertices
        glBindVertexArray(vao)
        glBindBuffer(GL_ARRAY_BUFFER, pos_vbo)
        glBufferData(GL_ARRAY_BUFFER, positions.nbytes, positions, GL_STATIC_DRAW)
        position_location = glGetAttribLocation(program, 'position')
        # assert position_location>=0
        glVertexAttribPointer(position_location, 3, GL_FLOAT, False, 0, buffer_offset(0))
        glEnableVertexAttribArray(position_location)

        uv_location = glGetAttribLocation(program, 'uv')
        # assert uv_location>=0
        glBindBuffer(GL_ARRAY_BUFFER, uv_vbo)
        glBufferData(GL_ARRAY_BUFFER, uvs.nbytes, uvs, GL_STATIC_DRAW)
        glVertexAttribPointer(uv_location, 2, GL_FLOAT, False, 0, buffer_offset(0))
        glEnableVertexAttribArray(uv_location)

        glBindBuffer(GL_ARRAY_BUFFER, 0)
        glBindVertexArray(0)
        quad.cache = vao
    finally:
        glBindVertexArray(vao)
        glDrawArrays(GL_TRIANGLE_STRIP, 0, 4)
        glBindVertexArray(0)


def plane(program):
    try:
        print("call plane")
        memo = plane.memo
    except AttributeError:
        print("create memo for", __name__)
        memo = dict()
        plane.memo = memo

    try:
        vao = plane.memo[program]
    except AttributeError:
        positions = np.array(
            # positions        # texture Coords
            [(-1.0, 0.0, 1.0),
            (-1.0,  0.0, -1.0),
            ( 1.0,  0.0, 1.0),
            ( 1.0,  0.0, -1.0)],
            dtype=np.float32
        )
        positions*=(3, 1, 3)

        uvs = np.array(
            # positions        # texture Coords
            [(0.0, 1.0),
            (0.0, 0.0),
            (1.0, 1.0),
            (1.0, 0.0)],
            dtype=np.float32
        )

        normals = np.array(
            # positions        # texture Coords
            [(0.0, 1.0, 0.0),
            (0.0, 1.0, 0.0),
            (0.0, 1.0, 0.0),
            (0.0, 1.0, 0.0)],
            dtype=np.float32
        )

        # setup VAO
        vao = glGenVertexArrays(1)

        pos_vbo, uv_vbo, normal_vbo = glGenBuffers(3) # FIXME: use single vbo for positions and vertices
        glBindVertexArray(vao)

        position_location = glGetAttribLocation(program, 'position')
        glBindBuffer(GL_ARRAY_BUFFER, pos_vbo)
        glBufferData(GL_ARRAY_BUFFER, positions.nbytes, positions, GL_STATIC_DRAW)
        glVertexAttribPointer(position_location, 3, GL_FLOAT, False, 0, buffer_offset(0))
        glEnableVertexAttribArray(position_location)

        uv_location = glGetAttribLocation(program, 'uv')
        if uv_location>=0:
            glBindBuffer(GL_ARRAY_BUFFER, uv_vbo)
            glBufferData(GL_ARRAY_BUFFER, uvs.nbytes, uvs, GL_STATIC_DRAW)
            glVertexAttribPointer(uv_location, 2, GL_FLOAT, False, 0, buffer_offset(0))
            glEnableVertexAttribArray(uv_location)

        normal_location = glGetAttribLocation(program, 'normal')
        if normal_location is not -1:
            glBindBuffer(GL_ARRAY_BUFFER, normal_vbo)
            glBufferData(GL_ARRAY_BUFFER, normals.nbytes, normals, GL_STATIC_DRAW)
            glVertexAttribPointer(normal_location, 3, GL_FLOAT, False, 0, buffer_offset(0))
            glEnableVertexAttribArray(normal_location)

        glBindBuffer(GL_ARRAY_BUFFER, 0)
        glBindVertexArray(0)
        plane.vao = vao
    finally:
        glBindVertexArray(vao)
        glDrawArrays(GL_TRIANGLE_STRIP, 0, 4)
        glBindVertexArray(0)

def cube(program):
    try:
        vao = cube.vao
        ebo = cube.ebo
    except AttributeError:
        """ create flat cube
        [https://developer.mozilla.org/en-US/docs/Web/API/WebGL_API/Tutorial/Creating_3D_objects_using_WebGL]
        """
        # Create geometry
        positions = np.array([
            # Front face
            -0.5, -0.5,  0.5,
            0.5, -0.5,  0.5,
            0.5,  0.5,  0.5,
            -0.5,  0.5,  0.5,

            # Back face
            -0.5, -0.5, -0.5,
            -0.5,  0.5, -0.5,
            0.5,  0.5, -0.5,
            0.5, -0.5, -0.5,

            # Top face
            -0.5,  0.5, -0.5,
            -0.5,  0.5,  0.5,
            0.5,  0.5,  0.5,
            0.5,  0.5, -0.5,

            # Bottom face
            -0.5, -0.5, -0.5,
            0.5, -0.5, -0.5,
            0.5, -0.5,  0.5,
            -0.5, -0.5,  0.5,

            # Right face
            0.5, -0.5, -0.5,
            0.5,  0.5, -0.5,
            0.5,  0.5,  0.5,
            0.5, -0.5,  0.5,

            # Left face
            -0.5, -0.5, -0.5,
            -0.5, -0.5,  0.5,
            -0.5,  0.5,  0.5,
            -0.5,  0.5, -0.5,
        ], dtype=np.float32).reshape((-1,3))
        positions+=(0,0.5,0)

        normals = np.array([
             0.0,  0.0,  1.0, # Front face
             0.0,  0.0, -1.0, # Back face
             0.0,  1.0,  0.0, # Top face
             0.0, -1.0,  0.0, # Bottom face
             1.0,  0.0,  0.0, # Right face
            -1.0,  0.0,  0.0, # Left face
        ], dtype=np.float32).reshape((-1,3)).repeat(4, axis=0)

        indices = np.array([
            0,  1,  2,      0,  2,  3,    # front
            4,  5,  6,      4,  6,  7,    # back
            8,  9,  10,     8,  10, 11,   # top
            12, 13, 14,     12, 14, 15,   # bottom
            16, 17, 18,     16, 18, 19,   # right
            20, 21, 22,     20, 22, 23,   # left
        ], dtype=np.uint).reshape((-1,3))

        print("indices.size", indices.size)

        uvs = np.array([
           # Front
            0.0,  0.0,
            1.0,  0.0,
            1.0,  1.0,
            0.0,  1.0,
            # Back
            0.0,  0.0,
            1.0,  0.0,
            1.0,  1.0,
            0.0,  1.0,
            # Top
            0.0,  0.0,
            1.0,  0.0,
            1.0,  1.0,
            0.0,  1.0,
            # Bottom
            0.0,  0.0,
            1.0,  0.0,
            1.0,  1.0,
            0.0,  1.0,
            # Right
            0.0,  0.0,
            1.0,  0.0,
            1.0,  1.0,
            0.0,  1.0,
            # Left
            0.0,  0.0,
            1.0,  0.0,
            1.0,  1.0,
            0.0,  1.0,
        ], dtype=np.float32).reshape(-1,2)

        # setup VAO
        vao = glGenVertexArrays(1)
        
        pos_vbo, uv_vbo, normal_vbo = glGenBuffers(3) # FIXME: use single vbo for positions and vertices
        glBindVertexArray(vao)
        glBindBuffer(GL_ARRAY_BUFFER, pos_vbo)
        glBufferData(GL_ARRAY_BUFFER, positions.nbytes, positions, GL_STATIC_DRAW)
        position_location = glGetAttribLocation(program, 'position')
        glVertexAttribPointer(position_location, 3, GL_FLOAT, False, 0, buffer_offset(0))
        glEnableVertexAttribArray(position_location)

        uv_location = glGetAttribLocation(program, 'uv')
        if uv_location>=0:
            glBindBuffer(GL_ARRAY_BUFFER, uv_vbo)
            glBufferData(GL_ARRAY_BUFFER, uvs.nbytes, uvs, GL_STATIC_DRAW)
            glVertexAttribPointer(uv_location, 2, GL_FLOAT, False, 0, buffer_offset(0))
            glEnableVertexAttribArray(uv_location)

        normal_location = glGetAttribLocation(program, 'normal')
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

        cube.vao = vao
    finally:
        glBindVertexArray(vao)
        glDrawArray(GL_TRIANGLES, 6*6, GL_UNSIGNED_INT, None)
        glBindVertexArray(0)

def sphere(program):
    try:
        vao = sphere.vao
        ebo = sphere.ebo
    except AttributeError:
        import math
        # create sphere geometry
        """
        reference: [http://www.songho.ca/opengl/gl_sphere.html]
        """
        vertices = []
        normals = []
        texCoords = []

        radius = 0.5
        origin = (0,-0.5,0)
        sectorCount = 8
        stackCount = 8

        #
        sectorStep = 2 * math.pi / sectorCount
        stackStep = math.pi / stackCount

        lengthInv = 1/radius

        for i in range(0, stackCount+1):
            stackAngle = math.pi / 2 - i * stackStep;        # starting from pi/2 to -pi/2
            xy = radius * math.cos(stackAngle);             # r * cos(u)
            y = radius * math.sin(stackAngle);              # r * sin(u)

            # add (sectorCount+1) vertices per stack
            # the first and last vertices have same position and normal, but different tex coords
            for j in range(0, sectorCount+1):
                sectorAngle = j * sectorStep;           # starting from 0 to 2pi

                # vertex position (x, y, z)
                x = xy * math.cos(sectorAngle)             # r * cos(u) * cos(v)
                z = xy * math.sin(sectorAngle)             # r * cos(u) * sin(v)
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
            k1 = i * (sectorCount + 1)     # beginning of current stack
            k2 = k1 + sectorCount + 1      # beginning of next stack

            for j in range(0, sectorCount):
                # 2 triangles per sector excluding first and last stacks
                # k1 => k2 => k1+1
                if i != 0:
                    indices.append(k1 + 1)
                    indices.append(k2)
                    indices.append(k1)
                    
                # k1+1 => k2 => k2+1
                if i != (stackCount-1):
                    indices.append(k2 + 1)
                    indices.append(k2)
                    indices.append(k1 + 1)
                    
                k1+=1
                k2+=1

        positions = np.array(vertices, dtype=np.float32).reshape( (-1, 3))
        
        magnitudes = np.sqrt((positions ** 2).sum(-1))[..., np.newaxis]
        normals = positions/magnitudes
        positions-=origin
        uvs = np.array(texCoords, dtype=np.float32).reshape((-1,2))
        indices = np.array(indices, dtype=np.uint)

        # create VAO
        vao = glGenVertexArrays(1)
        
        pos_vbo, uv_vbo, normal_vbo = glGenBuffers(3) # FIXME: use single vbo for positions and vertices
        glBindVertexArray(vao)
        glBindBuffer(GL_ARRAY_BUFFER, pos_vbo)
        glBufferData(GL_ARRAY_BUFFER, positions.nbytes, positions, GL_STATIC_DRAW)
        position_location = glGetAttribLocation(program, 'position')
        glVertexAttribPointer(position_location, 3, GL_FLOAT, False, 0, buffer_offset(0))
        glEnableVertexAttribArray(position_location)

        uv_location = glGetAttribLocation(program, 'uv')
        if uv_location>=0:
            glBindBuffer(GL_ARRAY_BUFFER, uv_vbo)
            glBufferData(GL_ARRAY_BUFFER, uvs.nbytes, uvs, GL_STATIC_DRAW)
            glVertexAttribPointer(uv_location, 2, GL_FLOAT, False, 0, buffer_offset(0))
            glEnableVertexAttribArray(uv_location)

        normal_location = glGetAttribLocation(program, 'normal')
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

        sphere.vao = vao
        sphere.ebo = ebo
    finally:
        glBindVertexArray(vao)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, ebo)
        glDrawElements(GL_TRIANGLES, (8*13+2)*3, GL_UNSIGNED_INT, None)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, 0)
        glBindVertexArray(0)






