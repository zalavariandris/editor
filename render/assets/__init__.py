import imageio
import numpy as np
from pathlib import Path
assets_folder = Path(__file__).parent
import singledispatch
import glm
import math

def imread(filename):
	return imageio.imread(Path(assets_folder, filename))


def to_srgb(value, gamma=2.2):
	gamma = 1/gamma
	if isinstance(value, np.ndarray) and value.shape == (3, ):
		return np.power(value, (gamma, gamma, gamma)).astype(value.dtype)
	elif isinstance(value, np.ndarray) and len(value.shape)==3 and value.shape[2] == 3:
		return np.power(value, (gamma, gamma, gamma)).astype(value.dtype)
	elif isinstance(value, glm.vec3):
		return glm.vec3(math.pow(value.r, gamma), math.pow(value.g, gamma), math.pow(value.b, gamma))
	elif isinstance(value, tuple) and len(value) == 3:
		return (math.pow(value[0], gamma), math.pow(value[1], gamma), math.pow(value[2], gamma))
	else:
		raise NotImplementedError("for value: {}".format(value))


def to_linear(value, gamma=2.2):
	if isinstance(value, np.ndarray) and value.shape == (3, ):
		return np.power(value, (gamma, gamma, gamma)).astype(value.dtype)
	elif isinstance(value, np.ndarray) and len(value.shape)==3 and value.shape[2] == 3:
		return np.power(value, (gamma, gamma, gamma)).astype(value.dtype)
	elif isinstance(value, glm.vec3):
		return glm.vec3(math.pow(value.r, gamma), math.pow(value.g, gamma), math.pow(value.b, gamma))
	elif isinstance(value, tuple) and len(value) == 3:
		return (math.pow(value[0], gamma), math.pow(value[1], gamma), math.pow(value[2], gamma))
	else:
		raise NotImplementedError("for value: {}".format(value))