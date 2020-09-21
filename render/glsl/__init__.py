from pathlib import Path
import logging
import functools


@functools.lru_cache(maxsize=128)
def read(*args):
	logging.debug("read {}".format(args))
	glsl_folder = Path(__file__).parent
	if len(args) == 1:

		shader = args[0]
		vertex = Path(glsl_folder, shader+'.vs').read_text()
		fragment = Path(glsl_folder, shader+'.fs').read_text()

		# look for optional geometry shader
		if Path(glsl_folder, shader+'.gs').exists():
			geometry = Path(glsl_folder, shader+'.gs').read_text()
			return vertex, fragment, geometry
		else:
			return vertex, fragment
	elif len(args) == 2:
		"""vertex and fragment shader"""
		vertex, fragment = args
		return Path(glsl_folder, vertex).read_text(), Path(glsl_folder, fragment).read_text()
	elif len(args == 3):
		"""vertex, fragment and geometry shader"""
		vertex, fragment, geometry = args
		return Path(glsl_folder, vertex).read_text(), Path(glsl_folder, fragment).read_text(), Path(glsl_folder, geometry).read_text()
	else:
		raise NotImplementedError()