#
# Useful utility functions
#

def minAngDist(a, b):
    """Calculate the difference between two angles in degrees, keeping
    in mind that 0 and 360 are the same.  Also, keep value in range [0-180].
    You cannot just do an abs(a-b).    """
    normDeg = (a - b) % 360
    minAng = min(360 - normDeg, normDeg)
    return minAng


# print(f"{minAngDist(20, 15)}")
# print(f"{minAngDist(20, -15)}")
# print(f"{minAngDist(-20, 15)}")
# print(f"{minAngDist(-20, -15)}")
# print(f"{minAngDist(11, 354)}")
# print(f"{minAngDist(-11, 354)}")
