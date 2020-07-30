import cv2

from utils import memoize

@memoize
def getVideoCapture(filePath):
    return cv2.VideoCapture(filePath)

@memoize
def readCapture(cap, frame):
    cursor = cap.get(cv2.CAP_PROP_POS_FRAMES)
    if frame!=cursor:
        print("set cursor")
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame)

    ret, img = cap.read()
    return img

def read(path, frame):
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
        print(endTime-startTime)
        frame+=1
        cv2.imshow("hello", img)

        if cv2.waitKey(1)==27:
            break



    
    cv2.destroyAllWindows()