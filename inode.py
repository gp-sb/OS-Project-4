from libDisk import *
from tinyFSHelpers import set_inodes_per_block, get_inodes_per_block, allocate_block, insert_byte_data, insert_data
from utils import to_bytes, read_int_bytes, make_blocksize

#Block Organization
    #block 0 is superblock
    #block 1 is root dir
    #block 2 is INODE

MAX_INODES = 20 # maximum amount of Inodes (max files is MAX_INODES-3)
MAX_BLOCKS_PER_INODE = 6
INODE_SIZE_OFFSET = 2
REMAINING_DATA_IN_CURRENT_BLOCK_OFFSET = 6
DIRECT_BLOCK_OFFSET = 8

ROOT_INODE = (0x02 + (0x00 * MAX_INODES)).to_bytes(12, byteorder='little')
INODE_SIZE = 14 #Subject to change



#Object to load data into, so we can use in python
class Inode:
    def __init__(self, data):
        #if we are reading data or just creating a new inode
        if data != b'':
            self.fromBytes(data)
        else:
            self.number = 0
            self.size = len(data)           # Needed to know how much of last block is used
            self.max_data_size = 256 * MAX_BLOCKS_PER_INODE    # In bytes
            self.remaining_bytes_in_current_block = 0
            self.direct_blocks = [0] * MAX_BLOCKS_PER_INODE    # 6 direct blocks

    #Determines the INODE_SIZE
    def toBytes(self):
        blocks = [to_bytes(x, 1) for x in self.direct_blocks]
        return bytearray(to_bytes(self.number, 2) + \
                         to_bytes(self.size, 4) + \
                         to_bytes(self.remaining_bytes_in_current_block, 2) + \
                         b''.join(blocks))

    def fromBytes(self, data):
        self.number = read_int_bytes(data, 0, 2)
        self.size = read_int_bytes(data, INODE_SIZE_OFFSET, 4)
        self.remaining_bytes_in_current_block = read_int_bytes(data, REMAINING_DATA_IN_CURRENT_BLOCK_OFFSET, 2)
        self.direct_blocks = [read_int_bytes(data, DIRECT_BLOCK_OFFSET + i, 1) for i in range(MAX_BLOCKS_PER_INODE)]

def remove_inode(disk, inode_number):
    inode_block_bytes = bytearray(BLOCKSIZE)
    read_block(disk, 2, inode_block_bytes)
    inode_index = inode_number * INODE_SIZE
    empty_inode = Inode(b'')
    empty_inode.number = inode_number
    insert_byte_data(inode_block_bytes, inode_index, empty_inode.toBytes())
    return write_block(disk, 2, inode_block_bytes)

def write_initial_inodes(disk):
    empty_inode = Inode(b'')

    space_needed_for_inodes = INODE_SIZE * MAX_INODES
    blocks_needed_for_inodes = space_needed_for_inodes // BLOCKSIZE
    inodes_per_block = BLOCKSIZE // INODE_SIZE

    set_inodes_per_block(disk, inodes_per_block)

    #This is the case where the Inodes and the root inode cannot fit in one block, so we will fill the inodes out
    #and then write the root inode to the next block, at the end of block 0. I'd prefer the latter.
    current_block = 2
    final_block = blocks_needed_for_inodes + current_block
    current_inode = 0
    while current_block != final_block+1:          #Two is from: initial_block_number + total_blocks_needed
        inode_bytes = b""

        #This block labels the inodes with numbers, just keeping this for now so  we can clearly see them
        for i in range(inodes_per_block):
            empty_inode.number = current_inode
            b = empty_inode.toBytes()
            inode_bytes += b
            current_inode += 1
            if current_inode == MAX_INODES:
                break
        
        if(write_block(disk, current_block, make_blocksize(inode_bytes))) != DISK_OK:
            return DISK_ERROR
        
        current_block += 1

    return DISK_OK
    
