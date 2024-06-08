from libDisk import *
from superblock import *
from utils import to_bytes, read_int_bytes


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
            return i - BITMAP_OFFSET
            
    return DISK_ERROR


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

def set_inodes_per_block(disk, number_of_inodes):
    data = bytearray(BLOCKSIZE)
    read_block(disk, 0, data)
    insert_data(data, INODES_PER_BLOCK_OFFSET, number_of_inodes, 1)
    return write_block(disk, 0, data)

def get_inodes_per_block(disk):
    data = bytearray(BLOCKSIZE)
    read_block(disk, 0, data)
    return read_int_bytes(data, INODES_PER_BLOCK_OFFSET, 1)

def free_block(disk, block_number):
    data = bytearray(BLOCKSIZE)
    read_block(disk, 0, data)
    data[BITMAP_OFFSET + block_number] = 0

    #Write the updated bitmap back to disk
    if write_block(disk, 0, data):
        #Zero out the block
        return write_block(disk, block_number, bytearray(BLOCKSIZE))
    return DISK_ERROR
