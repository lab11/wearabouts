#!/usr/bin/env python3

import os

filenames = ""
for index in range(10):
    filenames += "labels_" + str(index) + ".gif "
    os.system("convert labels_" + str(index) + ".eps -background white -alpha remove labels_" + str(index) + ".gif")

os.system("convert " + filenames + "-dispose background -set delay 100 -loop 0 labels_animated.gif")
os.system("rm " + filenames)

