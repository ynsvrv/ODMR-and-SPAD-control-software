import unittest
import random
from matplotlib import pyplot

"""
Taken from a StackOverflow thread: https://stackoverflow.com/questions/2049582/how-to-determine-if-a-point-is-in-a-2d-triangle
Thanks xApple and Phuclv!
(Beware that this code is not consistent with edge cases.
Whether or not the edges are included is dependent on whether the triangle is specified clockwise or anti-clockwise.
So take margins!)
"""

###############################################################################
def point_in_triangle(point, triangle):
    """Returns True if the point is inside the triangle
    and returns False if it falls outside.
    - The argument *point* is a tuple with two elements
    containing the X,Y coordinates respectively.
    - The argument *triangle* is a tuple with three elements each
    element consisting of a tuple of X,Y coordinates.

    It works like this:
    Walk clockwise or counterclockwise around the triangle
    and project the point onto the segment we are crossing
    by using the dot product.
    Finally, check that the vector created is on the same side
    for each of the triangle's segments.
    """
    # Unpack arguments
    x, y = point
    ax, ay = triangle[0]
    bx, by = triangle[1]
    cx, cy = triangle[2]
    # Segment A to B
    side_1 = (x - bx) * (ay - by) - (ax - bx) * (y - by)
    # Segment B to C
    side_2 = (x - cx) * (by - cy) - (bx - cx) * (y - cy)
    # Segment C to A
    side_3 = (x - ax) * (cy - ay) - (cx - ax) * (y - ay)
    # All the signs must be positive or all negative
    return (side_1 < 0.0) == (side_2 < 0.0) == (side_3 < 0.0)

###############################################################################
class TestPointInTriangle(unittest.TestCase):

    triangle = ((22 , 8),
                (12 , 55),
                (7 , 19))

    def test_inside(self):
        point = (15, 20)
        self.assertTrue(point_in_triangle(point, self.triangle))

    def test_outside(self):
        point = (1, 7)
        self.assertFalse(point_in_triangle(point, self.triangle))

    def test_border_case(self):
        """If the point is exactly on one of the triangle's edges,
        we consider it is inside."""
        point = (7, 19)
        self.assertTrue(point_in_triangle(point, self.triangle))

###############################################################################

def graphical_test():
    # The area #
    size_x = 64
    size_y = 64

    # The triangle #
    triangle = ((22 , 8),
                (12 , 55),
                (7 , 19))

    # Number of random points #
    count_points = 10000

    # Prepare the figure #
    figure = pyplot.figure()
    axes = figure.add_subplot(111, aspect='equal')
    axes.set_title("Test the 'point_in_triangle' function")
    axes.set_xlim(0, size_x)
    axes.set_ylim(0, size_y)

    # Plot the triangle #
    from matplotlib.patches import Polygon
    axes.add_patch(Polygon(triangle, linewidth=1, edgecolor='k', facecolor='none'))

    # Plot the points #
    for i in range(count_points):
        x = random.uniform(0, size_x)
        y = random.uniform(0, size_y)
        if point_in_triangle((x,y), triangle): pyplot.plot(x, y, '.g')
        else:                                  pyplot.plot(x, y, '.b')
    pyplot.show()

################################################################################

if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(TestPointInTriangle)
    unittest.TextTestRunner().run(suite)
    graphical_test()