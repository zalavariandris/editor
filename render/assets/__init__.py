import imageio
from pathlib import Path
assets_folder = Path(__file__).parent

def imread(filename):
	return imageio.imread(Path(assets_folder, filename))