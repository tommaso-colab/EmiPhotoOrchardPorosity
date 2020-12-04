# -*- coding: utf-8 -*-
# 

import cv2
import matplotlib.pyplot as plt
import csv
from MOSES_UndistortImage import Undistort
from pprint import pprint as pp


class ImageAnalysis(object):
    """
    Class which contains functions definition to calculate the crown porosity from a photo.
    """
    def __init__(self, directory, file_list, **kwargs):
        """
        Constructor.
        :param directory: the directory containing the '.jpg' images.
        :param file_list: a list of the file names.
        :param kwargs: - 'sub_sampling_size': number of rows and columns which will form the analysis grid;
                       - 'rejection_area': width of the frame which will be excluded from the analysis, expressed as
                       a percentage. For example 0.1 will exclude the outer 10% of each border
        """
        self.directory = directory
        self.file_list = file_list
        self.threshes = [0.40, 0.43, 0.45, 0.50, 0.55, 0.60, 0.65, 0.70, 0.75, 0.80, 0.85, 0.90, 0.95, 1.10]
        # Setting up algorithm's parameters...
        self.sub_sampling_size = kwargs['sub_sampling_size'] if ('sub_sampling_size' in kwargs.keys()) else 10
        # Default value for sub_sampling_size if the value is too small or absent.
        if self.sub_sampling_size is None or self.sub_sampling_size < 0:
            self.sub_sampling_size = 10

        rejection_area = kwargs['rejection_area'] if ('rejection_area' in kwargs.keys()) else 0
        # Default value for rejection_area if the value is too small or absent.
        if rejection_area is None or rejection_area < 0:
            rejection_area = 0
        if rejection_area > 0.3:
            rejection_area = 0.3

        self.rejection = int(self.sub_sampling_size * rejection_area)

        self.display_results = kwargs['display'] if ('display' in kwargs.keys()) else False

    @staticmethod
    def otsu_binarization(img):
        """
        Performs the binarization of an image using Otsu algorithm.
        :param img: the image.
        :return: the binarized image.
        """
        blur = cv2.GaussianBlur(img, (5, 5), 0)
        remapped = cv2.applyColorMap(blur, cv2.COLORMAP_OCEAN) 
        remapped = cv2.cvtColor(remapped, cv2.COLOR_BGR2GRAY)
        ret, img_otsu = cv2.threshold(remapped, 0, 255, cv2.THRESH_BINARY+cv2.THRESH_OTSU)

        return img_otsu

    def rejection_grid(self, img):
        """
        Builds a list containing rectangles, described by regards of their side position.
        The rectangles on the border of the image are excluded according to rejection_area's value.
        :param img: the image.
        :return: -grid: list of rectangles.
                 -aoi: (area of interest)the rectangle containing all of the elements of grid where the analysis will
                 be actuated.
        """
        h, w = img.shape[:2]
        dw = int(w / self.sub_sampling_size)
        dh = int(h / self.sub_sampling_size)
        grid = []
        for x in xrange(self.rejection, self.sub_sampling_size - self.rejection):
            for y in xrange(self.rejection, self.sub_sampling_size - self.rejection):
                # Defining the coordinates of every rectangle made inside the image excluding the border
                # side according to the 'rejection_area' value.
                d = dict()
                d['x1'] = dw * x
                d['x2'] = dw * (x + 1)
                d['y1'] = dh * y
                d['y2'] = dh * (y + 1)
                if x == self.sub_sampling_size - 1:
                    d['x2'] = w
                if y == self.sub_sampling_size - 1:
                    d['y2'] = h
                grid.append(d)

        aoi = dict()
        # Defines a dictionary which contains the coordinates of the 'aoi' (area of interest),
        # where the analysis will be performed.
        aoi['x1'] = grid[0]['x1']
        aoi['y1'] = grid[0]['y1']
        aoi['x2'] = grid[len(grid) - 1]['x2']
        aoi['y2'] = grid[len(grid) - 1]['y2']
        print 'total_px = ', img.size
        print 'aoi =', (aoi['x2']-aoi['x1'])*(aoi['y2']-aoi['y1'])
        print 'rejection_area =', img.size - (aoi['x2']-aoi['x1'])*(aoi['y2']-aoi['y1'])

        return grid, aoi

    def crown_count(self, img, thresh, grid, aoi):
        """
        Computes the number of pixel of the crown.
        :param img: the image.
        :param thresh: the threshold required for the analysis.
        :param grid: the lists of rectangles.
        :param aoi: the rectangular area which contains every element of grid.
        :return: - number of pixel of the crown (both black and white);
                 - an image which has all the pixel of the large gap (sky) highlighted in gray. None if display_results
                 is false
        """
        binarized = self.otsu_binarization(img)
        display = 0
        if self.display_results:
            display = binarized.copy()
        large_gap_pix = 0
        for roi in grid:
            # Counting the number of white pixel contained in each reagion of interest.
            area = (roi['y2'] - roi['y1']) * (roi['x2'] - roi['x1'])
            wp = cv2.countNonZero(binarized[
                                  roi['y1']:roi['y2'],
                                  roi['x1']:roi['x2']])
            if (float(wp) / float(area)) > thresh:
                # If the ratio between the white pixel and the surface of the rectangle is bigger than the
                # threshold, the count of white pixel for that specific rectangle is added to large_gap_pix
                large_gap_pix = large_gap_pix + wp
                if self.display_results:
                    # Create a copy of the image highlighting the selected pixel.
                    for x in xrange(roi['x1'], roi['x2']):
                        for y in xrange(roi['y1'], roi['y2']):
                            if binarized[y, x] == 255:
                                display[y, x] = 128
        if self.display_results:
            return (aoi['x2']-aoi['x1'])*(aoi['y2']-aoi['y1']) - large_gap_pix, display
        else:
            return (aoi['x2'] - aoi['x1']) * (aoi['y2'] - aoi['y1']) - large_gap_pix, None

    @staticmethod
    def count_black_pixel(img, aoi):
        """
        Performs the counting of black pixels, which represents the foliage cover (leaf_pix).
        :param img: the image.
        :param aoi: the rectangular area which contains every element of grid. Is the analyzed area.
        :return: The amount of black pixel in 'aoi'.
        """
        return (aoi['x2']-aoi['x1'])*(aoi['y2']-aoi['y1']) - cv2.countNonZero(img[aoi['y1']:aoi['y2'],
                                                                              aoi['x1']:aoi['x2']])

    def compute_results(self, bp, img, grid, aoi):
        """

        :param bp: the number of black pixel contained in the image's 'aoi'.
        :param img: the image.
        :param grid: the list of rectangle obtained by 'rejection_grid'.
        :param aoi: the rectangle containing all of the elements of grid where the analysis will be actuated.
        :return: a list that contain all the calculated fraction cover '(leaf_pix / float(crown_pix))'.
        """
        leaf_pix = float(bp)
        fraction_cover = []
        d_list = []
        for t in self.threshes:
            # For each threshold will be computed:
            #    - the number of crown pixel calculated;
            #    - the list of fraction cover calculated;
            #    - the list of coordinates needed for the displaying.
            crown_pix, display = self.crown_count(img, t, grid, aoi)
            if crown_pix == 0.0:
                fraction_cover.append("0.00")
            else:
                fraction_cover.append(leaf_pix / float(crown_pix))
                    
            d_list.append(display)
        if self.display_results:
            # If 'display_results' is true it will be created a windows that contains a picture for each threshold
            # value, showing the algorithm result. The gray pixel are the one identified as part of the sky
            for i in xrange(4):
                for j in xrange(1, 5):
                    if i * 4 + j - 1 >= len(d_list):
                        continue
                    plt.subplot(4, 4, i * 4 + j)
                    plt.imshow(d_list[i * 4 + j - 1], 'gray')
                    plt.title(self.threshes[i * 4 + j - 1])
                    plt.xticks([]), plt.yticks([])
            plt.subplots_adjust(bottom=0, left=0.01, right=0.99,
                                top=0.99, wspace=0.01, hspace=0.01)
            plt.show()
        return fraction_cover

    def analyze_image(self, file_path):
        """
        Performs the analysis of a single image.
        :param file_path: the file path
        :return: - 'fraction_cover': a list that contain all the calculated fraction cover
                   '(leaf_pix / float(crown_pix))' inside the image;
                 - 'leaf_pix': the number of black pixels that represent the foliage cover.
        """
        print 'Analysing: ', file_path
        img = cv2.imread(file_path, cv2.IMREAD_GRAYSCALE)
        grid, aoi = self.rejection_grid(img)
        img_otsu = self.otsu_binarization(img)
        leaf_pix = self.count_black_pixel(img_otsu, aoi)
        fraction_cover = self.compute_results(leaf_pix, img, grid, aoi)

        return fraction_cover, leaf_pix

    def setup_csv(self):
        """
        Defines the setup of the '.csv' file which will contain the results of the analysis. This setup will create the
        header of the table which looks like this:
        'File Name'; 'Leaf pix Count'; 'Porosity'(according to the threshold values).
        :return: Nothing.
        """
        with open(self.directory+'results.csv', 'wb') as f:
            header = ['File Name', 'Leaf pix Count']
            for t in self.threshes:
                if t > 1:
                    header.append('Porosity_Can-EYE_Comparison'.format(t))
                if t < 1:
                    header.append('Porosity {:.2f}'.format(t))
            writer = csv.writer(f, delimiter=';')
            writer.writerow(header)

    def save_to_csv(self, fraction_cover, file_name, leaf_pix):
        """
        Populate the csv table with analysis results
        :param fraction_cover: the fraction cover value.
        :param file_name: the file name.
        :param leaf_pix: the number of black pixels contained in the image's 'aoi'.
        :return: Nothing.
        """
        with open(self.directory+'\\results.csv', 'ab') as f:
            writer = csv.writer(f, delimiter=';')
            row = [file_name, leaf_pix]
            for fc in fraction_cover:
