# -*- coding: utf-8 -*-
# 

from MOSES_ImageAnalysis import ImageAnalysis
from MOSES_UndistortImage import Undistort
import time
import subprocess
import argparse
import os
"""
Performs a full image's undistortion and analysis on all the images of a given folder. If called with '-c' it runs a
calibration prior to undistortion. The calibration is performed using a C++ executable; mind because some
of its parameters are hard coded in this main function (calibration_app_path).
The image's undistortion is performed via 'MOSES_UndistortImage.py', while the image's analysis is performed via
'MOSES_ImageAnalysis.py'.
"""
###########################################################################
#FUNZIONI estratte da UNDISTORT
def get_image_list(image_directory):
    """
    Creates a list of the '.jpg' files contained in 'self.image_directory'.
    :return: a list containing a dictionary for each '.jpg' image. Each dictionary has two keys: name (the name of
    the file), path (the complete file path).
    """
    file_list = []
    for f in os.listdir(image_directory):
        if f.endswith('.jpg'):
            file_list.append({"path": image_directory+'\\'+f, "name": f})
    return file_list

def get_undistorted_file_path(file_list, directory):
    """
    Gets the directory containing the processed images and a list of their file names.
    :return: the directory and the list
    """
    name_list = [x['name'] for x in file_list]
    directory = directory
    return directory+"\\", name_list
###########################################################################   
#importante: con chiamata -c FA CALIRBAZIONE, con chiamata -D NON FA UNDISTORT
##IMPOSTA CARTELLA DI LAVORO:

path =".\FOTO_CC_05072018"
print("####path")
print(path)
parameters_path = 'out_CAMERADATA_Orizzontal.xml'

#valuta parametri di run
parser = argparse.ArgumentParser(description='Undistort images.')
parser.add_argument('-c', action='store_true',
                    help='run calibration prior to undistorting')
parser.add_argument('-d', action='store_true')
args = parser.parse_args()
calibrate = args.c
SkipUndist = args.d
##
if calibrate:
    calibration_app_path = [".\Camera_Calibration_Orizzontal.exe",
                                ".\default_orizzontal.xml"]
    print "Calibration in progress..."
    calibration = subprocess.check_output(calibration_app_path)
    time.sleep(1)
##
if SkipUndist:
    
    file_listPATH = get_image_list(path)
    directory, file_list = get_undistorted_file_path(file_listPATH, path)
    print "file_list"
    print file_list
    print "directory"
    print directory    
else:   
    print "Elimination of distortion process is starting..."
    cm = Undistort.load_from_xml(parameters_path, 'Camera_Matrix')
    dc = Undistort.load_from_xml(parameters_path, 'Distortion_Coefficients')   
    u = Undistort(path, cm, dc)
    print("cm parameters:" ,  cm)
    print("dc parameters:" ,  dc)
    u.undistort_all()
    print "Elimination of distortion process completed!"
    directory, file_list = u.get_undistorted_file_path()
    print("directory")
    print(directory)
    print("file_list")
    print(file_list)
## ESEGUI CALCOLO CANOPY COVER
threshes = [0.40, 0.43, 0.45, 0.50, 0.55, 0.60, 0.65, 0.70, 0.75, 0.80, 0.85, 0.90, 0.95, 1.10]
print "Analysis is starting..."
image_analysis = ImageAnalysis(directory, file_list, sub_sampling_size=15, rejection_area=0.1, display=True)
image_analysis.analyse_all()
print "Analysis is completed!"





