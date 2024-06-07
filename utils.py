# utils.py

from libDisk import BLOCKSIZE



def to_bytes(data, data_size):
    return data.to_bytes(data_size, byteorder='big')

def read_int_bytes(data, offset, size):
    return int.from_bytes(data[offset: offset + size], byteorder="big")

# Makes data's size block size, if smaller. Leaves data unchanged if larger
def make_blocksize(data):
    if len(data) < BLOCKSIZE:
        return data + bytes(BLOCKSIZE - len(data))
    return data[:BLOCKSIZE]
