#
# Calculate some useful scorecard location values
#
import logging
import math
from math import sin, cos
from typing import List

from numpy import deg2rad
from point2d import Point2D


def get_corners_from_center_size_rotation(
        center: Point2D,
        size: Point2D,
        rotation: float) -> List[Point2D]:
    ''' Get the 4 points of a rectangle with a given
     center, size, and rotation.  Returns a list of
     points that is a polygon.  Rotation is CW.'''
    pt0 = Point2D(center.x - (size.x / 2.), center.y + (size.y / 2.))
    pt1 = Point2D(center.x + (size.x / 2.), center.y + (size.y / 2.))
    pt2 = Point2D(center.x + (size.x / 2.), center.y - (size.y / 2.))
    pt3 = Point2D(center.x - (size.x / 2.), center.y - (size.y / 2.))

    pt0 = rotate_point(pt0, center, rotation)
    pt1 = rotate_point(pt1, center, rotation)
    pt2 = rotate_point(pt2, center, rotation)
    pt3 = rotate_point(pt3, center, rotation)

    polygon = [pt0, pt1, pt2, pt3]
    return polygon


def is_point_in_polygon(
        pt: Point2D,
        polygon: List[Point2D]) -> bool:
    '''Determine if a point is in a polygon.  General solution
    for any polygon that does not contain holes or crossovers.
        pt:  point we are determining
        polygon:  list of points, in order, does NOT have first
            point as last.
    In our use case, polygon is a rotated rectangle, but doesn't
    need to be.

    See: https://wrf.ecse.rpi.edu/Research/Short_Notes/pnpoly.html
    for discussion of underlying algorithm'''
    if len(polygon) < 3:
        logging.warning("Polygon has less than 3 members!!!")
        return False

    # Close the polygon, by making last point same as first
    polygon.append(polygon[0])

    # Go through the sequential pairs of points, toggle is_inside for each
    # crossing
    is_inside = False
    for p1, p2 in zip(polygon, polygon[1:]):
        if ((p1.y > pt.y) != (p2.y > pt.y) and
                pt.x < (p2.x - p1.x) * (pt.y - p1.y) / (p2.y - p1.y) + p1.x):
            is_inside = not is_inside

    return is_inside


def rotate_x_z(x, z, center_x, center_z, rotation):
    '''Rotate a coordinate system by rot (measured CW)
    around a center point.  Calculate new point'''
    rot = deg2rad(-rotation)
    x_shift = x - center_x
    y_shift = z - center_z

    x_prime = x_shift * cos(rot) - y_shift * sin(rot)
    y_prime = x_shift * sin(rot) + y_shift * cos(rot)

    x_prime += center_x
    y_prime += center_z
    return x_prime, y_prime


def rotate_point(p1: Point2D, center: Point2D, rot):
    return Point2D(rotate_x_z(p1.x, p1.y, center.x, center.y, rot))


def calc_dist_point_to_segment(
        E: Point2D,
        A: Point2D,
        B: Point2D) -> float:
    '''find the distance between a line segment and a point.  See:
    https://www.geeksforgeeks.org/minimum-distance-from-a-\
    point-to-the-line-segment-using-vectors/'''

    # Vectors between points
    AB = Point2D(B.x - A.x, B.y - A.y)
    BE = Point2D(E.x - B.x, E.y - B.y)
    AE = Point2D(E.x - A.x, E.y - A.y)

    # Dot products
    AB_BE = AB.x * BE.x + AB.y * BE.y
    AB_AE = AB.x * AE.x + AB.y * AE.y

    # If they are not perpendicular, find the
    # point that is closest and return distance
    if AB_BE > 0:
        return (E - B).r
    elif AB_AE < 0:
        return (E - A).r

    # Finding the perpendicular distance
    x1 = AB.x
    y1 = AB.y
    x2 = AE.x
    y2 = AE.y
    mod = math.sqrt(x1 * x1 + y1 * y1)
    return abs(x1 * y2 - y1 * x2) / mod


def is_point_near_base(pt, center, size, rotation, size_limit) -> bool:
    '''Determine if a point is within size_limit of the 'base' of a
    ramp.  The base is line segment connecting last two pts.'''
    pt2 = Point2D(center.x + (size.x / 2.), center.y - (size.y / 2.))
    pt3 = Point2D(center.x - (size.x / 2.), center.y - (size.y / 2.))
    pt2 = rotate_point(pt2, center, rotation)
    pt3 = rotate_point(pt3, center, rotation)

    min_dist = calc_dist_point_to_segment(pt, pt2, pt3)
    if min_dist <= size_limit:
        return True
    return False


def up_ramp_or_down(A_x, A_z, B_x, B_z, rot):
    '''Determine if we are moving in the direction of a ramp.'''

    # Vector from A to B
    AB = Point2D(B_x - A_x, B_z - A_z)

    # Vector for rotation.  Note that we are using: 0 -> vertical,
    # 90 -> point to right;  180 -> down,  270 -> point to left
    rotation = deg2rad(90 - rot)
    rot_vec = Point2D(cos(rotation), sin(rotation))

    # Dot product
    AB_rot = AB.x * rot_vec.x + AB.y * rot_vec.y
    if AB_rot > 0:
        return True
    return False


def is_on_ramp(
        x,
        z,
        center_x,
        center_z,
        size_x,
        size_z,
        rotation) -> bool:
    '''Helper function to convert to Point2D and perform inside calc'''
    pt = Point2D(x, z)
    center = Point2D(center_x, center_z)
    size = Point2D(size_x, size_z)

    corners = get_corners_from_center_size_rotation(center, size, rotation)
    is_actually_on = is_point_in_polygon(pt, corners)
    # is_near_base = is_point_near_base(pt, center, size, rotation, size_limit)
    return is_actually_on
    # return is_actually_on or is_near_base
