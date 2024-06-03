from libDisk import *
from superblock import *

# Flips the bit at the given block number in the free block bitmap, returns if successful
def flip_free_block_bit(tfs, block_number):
    data = bytearray(BLOCKSIZE)
    read_block(tfs.disk, 0, data)
    old_bit_vlaue = data[BITMAP_OFFSET + block_number]
    new_bit_value = 0 if old_bit_vlaue == 1 else 1
    data[BITMAP_OFFSET + block_number] = new_bit_value
    return write_block(tfs.disk, 0, data)

# Returns if a disk has a superblock
def has_superblock(disk):
    data = bytearray(BLOCKSIZE)
    read_block(disk, 0, data)
    return data[:4] == MAGIC_NUMBER

# Returns the block number of the first free block, and updates free block bitmap
def allocate_block(disk):
    data = bytearray(BLOCKSIZE)
    read_block(disk, 0, data)
    for i in range(BITMAP_OFFSET, (BITMAP_OFFSET+NUMBER_OF_BLOCKS)):
        if data[i] == 0:
            data[i] = 1
            if(write_block(disk, 0, data) != DISK_OK):
                return DISK_ERROR
            return i - BITMAP_OFFSET + 2        #2 to offset for the superblock and root inode blocks
            
    return DISK_ERROR

# Makes data's size block size, if smaller. Leaves data unchanged if larger
def make_blocksize(data):
    if len(data) < BLOCKSIZE:
        return data + bytes(BLOCKSIZE - len(data))
    return data

#Prints all blocks on disk that are not all 0s
def print_disk(disk):
    for i in range(NUMBER_OF_BLOCKS):
        data = bytearray(BLOCKSIZE)
        read_block(disk, i, data)
        if data != bytearray(BLOCKSIZE):  
            print(f"Block {i}: {data}")

#Inserts data into a buffer at a given index with a speficied size
def insert_data(buffer, index, data, data_size):
    buffer[index : index + data_size] = to_bytes(data, data_size)
    return buffer

#Inserts byte data into a buffer at a given index, replacing the data at that index
def insert_byte_data(buffer, index, data):
    buffer[index: index + len(data)] = data
    return buffer

#Converts most things into bytes
def to_bytes(data, data_size):
    return data.to_bytes(data_size, byteorder='big')

#Reads a given number of bytes from a buffer at a given offset and returns the integer value
def read_int_bytes(data, offset, size):
    return int.from_bytes(data[offset: offset + size], byteorder="big")