# def read_inode(disk, inode_number):
#     inode_bytes = bytearray(256)
#     read_block(disk, 1, inode_bytes)
#     return inode_bytes[INODE_SIZE*inode_number : INODE_SIZE*(inode_number+1)]

def read_inode(disk, inode_number):
    inode_block_bytes = bytearray(BLOCKSIZE)

    inodes_per_block = get_inodes_per_block(disk)
    block_offset = 2 + (inode_number // inodes_per_block)
    inode_offset = inode_number % inodes_per_block
    read_block(disk, block_offset, inode_block_bytes)
    inode_bytes = inode_block_bytes[INODE_SIZE*inode_offset : INODE_SIZE*(inode_offset+1)]
    return Inode(inode_bytes)

def write_inode(disk, inode_number, inode):
    inode_block_bytes = bytearray(BLOCKSIZE)
    read_block(disk, 1, inode_block_bytes)
    inode_bytes = inode.toBytes()
    start_index = INODE_SIZE * inode_number
    end_index = start_index + INODE_SIZE
    inode_block_bytes[start_index:end_index] = inode_bytes
    write_block(disk, 1, make_blocksize(inode_block_bytes))

def update_inode_block(disk, new_block, old_block):

    #Iterate through inodes to find the inode with the old block
    data = bytearray(BLOCKSIZE)
    read_block(disk, 2, data)

    for i in range(0, INODE_SIZE*MAX_INODES, INODE_SIZE):
        inode_bytes = data[i:i+INODE_SIZE]
        print(inode_bytes)
        inode = Inode(inode_bytes)
        for b in range(MAX_BLOCKS_PER_INODE):
            if inode.direct_blocks[b] == old_block:
                print(data[i+DIRECT_BLOCK_OFFSET+b])
                data[i+DIRECT_BLOCK_OFFSET+b] = new_block
                write_block(disk, 2, data)
                return DISK_OK
    
# Determines if we can add data to old block, or if we need to add a new block, updates the inode accordingly,
# Returns:
#   - prev_block_number: The block number that is currently being written to, if -1, then we do not write to that block
#   - new_block_number: The block number that was added to the inode, if -1, then we do not add a new block
#   - remaining_space_in_current_block: The remaining space in the current block
def add_block_to_inode(disk, inode_number, data_size):

    #Read entire Inode block
    inode_block_bytes = bytearray(BLOCKSIZE)
    read_block(disk, 2, inode_block_bytes)
    inode_index = inode_number * INODE_SIZE

    #Get specific Inode's bytes
    inode_bytes = inode_block_bytes[inode_index: INODE_SIZE*(inode_number+1)]

    #Get the current size of the inode and caluclate if we need to add a new block
    inode_size = read_int_bytes(inode_bytes, INODE_SIZE_OFFSET, 4)
    remaining_space_in_prev_block = read_int_bytes(inode_bytes, REMAINING_DATA_IN_CURRENT_BLOCK_OFFSET, 2)

    #If the data size is greater than the remaining space
    add_new_block = inode_size == 0 or data_size > remaining_space_in_prev_block

    #Setup variables for information in order to write to disk
    prev_block_index  = inode_size // BLOCKSIZE
    at_start_index = remaining_space_in_prev_block == 0 and prev_block_index == 0
    #If we're at special case of the start of a block, we need g back one index (any multiple of 256)
    prev_block_index = prev_block_index -1 if remaining_space_in_prev_block == 0 and prev_block_index != 0 else prev_block_index

    # Do not write to previous block if it is full, -1 tells outer function to not write to that block
    prev_block_number = -1 if remaining_space_in_prev_block == 0 else read_int_bytes(inode_bytes, DIRECT_BLOCK_OFFSET + prev_block_index, 1)

    #Assume we do not add a new block
    new_block_number = -1


    if add_new_block:

        #Get a block to allocate, if full, error out
        new_block_number = allocate_block(disk)
        if new_block_number == DISK_ERROR:
            return -1, -1, DISK_ERROR

        #Calcs are messeed up for first index, so just set to 0 if we are starting the inode
        new_block_index = 0 if at_start_index else  prev_block_index + 1

        #Error if we've hit the max number of blocks per inode
        if new_block_index == MAX_BLOCKS_PER_INODE:
            return -1, -1, DISK_ERROR
        
        #Update the block number in the inode
        inode_block_bytes = insert_data(inode_block_bytes, inode_index + DIRECT_BLOCK_OFFSET + new_block_index, new_block_number, 1)

        #Update the remaining space in the new block
        data_written_to_new_block = data_size - remaining_space_in_prev_block
        remaining_space_in_current_block = BLOCKSIZE - data_written_to_new_block
    else:
        #Update the remaining space in the current block
        remaining_space_in_current_block = remaining_space_in_prev_block - data_size
    
    #Update remaining space of the current block in inode metadata
    inode_block_bytes = insert_data(inode_block_bytes, inode_index + REMAINING_DATA_IN_CURRENT_BLOCK_OFFSET, remaining_space_in_current_block, 2)

    # Update the size of the inode in inode metadata
    inode_size += data_size
    inode_block_bytes = insert_data(inode_block_bytes, inode_index + INODE_SIZE_OFFSET, inode_size, 4)

    #Write the updated inode back to disk
    if write_block(disk, 2, inode_block_bytes) == DISK_OK:
        return prev_block_number, new_block_number, remaining_space_in_current_block
    else:
        return -1, -1, DISK_ERROR
    
    
def write_data_to_inode(disk, inode_number, data):

    data = bytearray(data)

    #While we have data to write
    while len(data) > 0:

        #Buffer for writing data to disk
        write_bytes = bytearray(BLOCKSIZE)
        
        write_length = len(data) if len(data) < BLOCKSIZE else BLOCKSIZE

        #Add the block to the inode
        prev_block_number, new_block_number, remaining_bytes_in_block = add_block_to_inode(disk, inode_number, write_length)
        if remaining_bytes_in_block == DISK_ERROR:
            return DISK_ERROR
        
        # If we need to write to both a new block and the previous block,
        # calculate how much data we write to the previous block, write it, then write to the new block
        if prev_block_number != -1 and new_block_number != -1:

            #Write to the previous block
            bytes_to_new_block = BLOCKSIZE - remaining_bytes_in_block
            bytes_to_prev_block = write_length - bytes_to_new_block
            read_block(disk, prev_block_number, write_bytes)
            write_bytes = insert_byte_data(write_bytes, BLOCKSIZE - bytes_to_prev_block, data[:bytes_to_prev_block])
            if write_block(disk, prev_block_number, write_bytes) != DISK_OK:
                return DISK_ERROR
            
            #Write to the new block
            write_bytes = bytearray(BLOCKSIZE)
            read_block(disk, new_block_number, write_bytes)
            write_bytes = insert_byte_data(write_bytes, 0, data[bytes_to_prev_block:write_length])
            if write_block(disk, new_block_number, make_blocksize(write_bytes)) != DISK_OK:
                return DISK_ERROR
        
        #If we only need to write to the previous block
        elif prev_block_number != -1 and new_block_number == -1:
            read_block(disk, prev_block_number, write_bytes)
            write_bytes = insert_byte_data(write_bytes, BLOCKSIZE - (remaining_bytes_in_block + write_length), data)
            if write_block(disk, prev_block_number, write_bytes) != DISK_OK:
                return DISK_ERROR

        #If we only need to write to the new block
        elif prev_block_number == -1 and new_block_number != -1:
            write_bytes = insert_byte_data(write_bytes, 0, data)
            if write_block(disk, new_block_number, make_blocksize(data[:write_length])) != DISK_OK:
                return DISK_ERROR
            
        #This means add_block_to_inode returned an error
        else:
            return DISK_ERROR
        
        data = data[write_length:]

    return DISK_OK
