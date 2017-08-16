# -*- coding: utf-8 -*-
# Author: Umesh Mohan (umesh@heterorrhina.in)

# From: https://www.w3.org/TR/SVG/implnote.html#ArcImplementationNotes 
# (F.6.4 - F.6.6) and the paper "Approximation of a cubic bezier curve by
# circular arcs and vice versa", Aleksas Riškus, 2006: used with correction 
# in function smallArc

from math import sin, cos, acos, pi, sqrt, fabs
from numpy import dot, array
from numpy.linalg import norm

def angleBetween(u, v):
    # F.6.5 - Step 4
    if u[0]*v[1] - u[1]*v[0] < 0:
        sign = -1
    else:
        sign = 1
    return sign * acos(dot(u, v) / (norm(u) * norm(v)))

def arcCenterToEndpoint(cx, cy, rx, ry, phi, theta_1, delta_theta):
    # F.6.4
    cos_phi = cos(phi)
    sin_phi = sin(phi)
    rotation_matrix = [[cos_phi, -sin_phi], [sin_phi, cos_phi]]

    x1, y1 = dot(rotation_matrix, [rx * cos(theta_1), ry * sin(theta_1)]) + \
             [cx, cy]
    x2, y2 = dot(rotation_matrix, \
                 [rx * cos(theta_1 + delta_theta), \
                  ry * sin(theta_1 + delta_theta)]) + [cx, cy]

    large_arc = fabs(delta_theta) > pi
    sweep = delta_theta > 0

    return x1, y1, x2, y2, rx, ry, phi, large_arc, sweep

def arcEndpointToCenter(x1, y1, x2, y2, rx, ry, phi, large_arc, sweep):
    # F.6.5 - Step 1
    cos_phi, sin_phi = cos(phi), sin(phi)
    rotation_matrix     = [[cos_phi,  sin_phi], [-sin_phi, cos_phi]]
    rotation_matrix_neg = [[cos_phi, -sin_phi], [ sin_phi, cos_phi]]
    x1p, y1p = dot(rotation_matrix, [(x1-x2)/2, (y1-y2)/2])

    # F.6.6 Correction of out-of-range radii
    assert (rx != 0 and ry != 0), \
        'Use a "line to" command instead of arc with zero x and y radii.'
    rx, ry = fabs(rx), fabs(ry)
    lambda_ = ((x1p ** 2) / (rx ** 2)) + ((y1p ** 2) / (ry ** 2))
    if lambda_ > 1:
        rx, ry = sqrt(lambda_) * array([rx, ry])

    # F.6.5 - Step 2
    radicand = (((rx * ry) ** 2) - ((rx * y1p) ** 2) - ((ry * x1p) ** 2)) / \
               (((rx * y1p) ** 2) + ((ry * x1p) ** 2))
    if radicand < 0:
        radicand = 0
    if large_arc == sweep:
        sign = -1
    else:
        sign = 1
    cxp, cyp = sign * sqrt(radicand) * array([rx * y1p / ry, -ry * x1p / rx])

    # F.6.5 - Step 3
    cx, cy = dot(rotation_matrix_neg, [cxp, cyp]) + \
             [(x1 + x2) / 2, (y1 + y2) / 2]

    # F.6.5 - Step 4
    theta_1 = angleBetween([1,0], [(x1p - cxp) / rx, (y1p - cyp) / ry])
    delta_theta = angleBetween([(x1p - cxp) / rx, (y1p - cyp) / ry], \
                               [(-x1p - cxp) / rx, (-y1p - cyp) / ry])
    if sweep == False and delta_theta > 0:
        delta_theta -= 2 * pi
    if sweep == True and delta_theta < 0:
        delta_theta += 2 * pi

    return cx, cy, rx, ry, phi, theta_1, delta_theta

def smallArc(theta, delta_theta):
    # Riškus 2006 - Section 3 (equation sets 8 and 9)
    # Note: Correction of sign in calculation of x3 and y3
    x1, y1 = cos(theta), sin(theta)
    x4, y4 = cos(theta + delta_theta), sin(theta + delta_theta)
    q1 = (x1 ** 2) + (y1 ** 2)
    q2 = q1 + (x1 * x4) + (y1 * y4)
    k2 = (4.0/3.0) * (sqrt(2 * q1 * q2) - q2) / (x1 * y4 - y1 * x4)
    x2 = x1 - k2 * y1
    y2 = y1 + k2 * x1
    x3 = x4 + k2 * y4
    y3 = y4 - k2 * x4
    return x1, y1, x2, y2, x3, y3, x4, y4

def scale(x, y, sx, sy):
    return x * sx, y * sy

def rotate(x, y, theta):
    cos_theta, sin_theta = cos(theta), sin(theta)
    rotation_matrix = [[cos_theta,  -sin_theta], [sin_theta, cos_theta]]
    xp, yp = dot(rotation_matrix, [x, y])
    return xp, yp

def translate(x, y, dx, dy):
    return x + dx, y + dy

def arcCenterToCubic(cx, cy, rx, ry, theta_1, delta_theta, x_axis_rotation=0):
    n_segments = 1
    while n_segments * pi / 2 < fabs(delta_theta):
        n_segments += 1
    small_arc_delta_theta = delta_theta / n_segments
    cubic = []
    theta = theta_1
    for _ in range(n_segments):
        small_arc = iter(smallArc(theta, small_arc_delta_theta))
        cubic.append([translate(*rotate(*scale(*xy, rx, ry), \
                                        x_axis_rotation), cx, cy) \
                      for xy in zip(small_arc, small_arc)])
        theta += small_arc_delta_theta
    return cubic

def arcEndpointToCubic(x0, y0, x3, y3, rx, ry, \
                       x_axis_rotation=0, large_arc=True, sweep=True):
    cx, cy, rx, ry, _, theta_1, delta_theta = \
        arcEndpointToCenter(x0, y0, x3, y3, rx, ry, \
                            x_axis_rotation, large_arc, sweep)
    cubic = arcCenterToCubic(cx, cy, rx, ry, theta_1, delta_theta, \
                             x_axis_rotation=x_axis_rotation)
    return cubic

def ellipseToCubic(cx, cy, rx, ry, x_axis_rotation=0):
    cubic = arcCenterToCubic(cx, cy, rx, ry, 0, 2 * pi, \
                             x_axis_rotation=x_axis_rotation)
    cubic[-1][-1] = cubic[0][0]
    return cubic

def circleToCubic(cx, cy, r):
    return ellipseToCubic(cx, cy, r, r)

if __name__ == '__main__':
    #print(arcEndpointToCubic(100,0,0,100,100,100,large_arc=True,sweep=True))
    #print(arcEndpointToCubic(100,0,0,100,100,100,large_arc=False,sweep=True))
    #print(arcEndpointToCubic(100,0,0,100,100,100,large_arc=True,sweep=False))
    #print(arcEndpointToCubic(100,0,0,100,100,100,large_arc=False,sweep=False))
    #print()
    #print(circleToCubic(0,0,100))
    print(arcEndpointToCubic(200, 200, 300, 300, 150, 300))
