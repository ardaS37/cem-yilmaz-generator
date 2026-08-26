import cv2
import numpy as np
class Show:
    def __init__(self):
        pass
    def goster(self):
        imagelocation = "images/"
        generatedlocation = "generated_images/"
        image1 = "cmorjinal.jpg"
        image2 = "onplan.png"
        size = (236, 291)
        image1cv = cv2.imread(imagelocation + image1)
        image2cv = cv2.imread(imagelocation + image2)
        image2cv = cv2.resize(image2cv, size)
        sum = cv2.add(image1cv, image2cv)
        cv2.imshow("sum", sum)
        cv2.waitKey()
        cv2.destroyAllWindows()