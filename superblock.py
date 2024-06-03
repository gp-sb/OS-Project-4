from libDisk import *

MAGIC_NUMBER = 0x5a
MAGIC_NUMBER_OFFSET=0
BLOCKSIZE_OFFSET=1
NUMBER_OF_BLOCKS_OFFSET=3
ROOT_DIR_INODE_NUMBER_OFFSET=5
BITMAP_OFFSET=9

class SuperBlock:
    def __init__(self, root_dir_inode_number=2):
        self.magic_number = MAGIC_NUMBER
        self.block_size = BLOCKSIZE
        self.number_of_blocks = NUMBER_OF_BLOCKS
        self.root_dir_inode_number = root_dir_inode_number
        self.free_block_bitmap = [0] * NUMBER_OF_BLOCKS

    def toBytes(self):
        return self.magic_number.to_bytes(1, byteorder='big') + \
                self.block_size.to_bytes(2, byteorder='big') + \
                self.number_of_blocks.to_bytes(2, byteorder='big') + \
                self.root_dir_inode_number.to_bytes(4, byteorder='big') + \
                bytearray(self.free_block_bitmap)
