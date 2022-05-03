import unittest
from math import sqrt

from point2d import Point2D

from scorecard.scorecard_location_utils import (
    is_point_in_polygon, rotate_x_z, get_corners_from_center_size_rotation, calc_dist_point_to_segment, up_ramp_or_down)


class TestScorecardLocationutils(unittest.TestCase):

    def test_rotate_point(self):
        # Compare to results at:
        # https://www.emathhelp.net/en/calculators/algebra-2/rotation-calculator/
        x = 3
        z = 5
        center_x = 0
        center_z = 0
        rot = 33
        x_p, z_p = rotate_x_z(x, z, center_x, center_z, rot)
        self.assertAlmostEqual(5.2392, x_p, delta=0.0001)
        self.assertAlmostEqual(2.55943, z_p, delta=0.0001)

        x = -4
        z = 1.5
        center_x = -1
        center_z = -1
        rot = 61
        x_p, z_p = rotate_x_z(x, z, center_x, center_z, rot)
        self.assertAlmostEqual(-0.26787, x_p, delta=0.0001)
        self.assertAlmostEqual(2.83588, z_p, delta=0.0001)

    def test_get_polygon_from_center_size_rotation_1(self):
        center = Point2D(0, 0)
        size = Point2D(1, 1)
        rotation = 60

        polygon = get_corners_from_center_size_rotation(center, size, rotation)
        pt1 = polygon[3]
        # should be x_contrib = 0.5 / 2.;  z_contrib = sqrt(3)/2 / 2.
        x_expected = 0.25 * sqrt(3) + 0.25
        self.assertAlmostEqual(-x_expected, pt1.x, delta=0.0001)

    def test_get_polygon_from_center_size_rotation_2(self):
        # This is ramp_lower from ramps_eval_5_ex_1.json
        center = Point2D(1.5, 1)
        size = Point2D(2, 1)
        rotation = 90

        polygon = get_corners_from_center_size_rotation(center, size, rotation)
        pt = polygon[0]
        x_expected = 2.0
        y_expected = 2.0
        self.assertAlmostEqual(x_expected, pt.x, delta=0.0001)
        self.assertAlmostEqual(y_expected, pt.y, delta=0.0001)

    def test_get_polygon_from_center_size_rotation_3(self):
        '''Random values, computed with https://keisan.casio.com/exec/system/1223522781 '''
        center = Point2D(-3., 2.)
        size = Point2D(5, 4)
        rotation = -217

        # Point 3 is (originally lower right), so if doing coord transform
        # of size, you should add size to x and subtract from z.
        # Then rotate coordinate frame.

        polygon = get_corners_from_center_size_rotation(center, size, rotation)
        pt = polygon[3]
        x_expected = -2.20704
        y_expected = 5.1018
        self.assertAlmostEqual(x_expected, pt.x, delta=0.0001)
        self.assertAlmostEqual(y_expected, pt.y, delta=0.0001)

    def test_is_point_in_polygon(self):
        pt = Point2D(0.5, 0.5)
        polygon = [Point2D(0, 0), Point2D(1, 0), Point2D(1, 1), Point2D(0, 1)]
        is_inside = is_point_in_polygon(pt, polygon)
        self.assertTrue(is_inside)

        pt = Point2D(1.01, -0.1)
        is_inside = is_point_in_polygon(pt, polygon)
        self.assertFalse(is_inside)

        # Concave polygon example
        # This one is not in the polygon
        pt = Point2D(4, 4)
        polygon = [
            Point2D(6.1, 5.80),
            Point2D(8.0, 2.9),
            Point2D(5.8, 0.6),
            Point2D(1.2, 2.86),
            Point2D(5.5, 3),
        ]
        is_inside = is_point_in_polygon(pt, polygon)
        self.assertFalse(is_inside)

        # But this one is
        pt = Point2D(6.5, 4.5)
        is_inside = is_point_in_polygon(pt, polygon)
        self.assertTrue(is_inside)

    def test_calc_dist_point_to_segment(self):
        E = Point2D(1, 1)
        A = Point2D(0, 0)
        B = Point2D(2, 0)
        dist = calc_dist_point_to_segment(E, A, B)
        self.assertAlmostEqual(1, dist, delta=0.0001)

        E = Point2D(5, 4)
        dist = calc_dist_point_to_segment(E, A, B)
        self.assertAlmostEqual(5, dist, delta=0.0001)

        # From: https://www.mathportal.org/calculators/analytic-geometry/line-point-distance.php
        E = Point2D(-3.75, -4)
        A = Point2D(-4, 1)
        B = Point2D(-2.5, -2)
        dist = calc_dist_point_to_segment(E, A, B)
        self.assertAlmostEqual(2.3585, dist, delta=0.0001)

    def test_up_ramp_or_down(self):
        A = Point2D(0, 0)
        B = Point2D(0, 1)
        rot = 0
        up = up_ramp_or_down(A.x, A.y, B.x, B.y, rot)
        self.assertTrue(up)
