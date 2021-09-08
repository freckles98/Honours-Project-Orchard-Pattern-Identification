import math
import time

import shapely.affinity
from shapely.affinity import affine_transform, translate, rotate
import sys

from shapely.geometry import Point

import generateShape as gs
import hausdorffDistance as hd
import numpy as np
import multiprocessing as mp


class PatternNode:
    def __init__(self, point, shape, confidence):
        self.point = point
        self.shape = shape
        self.confidence = confidence




class MatchingModel:
    def __init__(self, distance, model):
        self.distance = distance
        self.model = model


def rotations(point_set):
    return rotate(point_set, 15, origin='center')

def rotate_back(point_set):
    return rotate(point_set, -180, origin='center')

def translations(point_set, x, y):
    return translate(point_set, x, y, 0)


def normalize_data(data):
    num_trees = data[1]
    centroids = data[0]
    convex = centroids.convex_hull
    area = convex.area
    density = num_trees / area

    centroids = shapely.affinity.scale(centroids, math.sqrt(density), math.sqrt(density))
    rectangle = centroids.minimum_rotated_rectangle
    x, y = rectangle.exterior.coords.xy
    translation_index = y.index(min(y))
    translation_x = x[translation_index] #x
    translation_y = y[translation_index] #y

    rotation_index = x.index(max(x))
    rotation_x = x[rotation_index] #a
    rotation_y = y[rotation_index] #b
    distance_x = math.sqrt((translation_x - rotation_x)**2+(translation_y - translation_y)**2)
    distance_y = math.sqrt((rotation_x - rotation_x)**2+(rotation_y - translation_y)**2)
    angle = math.atan(distance_y/distance_x)
    centroids = rotate(centroids, -angle, origin=Point(translation_x, translation_y), use_radians=True)
    gs.display_data(centroids, 0)
    centroids = translations(centroids, -translation_x,-translation_y)
    gs.display_data(centroids, 0)
    return centroids

def matching_the_pattern(model, data_set, shape, pattern, data):

    minimum = np.inf
    matching_model = MatchingModel(minimum, model)
    final_pattern = []
    switch = False
    flag = False
    start = time.time()
    # need to change the range
    for y in range(int(5)):
        for x in range(int(5)):
            for z in range(12):

                haus = hd.hausdorff(model, data_set, shape, pattern)
                dist = haus[0]
                pattern = haus[1]
                if 0 <= dist < matching_model.distance:
                    matching_model = MatchingModel(dist, model)
                    final_pattern = pattern
                model = rotations(model)

            model = rotate_back(model)
            print("end of rotations", x)
            if switch == False:
                model = translations(model, 0.2, 0)
            else:
                model = translations(model, -0.2, 0)



        if switch:
            switch = False
        else:
            switch = True
        if flag == True:
            break
        model = translations(model, 0, 0.2)
        #gs.display_data(data, matching_model.model)

    #if minimum == np.inf:
        #print("no match")
    #gs.display_data(matching_model.model, data)
    #gs.display_data(data, 0)
    gs.display_data(matching_model.model,0)
    end = time.time()
    print(end-start)
    return (matching_model, final_pattern)

def execute_over_entire_pattern(model, data, shape, pattern):
    area = data.minimum_rotated_rectangle
    xcord, ycord = area.exterior.coords.xy

    list_of_matches = []
    switch = False

    for y in range(0, int(max(ycord)), 10):

        for x in range(0, int(max(xcord)), 10):

            area = model.minimum_rotated_rectangle
            data_set = []
            for point in data:
                if area.contains(point) or area.touches(point):
                    data_set.append(point)
            data_set = gs.to_multipoint(data_set)
            #print(data_set[0])

            gs.display_data(data_set, 0)
            # change this not hausdorff best pattern match
            if len(data_set) > 0:
                matches = matching_the_pattern(model, data_set, shape, pattern, data)
                pattern.append(matches[1])
                list_of_matches.append(matches[0])


            if not switch:
                model = translations(model, 10, 0)
            else:
                model = translations(model, -10, 0)

        if switch:
            switch = False
        else:
            switch = True
        model = translations(model, 0, 10)
        print("Okay going up", y)
        #gs.display_data(model, data)
    return list_of_matches, pattern




