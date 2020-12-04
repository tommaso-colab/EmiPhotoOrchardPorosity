# -*- coding: utf-8 -*-
# 

import numpy as np
import cv2
import os
import xml.etree.ElementTree as Et
import subprocess
import time
import argparse


class Undistort(object):
    """
    Class which contains functions definition to perform the fish-eye distortion removal from set of images.
    """
    def __init__(self, img_dir, cam_matrix, dist_c):
        """
        Constructor.
        img_dir : directory path containing '.jpg' images;
        cam_matrix : camera's matrix obtained from the camera calibration process;
        dist_c : camera's distortion coefficient obtained from the camera calibration process;
        """
        self.image_directory = img_dir
        self.save_path = img_dir + '\Undistorted_Images'
        if not os.path.exists(self.save_path):
            os.makedirs(self.save_path)

        self.file_list = self.get_image_list()
        self.camera_matrix = cam_matrix
        self.distortion_coefficient = dist_c

        if len(self.file_list) > 0:
            if cam_matrix is not None and dist_c is not None:
                img = cv2.imread(self.file_list[0]["path"])
                h, w = img.shape[:2]
                print("img.shape")
                print(img.shape)
                self.newcameramtx, self.roi = cv2.getOptimalNewCameraMatrix(self.camera_matrix,
                                                                            self.distortion_coefficient,
                                                                            (w, h),
                                                                            1,
                                                                            (w, h))
                print("newOptimalCameraMatrix")
                print(self.newcameramtx)
                print("self.roi")
                print(self.roi)
        else:
            print "ERROR: Empty folder: .jpg files required"

    def get_image_list(self):
        """
        Creates a list of the '.jpg' files contained in 'self.image_directory'.
        :return: a list containing a dictionary for each '.jpg' image. Each dictionary has two keys: name (the name of
        the file), path (the complete file path).
        """
        file_list = []
        for f in os.listdir(self.image_directory):
            if f.endswith('.jpg'):
                file_list.append({"path": self.image_directory+'\\'+f, "name": f})
        return file_list

    def undistort_image(self, image_path):
        """
        Performs the actual distortion removal on single image.
        :param image_path: the image file path.
        :return: the undistorted image. The size of which is different than the original image's to account the region
        of interest (roi).
        """
        img = cv2.imread(image_path)
        dst = cv2.undistort(img, self.camera_matrix, self.distortion_coefficient, None, self.newcameramtx)

        x, y, w, h = self.roi

        return dst[y: y + h, x: x + w]

    def undistort_all(self):
        """
        Performs undistortion on all images and save the results to file.
        :return: Nothing
        """
        for image_path in self.file_list:
            img = self.undistort_image(image_path['path'])
            print "saving:", image_path['name']
            cv2.imwrite(self.save_path+'\\' + image_path['name'], img)

    def get_undistorted_file_path(self):
        """
        Gets the directory containing the processed images and a list of their file names.
        :return: the directory and the list
        """
        name_list = [x['name'] for x in self.file_list]
        directory = self.save_path

        return directory+"\\", name_list

    @staticmethod
    def load_from_xml(path, data_name):
        """
        Extracts parameters from the calibration results file. It works only for parameter which are matrix.
        :param path: the result's file path.
        :param data_name: the name of the parameter to extract from the file.
        :return: the requested parameter.
        """
        tree = Et.parse(path)
        root = tree.getroot()
        data_container = root.find(data_name).find('data')
        rows = int(root.find(data_name).find('rows').text)
        cols = int(root.find(data_name).find('cols').text)
        matrix = []
        elements = data_container.text.split()

        for i in range(0, cols):
            matrix.append([])
            for j in range(0, rows):
                matrix[i].append(float(elements[rows * i + j]))

        return np.array(matrix)


def main():
    """
    Performs a full undistortion on all the images of a given folder. If called with '-c' it runs a calibration prior
    to undistorting. The calibration is performed using a C++ executable; mind because some of its parameters are hard
    coded in this main function (calibration_app_path).
    :return: Nothing.
    """
    parser = argparse.ArgumentParser(description='Undistort images.')
    parser.add_argument('-c', action='store_true',
                        help='run calibration prior to undistorting')

    args = parser.parse_args()
    parameters_path = 'out_CAMERADATA_Orizzontal.xml'
    calibrate = args.c
    if calibrate:
        calibration_app_path = [".\Calibrazione_Camera_c++\Camera_Calibration_Orizzontal.exe",
                                ".\Calibrazione_Camera_c++\default_orizzontal.xml"]
        print "Calibration in progress..."
        calibration = subprocess.check_output(calibration_app_path)
        time.sleep(1)
    print "Elimination of distortion process is starting"
    cm = Undistort.load_from_xml(parameters_path, 'Camera_Matrix')
    dc = Undistort.load_from_xml(parameters_path, 'Distortion_Coefficients')
    print 'Camera Matrix = ', cm
    print 'Distortion Coefficient = ', dc
    directory = (".\fototest")
    
    u = Undistort(directory, cm, dc)
    u.undistort_all()

if __name__ == '__main__':
    main()
