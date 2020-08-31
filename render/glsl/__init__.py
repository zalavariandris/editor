from pathlib import Path

def read(*args):
	glsl_folder = Path(__file__).parent
	if len(args)==1:
		shader = args[0]
		return Path(glsl_folder, shader+'.vs').read_text(), Path(glsl_folder, shader+'.fs').read_text()
	elif len(args)==2:
		vertex, fragment = args
		return Path(glsl_folder, vertex).read_text(), Path(glsl_folder, fragment).read_text()
	else:
		raise NotImplementedError