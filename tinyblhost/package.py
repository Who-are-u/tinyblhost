# -*- encoding: utf-8 -*-
#@File    :   package.py
#@Time    :   2025/01/07 09:58:49
#@Author  :   Jianping Zhang 
#@Version :   1.0
#@Contact :   Jianping.zhang_2@nxp.com
#@Brief   :   

import serial
import struct
import binascii
import crcmod.predefined
import tinyblhost.response as resp

# 定义包类型常量
PING_PACKET_TYPE = 0xA6
PING_RESPONSE_PACKET_TYPE = 0xA7
COMMAND_PACKET_TYPE = 0xA4
DATA_PACKET_TYPE = 0xA5
QUERY_MAX_DATA_LENGTH_CMD = 0x0B  # 查询最大数据长度命令

RESPONSE_PACKET_TYPE_ACK = 0xA1
RESPONSE_PACKET_TYPE_NACK = 0xA2
RESPONSE_PACKET_TYPE_ABORT = 0xA3

def calculate_crc16(data: bytearray):
    crc16_xmodem = crcmod.predefined.mkPredefinedCrcFun('xmodem')
    crc16_xmodem_checksum = crc16_xmodem(bytes(data))
    return crc16_xmodem_checksum

def create_frame_packet(packet_type, payload):
    """创建帧包"""
    start_byte = 0x5A
    payload_size = len(payload)
    packet_header = struct.pack('<BBH', start_byte, packet_type, payload_size)
    crc_data = packet_header + payload
    crc = calculate_crc16(crc_data)
    crc_bytes = struct.pack('<H', crc)
    frame_packet = packet_header + crc_bytes + payload
    return frame_packet

def create_special_frame_packet(packet_type):
    """创建帧包"""
    start_byte = 0x5A
    frame_packet = struct.pack('<BB', start_byte, packet_type)
    return frame_packet

def create_command_packet(tag, flags, params):
    """创建命令包"""
    command_header = struct.pack('<BBBB', tag, flags, 0, len(params))
    params_bytes = b''
    for param in params:
        params_bytes += struct.pack('<I', param)
    command_packet = command_header + params_bytes
    return command_packet

def send_packet(ser, packet):
    """通过串行端口发送包"""
    ser.write(packet)
    print("Packet >>:", binascii.hexlify(packet))

def response_packet(ser, expected_response=None):
    """接收并处理包，根据预期的包类型和标签进行处理"""
    framing_header = ser.read(2)
    payload_data = b''
    result = ()
    status = False
    if framing_header and framing_header[0] == 0x5A:
        packet_type = framing_header[1]
        if packet_type in [COMMAND_PACKET_TYPE, DATA_PACKET_TYPE]:
            """ response packet(command packet) or data packet, embeded in the frame packet.
            """
            payload_size = struct.unpack('<H', ser.read(2))[0]
            crc_bytes = ser.read(2)
            crc = struct.unpack('<H', crc_bytes)[0]
            payload_data = ser.read(payload_size)

            if calculate_crc16(framing_header + struct.pack('<H', payload_size) + payload_data) == crc:
                if packet_type == COMMAND_PACKET_TYPE:
                    tag, flags, rsvd, param_count  = struct.unpack('<BBBB', payload_data[:4])
                    if expected_response and tag == expected_response:
                        response = resp.response_factoy(tag)
                        if response != None:
                            result = response.parse(payload_data) 
                            status = True
                        else:
                            print(f"does not support {tag}")
                    else:
                        print(f"Invalid Tag: {tag} != {expected_response}")
                elif packet_type == DATA_PACKET_TYPE:
                    print("Received Data Packet with Data:", payload_data)
                    result = (payload_data)
                    status = True
            else:
                print("CRC mismatch in received data.")
        else:
            print("Invalid packet")
    else:
        print("Invalid framing header or start byte.")

    return status, result

def response_ping_packet(ser):
    """接收并处理包，根据预期的包类型和标签进行处理"""
    status = False
    result = ()
    try:
        framing_header = ser.read(2)
        packet = bytearray()
        if framing_header and framing_header[0] == 0x5A:
            packet_type = framing_header[1]
            if packet_type == PING_RESPONSE_PACKET_TYPE:
                payload_data  = ser.read(6)
                crc_data  = ser.read(2)
                crc = struct.unpack_from("<H", crc_data)[0]  
                if calculate_crc16(framing_header + payload_data) == crc:
                    result = struct.unpack_from("<BBBBBB", payload_data)  
                    status = True
                else:
                    print("CRC mismatch in received data.")
                packet = framing_header + payload_data + crc_data
            else:
                print("Invalid ping response packet")
        else:
            print("Invalid framing header or start byte.")
    except Exception as e:
        raise ValueError("timeout")
    else:
        print("Packet <<:", binascii.hexlify(packet))

    return status, result

