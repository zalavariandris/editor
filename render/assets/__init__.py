import imageio
import numpy as np
from pathlib import Path
assets_folder = Path(__file__).parent

def imread(filename):
	return imageio.imread(Path(assets_folder, filename))

def to_srgb(img, gamma=2.2):
	return np.power(img, (1/gamma, 1/gamma, 1/gamma))

def to_linear(img, gamma=2.2):
	return np.power(img, (gamma, gamma, gamma))