##                print("fc in Cycle")
##                print(float(fc))
                if float(fc) == 0:
##                    print("fc if 0")
##                    print(fc)
                    porosity = 0
                else:
##                    print("fc")
##                    print(fc)
                    porosity = 1-fc
##                    print("porosity")
##                    print(porosity)
                row.append('{:.4f}'.format(porosity))
            writer.writerow(row)

    def analyse_all(self):
        """
        Performs the analysis of all the images contained in the directory defined by the user.
        :return: Nothing.
        """
        self.setup_csv()
        for f in self.file_list:
            full_path = self.directory+f
            fraction_cover, leaf_pix = self.analyze_image(full_path)
##            print("fraction_cover")
##            print(fraction_cover)
##            print("leaf_pix")
##            print(leaf_pix)
            self.save_to_csv(fraction_cover, f, leaf_pix)


def main():
    """
    Performs the Image's undistortion via 'MOSES_UndistortImage.py' then the Image's analysis allowing the user to
    change the values of 'sub_sampling_size', 'rejection_area' and 'display' flags.
    :return: Nothing.
    """
    u = Undistort('.\fotoOUT', None, None)
    directory, file_list = u.get_undistorted_file_path()

    print 'Directory analyzed:', directory
    print 'File list: ', pp(file_list)

    image_analysis = ImageAnalysis(directory, file_list, sub_sampling_size=5, rejection_area=0.1, display=False)
    image_analysis.analyse_all()


if __name__ == '__main__':
    main()