def response_special_frame_packet(ser):
    """接收并处理包，根据预期的包类型和标签进行处理"""
    status = False
    result = ()
    try:
        framing_header = ser.read(2)
        packet = bytearray()
        if framing_header and framing_header[0] == 0x5A:
            packet_type = framing_header[1]
            if packet_type in [0xA1, 0xA2, 0xA3]:   
                result = (packet_type)
                status  = True
            else:
                print(f"Invalid packet type {packet_type : #04x}")
            packet = framing_header
        else:
            print("Invalid framing header or start byte.")
    except Exception as e:
        raise ValueError("timeout")
    else:
        print("Packet <<:", binascii.hexlify(packet))

    return status, result

def execute_command(ser, tag, flags, params, data_to_send=None, receive_data=False, expected_response=resp.GENERIC_RESPONSE):
    """
    执行命令，包括 Ping 阶段、命令阶段以及可选的数据发送和接收阶段。
    """
    status_code = -1
    response_data = []

    # Send ping package and wait for ping response package.
    ping_packet = struct.pack('<BB', 0x5A, PING_PACKET_TYPE)
    send_packet(ser, ping_packet)
    status, result = response_ping_packet(ser)
    if not status:
        reponse_packet = create_special_frame_packet(RESPONSE_PACKET_TYPE_ACK)
        send_packet(ser, reponse_packet)
    else:
        # Parse Ping package if necessary.
        pass
    
    # If the command, such as write-memory, which has data phase, query the supported maxium package size firstly
    if data_to_send is not None:
        command_packet = create_command_packet(0x07, 0x00, [0xb, 0x00])
        frame_packet = create_frame_packet(COMMAND_PACKET_TYPE, command_packet)
        send_packet(ser, frame_packet)

        try:
            response_special_frame_packet(ser)  
            status, result = response_packet(ser, expected_response=resp.GETPROPERTY_RESPONSE)
        except Exception as e: 
            max_data_length = 512  
            print(e)
        else:
            max_data_length = result[1]
        finally:
            reponse_packet = create_special_frame_packet(RESPONSE_PACKET_TYPE_ACK)
            send_packet(ser, reponse_packet)
    
    # The command phase, send command
    command_packet = create_command_packet(tag, flags, params)
    frame_packet = create_frame_packet(COMMAND_PACKET_TYPE, command_packet)
    send_packet(ser, frame_packet)

    try:
        response_special_frame_packet(ser) 
        status, response_result = response_packet(ser, expected_response=expected_response)
    except Exception as e:
        print(e)
    else:
        status_code = response_result[0]
        response_data = [response_result[i+1] for i in range(len(response_result)-1)]     
    finally:
        reponse_packet = create_special_frame_packet(RESPONSE_PACKET_TYPE_ACK)
        send_packet(ser, reponse_packet)    

    # The data phase(send).
    if data_to_send is not None:
        for i in range(0, (len(data_to_send) + max_data_length - 1)//max_data_length, 1):
            if i == len(data_to_send)//max_data_length:
                package_len = len(data_to_send)%max_data_length
            else:
                package_len = max_data_length
            chunk = data_to_send[i*max_data_length:i*max_data_length + package_len]
            data_frame_packet = create_frame_packet(DATA_PACKET_TYPE, chunk)
            send_packet(ser, data_frame_packet)
            
            status, result = response_special_frame_packet(ser)
            if status and result !=0xA1:
                print("Abort transfer.")
                break
    
        try:
            status, response_result = response_packet(ser, expected_response=resp.GENERIC_RESPONSE)
        except Exception as e:
            print(e)
        else:
            status_code = response_result[0]
            response_data = [response_result[i+1] for i in range(len(response_result)-1)]    
        finally:
            reponse_packet = create_special_frame_packet(RESPONSE_PACKET_TYPE_ACK)
            send_packet(ser, reponse_packet) 


    # The data phase(receive)
    if receive_data:
        data_len = 0
        data_bytes = b''
        while True:
            try:
                status, receive_data = response_packet(ser)
            except Exception as e:
                print(e)
            else:
                data_len = data_len + len(receive_data)
                data_bytes = data_bytes + receive_data
            finally:
                reponse_packet = create_special_frame_packet(RESPONSE_PACKET_TYPE_ACK)
                send_packet(ser, reponse_packet)
                if data_len >= params[1]:
                    break

        try:  
            status, _ = response_packet(ser, expected_response=resp.GENERIC_RESPONSE)
        except Exception as e:
            print(e)
        else:
            response_data.append(data_bytes)
        finally:
            reponse_packet = create_special_frame_packet(RESPONSE_PACKET_TYPE_ACK)
            send_packet(ser, reponse_packet)

    return status_code, response_data
