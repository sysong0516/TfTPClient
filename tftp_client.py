#!/usr/bin/python3
'''
$ tftp ip_address [-p port_mumber] <get|put> filename
'''
import socket
import argparse
import sys
# import validators
from struct import pack, unpack
import time
import os

DEFAULT_PORT = 69
BLOCK_SIZE = 512
DEFAULT_TRANSFER_MODE = 'octet'

OPCODE = {'RRQ': 1, 'WRQ': 2, 'DATA': 3, 'ACK': 4, 'ERROR': 5}
MODE = {'netascii': 1, 'octet': 2, 'mail': 3}

ERROR_CODE = {
    0: "Not defined, see error message (if any).",
    1: "File not found.",
    2: "Access violation.",
    3: "Disk full or allocation exceeded.",
    4: "Illegal TFTP operation.",
    5: "Unknown transfer ID.",
    6: "File already exists.",
    7: "No such user."
}
def send_wrq(filename, mode):
    global sock
    expected_block_number = 1
    format = f'>h{len(filename)}sB{len(mode)}sB'
    wrq_message = pack(format, OPCODE['WRQ'], bytes(filename, 'utf-8'), 0, bytes(mode, 'utf-8'), 0)
    try:
        sock.sendto(wrq_message,server_address)
        sock.settimeout(5)
        #wrq메시지에 대한 ack은 opcode 4와 block number 0을 포함한다
        wrq_res, wrq_ad=sock.recvfrom(4)
        opcode, block_number = unpack("!HH", wrq_res)
        print(opcode,block_number,wrq_ad)
    except sock.timeout:
        print('timeout')
        sys.exit(0)
    with open(filename, 'rb') as file:
        data_blocks = []
        while True:
            data_block = file.read(512)
            if not data_block:
                break
            data_blocks.append(data_block)
    try:
        for data_block in data_blocks:
            print(data_block)
            data_packet = pack(f'!HH{len(data_block)}s', OPCODE['DATA'], expected_block_number, data_block)
            sock.sendto(data_packet, wrq_ad)
            sock.settimeout(5)
            # ACK 대기
            response, ad = sock.recvfrom(4)
            opcode, block_number = unpack("!HH", response)
            print(f'{opcode}, {block_number}, {expected_block_number}')
            if opcode == OPCODE['ACK']and block_number == expected_block_number:
                print(f"ACK received for block {block_number}")
                expected_block_number += 1  # 다음 블록을 기대
            else:
                print("Unexpected response received. Expected ACK.")
                break  # 에러가 발생하면 루프 종료
    except socket.timeout:
        print("Timeout")
        sys.exit(0)
    print('전송완료')

def send_rrq(filename, mode):
    format = f'>h{len(filename)}sB{len(mode)}sB'
    rrq_message = pack(format, OPCODE['RRQ'], bytes(filename, 'utf-8'), 0, bytes(mode, 'utf-8'), 0)
    sock.sendto(rrq_message, server_address)
    print(rrq_message)
#put get 테스트
#put 데이터블록단위로 쪼개어 보낸후 블록단위로 Ack을 수신받아야함 settimeout(5)
#get 데이터블록 중복 오류제어 해야함 < sequence 넘버 확인 또는 ack 중복확인하면 될 듯

def send_ack(seq_num, server):
    format = f'>hh'
    ack_message = pack(format, OPCODE['ACK'], seq_num)
    sock.sendto(ack_message, server)
    print(seq_num)
    print(ack_message)


# parse command line arguments
parser = argparse.ArgumentParser(description='TFTP client program')
parser.add_argument(dest="host", help="Server IP address", type=str)
parser.add_argument(dest="operation", help="get or put a file", type=str)
parser.add_argument(dest="filename", help="name of file to transfer", type=str)
parser.add_argument("-p", "--port", dest="port", type=int)
args = parser.parse_args()

'''
if validators.domain(args.host):
    serber_ip = gethostbyname(args.host) 
else
    server_ip = args.host


if args.port == None:
    server_port = DEFAULT_PORT
'''

# Create a UDP socket
server_ip = args.host
server_port = DEFAULT_PORT
server_address = (server_ip, server_port)
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

mode = DEFAULT_TRANSFER_MODE
operation = args.operation
filename = args.filename
port = args.port
if port:
    print('{}번 포트 접속'.format(port))

# Send RRQ_message
if operation == 'get':
    send_rrq(filename, mode)
    # Open a file with the same name to save data  from server
    file = open(filename, 'wb')
    expected_block_number = 1
    pre_block=0
    while True:
        # receive data from the server
        # server uses a newly assigned port(not 69)to transfer data
        # so ACK should be sent to the new socket
        data, server_new_socket = sock.recvfrom(516)
        opcode = int.from_bytes(data[:2], 'big')

        # check message type
        if opcode == OPCODE['DATA']:
            block_number = int.from_bytes(data[2:4], 'big')
            if block_number==pre_block:
                print('중복된 데이터블록')
                send_ack(block_number, server_new_socket)
                continue
            print(block_number)
            if block_number == expected_block_number:
                send_ack(block_number, server_new_socket)
                file_block = data[4:]
                file.write(file_block)
                expected_block_number = expected_block_number + 1
                print(file_block.decode())
                pre_block=block_number
            else:
                send_ack(block_number, server_new_socket)

        elif opcode == OPCODE['ERROR']:
            error_code = int.from_bytes(data[2:4], byteorder='big')
            print(ERROR_CODE[error_code])
            if error_code == 0x01:
                print('존재하지 않는 파일입니다')
            break

        else:
            break

        if len(file_block) < BLOCK_SIZE:
            file.close()
            print(len(file_block))
            break
elif operation == 'put':
    send_wrq(filename, mode)
