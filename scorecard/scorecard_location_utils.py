#
# Calculate some useful scorecard location values
#
import logging
from math import sin, cos
from typing import List

from numpy import deg2rad
from point2d import Point2D


def get_polygon_from_center_size_rotation(
        center: Point2D,
        size: Point2D,
        rotation: float) -> List[Point2D]:
    '''Determine 4 corner points of rectangle from data given
    center:  (x,z) of the center of the object
    size:  (x_size, z_size) total size, so 1/2 that from center
    rotation:  degrees from vertical, going clockwise
    '''
    rot = deg2rad(rotation)
    dx_x = size.x * cos(rot) / 2.
    dz_x = size.x * sin(rot) / 2.

    dx_z = size.y * sin(rot) / 2.
    dz_z = size.y * cos(rot) / 2.

    pt1_x = center.x + (dx_x + dx_z)
    pt1_z = center.y + (-dz_x + dz_z)
    pt1 = Point2D(pt1_x, pt1_z)

    pt2_x = center.x + (dx_x - dx_z)
    pt2_z = center.y + (-dz_x - dz_z)
    pt2 = Point2D(pt2_x, pt2_z)

    pt3_x = center.x + (-dx_x - dx_z)
    pt3_z = center.y + (dz_x - dz_z)
    pt3 = Point2D(pt3_x, pt3_z)

    pt4_x = center.x + (-dx_x + dx_z)
    pt4_z = center.y + (dz_x + dz_z)
    pt4 = Point2D(pt4_x, pt4_z)

    polygon = [pt1, pt2, pt3, pt4]
    return polygon


def get_polygon_from_center_size_rotation2(
        center: Point2D,
        size: Point2D,
        rotation: float) -> List[Point2D]:
    pt1 = Point2D(center.x - (size.x / 2.), center.y + (size.y / 2.))
    pt2 = Point2D(center.x + (size.x / 2.), center.y + (size.y / 2.))
    pt3 = Point2D(center.x + (size.x / 2.), center.y - (size.y / 2.))
    pt4 = Point2D(center.x - (size.x / 2.), center.y - (size.y / 2.))

    pt1 = rotate_point(pt1, center, rotation)
    pt2 = rotate_point(pt2, center, rotation)
    pt3 = rotate_point(pt3, center, rotation)
    pt4 = rotate_point(pt4, center, rotation)

    print(f"{pt1}")
    print(f"{pt2}")
    print(f"{pt3}")
    print(f"{pt4}")

    polygon = [pt1, pt2, pt3, pt4]
    return polygon


def is_point_in_polygon(pt: Point2D, polygon: List[Point2D]):
    '''Determine if a point is in a polygon.  General solution
    for any polygon that does not contain holes or crossovers.
    pt:  point we are determining
    polygon:  list of points, in order, does NOT have first
    point as last

    See: https://wrf.ecse.rpi.edu/Research/Short_Notes/pnpoly.html
    for discussion'''
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


def rotate_point(p1: Point2D, center: Point2D, rot):
    return Point2D(rotate_x_z(p1.x, p1.y, center.x, center.y, rot))


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


def is_point_near_base(pt, center, size, rotation) -> bool:
    return False


def is_on_ramp(x, z, center_x, center_z, size_x, size_z, rotation) \
        -> bool:
    '''Helper function to convert to Point2D and perform inside calc'''
    pt = Point2D(x, z)
    center = Point2D(center_x, center_z)
    size = Point2D(size_x, size_z)

    is_actually_on = is_point_in_polygon(
        pt,
        get_polygon_from_center_size_rotation(center, size, rotation))
    is_near_base = is_point_near_base(pt, center, size, rotation)
    return is_actually_on
