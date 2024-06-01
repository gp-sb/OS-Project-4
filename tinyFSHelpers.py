from libDisk import *
from tinyFSObjects import *

def write_superblock(tfs):
    return write_block(tfs.disk, 0, make_256_bytes(tfs.sb.toBytes()))

def flip_free_block_bit(tfs, block_number):
    old_bit_vlaue = get_block_bitmap(tfs)[block_number] 
    new_bit_value = 0 if old_bit_vlaue == 1 else 1
    tfs.sb.free_block_bitmap[block_number] = new_bit_value
    write_superblock(tfs)

def has_superblock(disk):
    data = bytearray(256)
    read_block(disk, 0, data)
    return data[:4] == b"0x5a"
    
def get_block_bitmap(tfs):
    data = bytearray(256)
    read_block(tfs.disk, 0, data)
    return data[BITMAP_OFFSET: (BITMAP_OFFSET+tfs.sb.number_of_blocks)]

def allocate_block(tfs):
    bitmap = get_block_bitmap(tfs)
    for i in range(len(bitmap)):
        if bitmap[i] == 0:
            bitmap[i] = 1
            return DISK_OK
    return DISK_ERROR

def make_256_bytes(data):
    if len(data) < 256:
        return data + bytes(256 - len(data))
    return data