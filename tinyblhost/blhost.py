# -*- encoding: utf-8 -*-
#@File    :   blhost.py
#@Time    :   2025/01/08 11:30:26
#@Author  :   Jianping Zhang 
#@Version :   1.0
#@Contact :   Jianping.zhang_2@nxp.com
#@Brief   :   


import serial
import struct
import binascii
import tinyblhost.package as package
import tinyblhost.response as resp

class Blhost():
    def __init__(self, port='COM38', baudrate=115200):
        self.ser = serial.Serial(
            port='COM38',
            baudrate=115200,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            bytesize=serial.EIGHTBITS,
            timeout=1
        )    

    def deinit(self):
        self.ser.close()   

    def get_property(self, tag, index = 0):
        status, response_result = package.execute_command(self.ser, 0x07, 0x00, [tag, index], None, receive_data=False, expected_response = resp.GETPROPERTY_RESPONSE)
        return response_result[0], [response_result[i+1] for i in range(len(response_result)-1)]

    def read_memory(self, addr, byte_count, file, memory_id=0):
        status, response_result = package.execute_command(self.ser, 0x03, 0x00, [addr, byte_count, memory_id], None, receive_data=True, expected_response = resp.READMEMORY_RESPONSE)        
        return response_result[0], [response_result[i+1] for i in range(len(response_result)-1)]

    def write_memory(self, addr, file, memory_id=0):
        if isinstance(file, str):
            with open(file, "rb") as file_handler:
               file_data = file_handler.read() 
        elif isinstance(file, bytes):
            file_data = file
        else:
            print("Invalid parameters type")
            return
        
        byte_count = len(file_data)
        status, response_result = package.execute_command(self.ser, 0x04, 0x00, [addr, byte_count, memory_id], file_data, receive_data=False, expected_response = resp.GENERIC_RESPONSE)
        return response_result[0], [response_result[i+1] for i in range(len(response_result)-1)]