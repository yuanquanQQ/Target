import ContourClassifier as cntr
import Geometry2D as geo2D
import numpy as np
import cv2

def subtract_background(query, subtrahend):
    '''
    Subtract two images, so only the difference between them is left.

    Parameters:
        {Numpy.array} query - The image from which the background is subtracted [RGB]
        {Numpy.array} subtrahend - The background to subtract from the query [RGB]

    Returns:
        {Numpy.array} The difference image.
    '''

    # convert to grayscale
    gray_query = cv2.cvtColor(query, cv2.COLOR_RGB2GRAY)
    gray_subtrahend = cv2.cvtColor(subtrahend, cv2.COLOR_RGB2GRAY)

    # apply gaussian blur
    kernel = (3,3)
    gray_query = cv2.GaussianBlur(gray_query, kernel, 0)
    gray_subtrahend = cv2.GaussianBlur(gray_subtrahend, kernel, 0)

    # apply a black area on the subtrahend image
    gray_subtrahend[gray_query == 0] = 0

    # calculate diff
    diff = cv2.absdiff(gray_subtrahend, gray_query)
    return diff

def emphasize_lines(img, distances, estimatedRadius):
    '''
    Emphasize all of the straight lines in the image and get rid of unnecessary noise.

    Parameters:
        {Numpy.array} img - The image to edit
        {list} distances - [
                              {List} [
                                        {Number} x coordinate of the point,
                                        {Number} y coordinate of the point,
                                        {Number} The distance of the point from the bull'seye point
                                     ]
                              ...
                           ]
        {Number} estimatedRadius - A rough estimation of the target's radius,
                                   that will be used if for some reason it cannot be calculated on the fly.

    Returns:
        {Number} The target's current radius [px].
        {Numpy.array} An image with the lines emphasized.
    '''

    # find the target's outer ring
    circles = cv2.HoughCircles(img, cv2.HOUGH_GRADIENT, 1, 20,
                               param1=50, param2=30, minRadius=0,
                               maxRadius=int(estimatedRadius * 1.05))
    
    # use largest detected circle
    if type(circles) != type(None):
        outerCircle = sorted(circles[0], key=lambda x: x[2])[::-1][0]
        radius = outerCircle[2]
        
    # use a rough estimation of the target's radius as a fallback
    else:
        radius = estimatedRadius

    # zero out all pixels outside of the outer ring
    img[distances[1] > radius] = 0
    
    # apply thresh and morphology
    _, img = cv2.threshold(img, 20, 0xff, cv2.THRESH_BINARY)
    img = cv2.morphologyEx(img, cv2.MORPH_OPEN, np.ones((3,3), np.uint8))

    # find the straight segments in the image
    lines = cv2.HoughLinesP(img, 2, np.pi / 180, 120, minLineLength=20, maxLineGap=0)
    img_copy = np.zeros(img.shape, dtype=img.dtype)

    if type(lines) != type(None):
        for line in lines:
            for x1, y1, x2, y2 in line:
                cv2.line(img_copy, (x1, y1), (x2, y2), (0xff,0xff,0xff), 5)
                
    return radius, img_copy

def reproduce_proj_contours(img, distances, bullseye, radius):
    '''
    Extend the emphasized lines outwards the target circle in order to restore
    the shape of the projectiles that might has been broken during the process.

    Parameters:
        {Numpy.array} img - The image to edit
        {list} distances - [
                              {List} [
                                        {Number} x coordinate of the point,
                                        {Number} y coordinate of the point,
                                        {Number} The distance of the point from the bull'seye point
                                     ]
                              ...
                           ]
        {Tuple} bullseye - (
                              {Number} x coordinate of the bull'seye point,
                              {Number} y coordinate of the bull'seye point
                           )
        {Number} radius - The radius of the target

    Returns:
        {List} A list of the projectiles' contours.
    '''

    # detect the unconvex contours (true projectile contours)
    contours = cv2.findContours(img, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)[-2:]
    rect_contours = cntr.filter_convex_contours(contours[0])
    blank_img = np.zeros(img.shape, dtype=img.dtype)
    
    for cont in rect_contours:
        cntr.extend_contour_line(blank_img, cont, bullseye, length=radius)
    
    # clear unnecessary noise
    blank_img[distances[1] > radius] = 0
    blank_img = cv2.morphologyEx(blank_img, cv2.MORPH_CLOSE, np.ones((3,3), np.uint8))
    
    # detect contours again, after the extension
    return cv2.findContours(blank_img, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)[-2:][0]

def find_suspect_hits(contours, vertices, scale):
    '''
    Find all suspect points in the target that might be hits.

    Parameters:
        {List} contours - [
                             {Numpy.array} A projectile contour
                             ...
                          ]
        {Tuple} A, B, C, D, E vertices (respectively) of the target.
                E.g: A ----------- B
                     |             |
                     |      E      |
                     |             |
                     D ----------- C
                (
                   {tuple} (
                              {Number} x coordinates of point A,
                              {Number} y coordinates of point A
                           ),
                   ...,
                )
        {tuple} scale - (
                            {Number} The average size of the horizontal edges divided by
                                     the average size of the vertical edges (width / height ratio),
                            {Number} The average size of the vertical edges divided by
                                     the average size of the horizontal edges (height / width ratio),
                            {Number} The estimated size of the homography transformation
                                     divided by the estimated size of the target model
                                     (transformed size / actual size ratio)
                        )
    '''

    bullseye = vertices[5]
    res = []
    
    for cont in contours:
        contPts = [(cont[m][0][0],cont[m][0][1]) for m in range(len(cont))]
        point_A = contPts[0] # some random point on the contour

        # find the two furthest points on the contour
        point_B = cntr.contour_distances_from(contPts, point_A)[::-1][0]
        point_A = cntr.contour_distances_from(contPts, point_B)[::-1][0]
        
        # decide which of them is closer to the bullseye point
        A_dist = geo2D.euclidean_dist(point_A, bullseye)
        B_dist = geo2D.euclidean_dist(point_B, bullseye)
        hit = point_A if A_dist < B_dist else point_B

        # straighten the target's oval and find the real hit values
        res_x = (hit[0] - vertices[0][0]) * scale[0] + vertices[0][0]
        res_y = (hit[1] - vertices[0][1]) * scale[1] + vertices[0][1]
        res_dist = geo2D.euclidean_dist(hit, bullseye)
        res_hit = (res_x,res_y,res_dist, bullseye)
        res.append(res_hit)

    return res