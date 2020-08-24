"""single VBO from structured ndarray to VAO"""
offset = 0
vbo = gloo.VBO(vertices)
gtypes={
	np.float32: GL_FLOAT
}
for name in vertices.dtype.names:
	location = shader.get_attribute_location(name)
	size = vertices[name].shape[1]
	gtype = gtypes[np.float32]
	stride = vertices.itemsize
	vao.enable_vertex_attribute(location)
	vao.add_vertex_attribute(location, vbo, size, GL_FLOAT, stride=stride, offset=offset)
	offset+=vertices.dtype[name].itemsize