import os, sys
import threading

import gi
#import keyboard as keyboard

from  pynput import keyboard
import serial
import time
import cv2
import json
import numpy as np
from threading import Thread
from time import sleep
from PIL import Image, ImageFilter
from datetime import datetime, date
from matplotlib import pyplot as plt
from openpyxl import load_workbook

import main

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib

nomearq = "/home/lim02/ccnc_v2/imagensmax/02_08_2022_16_47_41_1.0_61.jpg"
#nome = "/home/lim02/ccnc_v2/ccnc_aux/img59.jpg"
img1 = Image.open(nomearq).convert("L")
#img = Image.open(nome).convert("L")
img1.show()
#img1.save("/home/lim02/ccnc_v2/imagensmax/02_08_2022_16_49_11_1.0_61_L.jpg")
threshold = 145
img2 = img1.point(lambda p: p > threshold and 255)
#img3 = img.point(lambda p: p > threshold and 255)
img2.show()
img2.save("/home/lim02/ccnc_v2/imagensmax/02_08_2022_16_49_11_1.0_61_BW.jpg")
#img3.show()

