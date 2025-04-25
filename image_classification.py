#data frame
import pandas as pd
import numpy as np
#machine training 
import seaborn as sns
import os
from PIL import Image, ImageOps
from sklearn.model_selection import train_test_split
#model classification
# pyright: reportMissingImports=false
import tensorflow as tf
from tensorflow.keras.models      import Sequential
from tensorflow.keras.layers      import Conv2D, MaxPooling2D, Activation, Dropout, Flatten, Dense
from tensorflow.keras.preprocessing.image import ImageDataGenerator

#loading data
