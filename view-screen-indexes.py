import mss
import cv2
import numpy as np

with mss.mss() as sct:
    for idx, monitor in enumerate(sct.monitors):
        print(f"Monitor {idx}: {monitor}")
        img = np.array(sct.grab(monitor))
        cv2.imshow(f"Monitor {idx}", cv2.resize(img, (480, 270)))
        cv2.waitKey(3000)  # wait 1000 milliseconds (1 second)
        cv2.destroyAllWindows()
