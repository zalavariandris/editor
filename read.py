import cv2
import numpy as np
from editor.utils import memoize


@memoize
def getVideoCapture(filePath: str)->cv2.VideoCapture:
    return cv2.VideoCapture(filePath)


@memoize
def readCapture(cap:cv2.VideoCapture, frame)->np.ndarray:
    cursor = cap.get(cv2.CAP_PROP_POS_FRAMES)
    if frame!=cursor:
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame)

    ret, img = cap.read()
    return img


def read(path: str, frame: int)->np.ndarray:
    """Return a frame of an video or image sequence a path
    opencv based read function with memoize builtin: each frame of every path
    """
    cap = getVideoCapture(path)
    return readCapture(cap, frame)


if __name__ == "__main__":
    from time import time

    frame = 0
    while True:
        startTime = time()
        img = read("C:/Users/andris/Desktop/2020 Paks/Grassblade/footage/IMG_9148.MOV", frame)
        endTime = time()
        frame+=1
        cv2.imshow("hello", img)
        print( type(img) )

        if cv2.waitKey(1)==27:
            break

    cv2.destroyAllWindows()