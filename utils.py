def convert_cvImgToPixmap(cvImg):

    from PySide2.QtGui import QImage, QPixmap
    # convert to pixmap
    height, width, channel = cvImg.shape
    bytesPerLine = 3 * width
    qImg = QImage(cvImg.data, width, height, bytesPerLine, QImage.Format_RGB888)
    return QPixmap.fromImage(qImg)


class memoize:
    def __init__(self, fn):
        self.fn = fn
        self.memo = dict()

    def __call__(self, *args):
        if args not in self.memo:
            self.memo[args] = self.fn(*args)
        return self.memo[args]

import time   
import contextlib
@contextlib.contextmanager
def profile(name, disabled=False):
    starttime = time.time()
    yield
    endtime = time.time()
    deltatime = endtime-starttime
    if not disabled:
        print("{} {:.0f} fps".format(name, 1/deltatime if deltatime>0 else float('inf')))

