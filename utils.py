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

def find_ranges(bitmap_block):
    ranges = []
    start = None
    
    for i, value in enumerate(bitmap_block):
        if value == 1:
            if start is None:
                start = i
        else:
            if start is not None:
                ranges.append((start, i - 1))
                start = None
                
    # Add the last range if it ends with 1s
    if start is not None:
        ranges.append((start, len(lst) - 1))
    
    return ranges