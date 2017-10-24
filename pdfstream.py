# -*- coding: utf-8 -*-
# Author: Umesh Mohan (umesh@heterorrhina.in)
# From PDF 1.7 file format specification

from ._misc import raiseValueError, raiseNotImplementedError,\
                  isWithinLimits
from .arc2cubic import arcCenterToCubic, arcEndpointToCubic, \
                      ellipseToCubic, circleToCubic, custom_path_operator
import math


def _setColorNamedToString(x):
    if type(x[-1]) is str:
        string_ = ' '.join(['{:.4f}'.format(i) for i in x[:-1]]) +  ' ' + x[-1]
        n_color = len(x) - 1
    else:
        string_ = ' '.join(['{:.4f}'.format(i) for i in x])
        n_color = len(x)
    return string_, n_color

general_graphics_state_operators = ['w', 'J', 'j', 'M', 'd', 'ri', 'i', 'gs']
special_graphics_state_operators = ['q', 'Q', 'cm']
path_construction_operators = ['m', 'l', 'c', 'v', 'y', 'h', 're']
path_painting_operators = ['S', 's', 'f', 'F', 'f*', 'B', 'B*', 'b', 'b*', 'n']
clipping_paths_operators = ['W', 'W*']
text_objects_operators = ['BT', 'ET']
text_state_operators = ['Tc', 'Tw', 'Tz', 'TL', 'Tf', 'Tr', 'Ts']
text_positioning_operators = ['Td', 'TD', 'Tm', 'T*']
text_showing_operators = ['Tj', 'TJ', '\'', '\"']
type_3_fonts_operators = ['d0', 'd1']
color_operators = ['CS', 'cs', 'SC', 'SCN', 'sc', 'scn', \
                   'G', 'g', 'RG', 'rg', 'K', 'k']
shading_patterns_operators = ['sh']
inline_images_operators = ['BI', 'ID', 'EI']
xobjects_operators = ['Do']
marked_content_operators = ['MP', 'DP', 'BMC', 'BDC', 'EMC']
compatibility_operators = ['BX', 'EX']

pdf_operator_state = {
    'PageDescriptionLevel': {
        'start': [],
        'end': {'BT': 'TextObject',
                'sh': 'ShadingObject',
                'Do': 'ExternalObject',
                'BI': 'InLineImageObject',
                'm' : 'PathObject',
                're': 'PathObject'},
        'allowed': general_graphics_state_operators +
                   special_graphics_state_operators +
                   color_operators +
                   text_state_operators +
                   marked_content_operators +
                   xobjects_operators
    },
    'TextObject': {
        'start': ['BT'],
        'end': {'ET': 'PageDescriptionLevel'},
        'allowed': general_graphics_state_operators +
                   color_operators +
                   text_state_operators +
                   text_showing_operators +
                   text_positioning_operators +
                   marked_content_operators
    },
    'ShadingObject': {
        'start': ['sh'],
        'end': {None: None},
        'allowed': []
    },
    'ExternalObject': {
        'start': ['Do'],
        'end': {None: None},
        'allowed': []
    },
    'InLineImageObject': {
        'start': ['BI'],
        'end': {'EI': 'PageDescriptionLevel'},
        'allowed': ['ID']
    },
    'PathObject': {
        'start': ['m', 're'],
        'end': dict({operator: 'PageDescriptionLevel' \
                        for operator in path_painting_operators},
                    **{'W': 'clipping_paths_operators',
                       'W*': 'clipping_paths_operators'}),
        'allowed': path_construction_operators
    },
    'ClippingPathObject': {
        'start': ['W', 'W*'],
        'end': {operator: 'PageDescriptionLevel' \
                    for operator in path_painting_operators},
        'allowed': []
    }
}