def best_pattern_match(data, pattern):
    model1 = gs.square_set(0, 0, 10, 10, True)
    model2 = gs.diamond_set(0, 0, 10, 10, True)
    model3 = gs.double_row(0, 10, True)
    gs.display_data(model1, 0)
    pool = mp.Pool(mp.cpu_count())
    min1 = execute_over_entire_pattern(model1, data, "square", pattern)
    pattern_square = min1[1]
    gs.display_data_pattern(pattern_square, data)


    min2 = execute_over_entire_pattern(model2, data, "diamond", pattern)
    pattern_diamond = min2[1]
    min3 = execute_over_entire_pattern(model3, data, "double", pattern)
    pattern_double_row = min3[1]

    for x in range(len(pattern_square)):
        if pattern_square[x].confidence < pattern_diamond[x].confidence:
            if pattern_square[x].confidence < pattern_double_row[x].confidence:
                return

    print("Min1", min1[0][0].distance, "min2", min2[0][0].distance, "min3", min3[0][0].distance)
    for x in range(len(min1)):
        if min1[0][x].distance == -1:
            if min2[0][x].distance == -1:
                if min3[0][x].distance == -1:
                    print("No match")
                else:
                    # gs.display_data(min3[x].model, data)
                    print("Matching pattern: double row")
                    return min3[x].model, "Double", pattern
            elif min3[0][x].distance == -1 or min2[x].distance < min3[x].distance:

                # gs.display_data(min2[x].model, data)
                print("Matching pattern: diamond")
                return min2[0][x].model, "Diamond", pattern

            else:
                # gs.display_data(min3[x].model, data)
                print("Matching pattern: double row")
        elif min2[0][x].distance != -1:
            if min3[0][x].distance != -1:
                if min1[0][x].distance < min2[0][x].distance and min1[0][x].distance < min3[0][x].distance:
                    # gs.display_data(min1[x].model, data)
                    print("Matching pattern: square")
                    return min1[0][x].model, "Square", pattern
                elif min2[0][x].distance < min3[0][x].distance and min2[0][x].distance < min1[0][x].distance:
                    # gs.display_data(min2[x].model, data)
                    print("Matching pattern: diamond")
                    return min2[0][x].model, "Diamond", pattern
                elif min3[0][x].distance < min1[0][x].distance and min3[0][x].distance < min2[0][x].distance:
                    # gs.display_data(min3[x].model, data)
                    print("Matching pattern: double row")
                    return min3[0][x].model, "Double", pattern
            else:
                if min1[0][x].distance < min2[0][x].distance:
                    # gs.display_data(min1.model, data)
                    print("Matching pattern: square")
                    return min1[0][x].model, "Square", pattern
                else:
                    # gs.display_data(min2[x].model, data)
                    print("Matching pattern: diamond")
                    return min2[0][x].model, "Diamond", pattern
        else:
            # gs.display_data(min1[x].model, data)
            print("Matching pattern: square")

def initialize_pattern_node(points):
    pattern = []
    for index, point in enumerate(points):

        pattern.append(PatternNode(Point(point.x, point.y), "none", np.inf))
    return pattern

def main():
    print("let the games begin")
    #data = gs.square_set(0, 0, 30, 30, True)
    data = gs.importData()
    data = normalize_data(data)


    pattern = initialize_pattern_node(data)

    best_match = best_pattern_match(data, pattern)
    #gs.display_data(best_match[2], 0)
    print(best_match[2])
    gs.display_data_pattern(best_match[2])


if __name__ == "__main__":
    main()
