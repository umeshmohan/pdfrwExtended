# -*- coding: utf-8 -*-
# Author: Umesh Mohan (umesh@heterorrhina.in)

from collections import namedtuple
from numpy import matmul
from math import sin, cos, tan

import pdfrw

def mm2pt(mm):
    return (mm / 25.4) * 72

def pt2mm(pt):
    return (pt / 72) * 25.4

def raiseValueError(item, value_):
    raise ValueError('Unknown value for ' + str(item) + ': ' + str(value_))

def raiseNotImplementedError(item):
    raise NotImplementedError(str(item) + ' is not implemented')

def isWithinLimits(values, lower_limit=0, upper_limit=1, \
                   include_lower_limit=True, include_upper_limit=True):
    if type(values) is not list:
        values = [values]
    for value in values:
        if include_lower_limit:
            if value<lower_limit:
                return False
        else:
            if value<=lower_limit:
                return False
        if include_upper_limit:
            if value>upper_limit:
                return False
        else:
            if value>=upper_limit:
                return False
    return True

PDFTransformationMatrix = namedtuple('PDFTransformationMatrix', 'a b c d e f')

def newTM(a=1, b=0, c=0, d=1, e=0, f=0):
    return PDFTransformationMatrix(a,b,c,d,e,f)

class PdfTM:
    '''PDF transformation matrix
From PDF 1.7 file format specification section 4.2.2 and 4.2.3'''
    def __init__(self, *tm):
        '''pdf_tm = PdfTM()
pdf_tm = PdfTM(a,b,c,d,e,f)'''
        if len(tm) == 0:
            self.tm = PDFTransformationMatrix(1,0,0,1,0,0)
        else:
            assert len(tm) == 6, \
                'Transformation Matrix needs six parameters. Got '+ str(len(tm))
            self.tm = PDFTransformationMatrix(*tm)
    def translate(self, tx, ty):
        translate_matrix = PdfTM(*newTM(e=tx, f=ty))
        self.tm = (self * translate_matrix).tm
        return self
    def scale(self, sx, sy):
        scale_matrix = PdfTM(*newTM(a=sx, d=sy))
        self.tm = (self * scale_matrix).tm
        return self
    def rotate(self, theta, x0=0, y0=0):
        self.translate(x0, y0)
        rotate_matrix = PdfTM(*newTM(a=cos(theta), b=sin(theta), \
                                   c=-sin(theta), d=cos(theta)))
        self.tm = (self * rotate_matrix).tm
        self.translate(-x0, -y0)
        return self
    def skew(self, alpha, beta):
        '''Skew x axis by alpha and y axis by beta'''
        skew_matrix - PdfTM(*newTM(b=tan(alpha), c=tan(beta)))
        self.tm = (self * skew_matrix).tm
        return self
    def __repr__(self):
        return self.__str__()
    def __str__(self):
        return ' '.join(['{:.4f}'.format(i) for i in self.tm])
    def __mul__(mL, mR):
        mR_array = [[mR.tm.a, mR.tm.b, 0],\
                    [mR.tm.c, mR.tm.d, 0],\
                    [mR.tm.e, mR.tm.f, 1]]
        mL_array = [[mL.tm.a, mL.tm.b, 0],\
                    [mL.tm.c, mL.tm.d, 0],\
                    [mL.tm.e, mL.tm.f, 1]]
        [[a,b,g],[c,d,h],[e,f,i]] = matmul(mL_array, mR_array)
        assert g==0 and h==0 and i==1, 'mL: ' + str(mL) + '\nm0: ' + str(mR) + \
                                       '\ng=' + str(g) + ', h=' + str(g) + \
                                       ', i=' + str(g)
        return PdfTM(a,b,c,d,e,f)

def newPdfPage(size=[0, 0,  mm2pt(210), mm2pt(297)]):
    page = pdfrw.PdfDict()
    page.Type = '/Page'
    page.MediaBox = size
    return page