pdf_operator = {
    # General graphics state
    'w'  : lambda line_width: '{:.4f} w'.format(line_width),
    'J'  : lambda line_cap: '{:d} J'.format(line_cap) \
                            if line_cap in [0,1,2] else \
                            raiseValueError('"line cap"', line_cap),
    'j'  : lambda line_join: '{:d} j'.format(line_join) \
                             if line_join in [0,1,2] else \
                             raiseValueError('"line join"', line_join),
    'M'  : lambda miter_limit: '{:.4f} M'.format(miter_limit),
    'd'  : lambda dash_array, dash_phase: '[' + ' '.join(['{:.4f}'.format(i) \
                                          for i in dash_array]) + \
                                          '] {:.4f} d'.format(dash_phase),
    'ri' : lambda intent: intent + ' ri' if intent in \
                          ['AbsoluteColorimetric', 'RelativeColorimetric', \
                           'Saturation', 'Perceptual'] \
                          else raiseValueError('"rendering intent"', intent),
    'i'  : lambda flatness: '{:d} i'.format(flatness) \
                            if flatness in range(101) else \
                            raiseValueError('"flatness"', flatness),
    'gs' : lambda graphics_state_parameter_dictionary: \
                graphics_state_parameter_dictionary + ' gs',
    # Special graphics state
    'q'  : lambda : 'q',
    'Q'  : lambda : 'Q',
    'cm' : lambda a, b, c, d, e, f: \
                (('{:.4f} ' * 6) + 'cm').format(a, b, c, d, e, f),
    # Path construction
    'm'  : lambda x, y: '{:.4f} {:.4f} m'.format(x, y),
    'l'  : lambda x, y: '{:.4f} {:.4f} l'.format(x, y),
    'c'  : lambda x1, y1, x2, y2, x3, y3: \
                (('{:.4f} ' * 6) + 'c').format(x1, y1, x2, y2, x3, y3),
    'v'  : lambda x2, y2, x3, y3: (('{:.4f} ' * 4)+'v').format(x2, y2, x3, y3),
    'y'  : lambda x1, y1, x3, y3: (('{:.4f} ' * 4)+'y').format(x1, y1, x3, y3),
    'h'  : lambda : 'h',
    're' : lambda x, y, width, height: \
                (('{:.4f} ' * 4) + 're').format(x, y, width, height),
    # Path painting
    'S'  : lambda : 'S',
    's'  : lambda : 's',
    'f'  : lambda : 'f',
    'F'  : lambda : 'F',
    'f*' : lambda : 'f*',
    'B'  : lambda : 'B',
    'B*' : lambda : 'B*',
    'b'  : lambda : 'b',
    'b*' : lambda : 'b*',
    'n'  : lambda : 'n',
    # Clipping paths
    'W'  : lambda : 'W',
    'W*' : lambda : 'W*',
    # Text objects
    'BT' : lambda : 'BT',
    'ET' : lambda : 'ET',
    # Text state
    'Tc' : lambda char_space: '{:.4f} Tc'.format(char_space),
    'Tw' : lambda word_space: '{:.4f} Tw'.format(word_space),
    'Tz' : lambda scale: '{:.4f} Tz'.format(scale),
    'TL' : lambda leading: '{:.4f} TL'.format(leading),
    'Tf' : lambda font_name, font_size: font_name + ' {:.4f} Tf'.format(font_size),
    'Tr' : lambda text_rendering_mode: '{:d} Tr'.format(text_rendering_mode) \
                                       if text_rendering_mode in range(8) else\
                                       raiseValueError('"text rendering mode"',
                                                       text_rendering_mode),
    'Ts' : lambda rise: '{:.4f} Ts'.format(rise),
    # Text positioning
    'Td' : lambda tx, ty: '{:.4f} {:.4f} Td'.format(tx, ty),
    'TD' : lambda tx, ty: '{:.4f} {:.4f} TD'.format(tx, ty),
    'Tm' : lambda a, b, c, d, e, f: \
                (('{:.4f} ' * 6) + 'Tm').format(a, b, c, d, e, f),
    'T*' : lambda : 'T*',
    # Text showing
    'Tj' : lambda string_: '(' + string_ + ') Tj',
    'TJ' : lambda array_: '[' + ' '.join(['(' + i + ')' if type(i) is str else\
                          '{:.2f}'.format(i) for i in array_]) + '] TJ',
    "'"  : lambda string_: string_ + ' \'',
    '"'  : lambda word_space, char_space, string_: \
                '{:.4f} {:.4f} '.format(word_space, char_space) + string_+' "',
    # Type 3 fonts
    'd0' : lambda horizontal_displacement: \
                '{:.4f} 0 d0'.format(horizontal_displacement),
    'd1' : lambda horizontal_displacement, \
                  lower_left_x, lower_left_y, \
                  upper_right_x, upper_right_y: \
                '{:.4f} 0 {:.4f} {:.4f} {:.4f} d0'\
                .format(horizontal_displacement, \
                lower_left_x, lower_left_y, upper_right_x, upper_right_y),
    # Color
    'CS' : lambda color_space: color_space + ' CS' if color_space in \
                               ['/DeviceGray', '/DeviceRGB', '/DeviceCMYK', \
                                '/Pattern'] else \
                               raiseNotImplementedError('color space: ' + \
                                                       color_space+' in "CS"'),
    'cs' : lambda color_space: color_space + ' cs' if color_space in \
                               ['/DeviceGray', '/DeviceRGB', '/DeviceCMYK', \
                                '/Pattern'] else \
                               raiseNotImplementedError('color space: ' + \
                                                       color_space+' in "cs"'),
    'SC' : lambda *x: ' '.join(['{:.4f}'.format(i) for i in x]) + ' SC' \
                      if len(x) in [1,3,4] else raiseValueError('"SC"', x),
    'SCN': lambda *x: _setColorNamedToString(x)[0] + ' SCN' \
                      if _setColorNamedToString(x)[1] in [1, 3, 4] else \
                      raiseValueError('"SCN"', x),
    'sc' : lambda *x: ' '.join(['{:.4f}'.format(i) for i in x]) + ' sc' \
                      if len(x) in [1,3,4] else raiseValueError('"sc"', x),
    'scn': lambda *x: _setColorNamedToString(x)[0] + ' scn' \
                      if _setColorNamedToString(x)[1] in [1, 3, 4] else \
                      raiseValueError('"scn"', x),
    'G'  : lambda gray: '{:.4f} G'.format(gray) \
                        if isWithinLimits(gray) else \
                        raiseValueError('gray', gray),
    'g'  : lambda gray: '{:.4f} g'.format(gray) \
                        if isWithinLimits(gray) else \
                        raiseValueError('gray', gray),
    'RG' : lambda r, g, b: '{:.4f} {:.4f} {:.4f} RG'.format(r, g, b) \
                           if isWithinLimits([r, g, b]) else \
                           raiseValueError('RGB', [r, g, b]),
    'rg' : lambda r, g, b: '{:.4f} {:.4f} {:.4f} rg'.format(r, g, b) \
                           if isWithinLimits([r, g, b]) else \
                           raiseValueError('RGB', [r, g, b]),
    'K'  : lambda c, m, y, k: '{:.4f} {:.4f} {:.4f} {:.4f} K'.format(c,m,y,k) \
                              if isWithinLimits([c, m, y, k]) else \
                              raiseValueError('CMYK', [c, m, y, k]),
    'k'  : lambda c, m, y, k: '{:.4f} {:.4f} {:.4f} {:.4f} k'.format(c,m,y,k) \
                              if isWithinLimits([c, m, y, k]) else \
                              raiseValueError('CMYK', [c, m, y, k]),
    # Shading patterns
    'sh' : lambda name: name + ' sh',
    # Inline images
    'BI' : lambda : 'BI',
    'ID' : lambda : 'ID',
    'EI' : lambda : 'EI',
    # XObjects
    'Do' : lambda name: name + ' Do',
    # Marked content
    'MP' : lambda tag: tag + ' MP',
    'DP' : lambda tag, properties: tag + ' ' + str(properties) + ' DP',
    'BMC': lambda tag: tag + ' BMC',
    'BDC': lambda tag, properties: tag + ' ' + str(properties) + ' BDC',
    'EMC': lambda : 'EMC',
    # Compatibility
    'BX' : lambda : 'BX',
    'EX' : lambda : 'EX'
}

