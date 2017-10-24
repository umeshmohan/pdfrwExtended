# -*- coding: utf-8 -*-
'''
pdfxobject

Description: 

@author: Umesh Mohan (moh@nume.sh) 
'''

import pdfrw
from .pdfstream import PdfStream


class PdfXObjectForm(pdfrw.PdfDict):
    def __init__(self, *args,
                 b_box=[-100, -100, 100, 100],
                 matrix=[1, 0, 0, 1, 0, 0],
                 stream_commands=[],
                 resources={},
                 name=None,
                 **kwargs):
        super(PdfXObjectForm, self).__init__(*args, **kwargs)
        self.Type = pdfrw.PdfName('XObject')
        self.Subtype = pdfrw.PdfName('Form')
        self.BBox = b_box
        if matrix != [1, 0, 0, 1, 0, 0]:
            self.Matrix = matrix
        self.private.stream_commands = []
        self.update_stream(stream_commands)
        if len(resources.items()) > 0:
            self.Resources = pdfrw.PdfDict()
            for resource_type, resource_dict in resources.items():
                self.Resources[pdfrw.PdfName(resource_type)] = pdfrw.PdfDict()
                for resource_name, resource_ref in resource_dict.items():
                    self.Resources[pdfrw.PdfName(resource_type)][pdfrw.PdfName(resource_name)] = resource_ref
        if name is not None:
            self.Name = pdfrw.PdfName(name)

    def update_stream(self, stream_commands):
        for stream_command in stream_commands:
            if type(stream_command) is str:
                stream_command = (stream_command, [])
            elif type(stream_command) is tuple:
                if len(stream_command) == 1:
                    stream_command = (stream_command[0], [])
                if len(stream_command) > 2:
                    stream_command = (stream_command[0], [*stream_command[1:]])
                if type(stream_command[1]) is not list:
                    stream_command = (stream_command[0], [stream_command[1]])
            self.stream_commands.append(stream_command)
        stream = PdfStream()
        stream.append_multiple_operations(self.stream_commands)
        self.stream = str(stream)