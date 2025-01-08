# -*- encoding: utf-8 -*-
#@File    :   response.py
#@Time    :   2025/01/08 10:37:11
#@Author  :   Jianping Zhang 
#@Version :   1.0
#@Contact :   Jianping.zhang_2@nxp.com
#@Brief   :   
   

import serial
import struct

GENERIC_RESPONSE = 0xA0
GETPROPERTY_RESPONSE = 0xA7
READMEMORY_RESPONSE = 0xA3

class GenericResponse():
    @staticmethod
    def parse(payload):
        tag, flags, rsvd, param_count  = struct.unpack('<BBBB', payload[:4])
        return struct.unpack('<II', payload[4:12]) #result == (status code, command tag)

class GetPropertyResponse():
    @staticmethod
    def parse(payload):
        tag, flags, rsvd, param_count  = struct.unpack('<BBBB', payload[:4])
        return struct.unpack(f'{param_count}I', payload[4: 4+4*param_count]) #result == (status code, Property code, ...)

class ReadMemoryResponse():
    @staticmethod
    def parse(payload):
        tag, flags, rsvd, param_count  = struct.unpack('<BBBB', payload[:4])
        return struct.unpack(f'{param_count}I', payload[4: 4+4*param_count]) #result == (status code, Property code, ...)
        

def response_factoy(response_type):
    if response_type == GENERIC_RESPONSE:
        return GenericResponse()
    elif response_type == GETPROPERTY_RESPONSE:
        return GetPropertyResponse()
    elif response_type == READMEMORY_RESPONSE:
        return ReadMemoryResponse()
    else:
        return None