class PdfStream:

    def __init__(self):
        self.current_state = 'PageDescriptionLevel'
        self.content = []
        self.commands = []
        self.last_point = None

    def isOperatorAllowed(self, operator):
        all_allowed_operators = pdf_operator_state[self.current_state]\
                                    ['allowed'] + \
                                list(pdf_operator_state[self.current_state]\
                                     ['end'].keys())
        return operator in all_allowed_operators

    def append(self, operator, *operator_parameters):
        if operator not in pdf_operator.keys():
            raise ValueError('Illegal PDF operator: ' + str(operator))
        if self.isOperatorAllowed(operator):
            self.content.append(pdf_operator[operator](*operator_parameters))
            new_state = self.current_state
            if operator in pdf_operator_state[self.current_state]['end'].keys():
                new_state = pdf_operator_state[self.current_state]['end'][operator]
                if None in pdf_operator_state[new_state]['end'].keys():
                    new_state = self.current_state
            self.current_state = new_state
            if new_state == 'PathObject':
                self.last_point = operator_parameters[-2:]
            else:
                self.last_point = None
        else:
            raise ValueError('The PDF operator ' + operator + \
                             ' is not allowed here.')
        self.commands.append([operator, operator_parameters])

    def appendCustomPath(self, path_type, *path_parameters, **path_kwargs):
        '''path_type should be one of ['Arc', 'ArcCenter', 'Ellipse', 'Circle']
path_parameters and path_kwargs for:
Arc : x0, y0, x3, y3, rx, ry, x_axis_rotation=0, large_arc=True, sweep=True
ArcCenter: cx, cy, rx, ry, theta_1, delta_theta, x_axis_rotation=0
Ellipse: cx, cy, rx, ry, x_axis_rotation=0
Circle: cx, cy, r'''
        if path_type in custom_path_operator.keys():
            assert (self.current_state in \
                custom_path_operator[path_type]['allowed']), \
                'Custom path of type "' + path_type + \
                '" is not allowed in the current state: ' + self.current_state
            if custom_path_operator[path_type]['send_last_point_to_function']:
                path_parameters = *self.last_point, *path_parameters
            cubic = custom_path_operator[path_type]\
                    ['to_cubic_function'](*path_parameters, **path_kwargs)
            self.commands.append([path_type + ':Start', \
                                  path_parameters, path_kwargs])
            if custom_path_operator[path_type]['prepend_move_to']:
                self.append('m', *cubic[0][0])
            for cubic_segment in cubic:
                self.append('c', *cubic_segment[1], *cubic_segment[2], \
                            *cubic_segment[3],)
            self.commands.append([path_type + ':End'])
        else:
            raise NotImplementedError('PDF custom path of type: ' + \
                                      path_type + ' is not implemented')

    def __repr__(self):
        return self.commands.__repr__()

    def __str__(self):
        #return '\n'.join([' '.join([nums.strip('0') for nums in contentlet.split(' ')]) for contentlet in self.content])
        #return_string = '\n'.join(self.content)
        return '\n'.join(self.content)

    def append_multiple_operations(self, operations):
        assert (type(operations) is list)
        for stream_command in operations:
            if type(stream_command) is str:
                stream_command = (stream_command, [])
            elif type(stream_command) is tuple:
                if len(stream_command) == 1:
                    stream_command = (stream_command[0], [])
                if len(stream_command) > 2:
                    stream_command = (stream_command[0], [*stream_command[1:]])
                if type(stream_command[1]) is not list:
                    stream_command = (stream_command[0], [stream_command[1]])
            operation_type, operation_parameters = stream_command
            if type(operation_parameters) is not list:
                operation_parameters = [operation_parameters]
            if operation_type in custom_path_operator:  # ['Arc', 'ArcCenter', 'Ellipse', 'Circle']:
                self.appendCustomPath(operation_type, *operation_parameters)
            else:
                self.append(operation_type, *operation_parameters)
