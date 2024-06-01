from libDisk import *


BITMAP_OFFSET=16
class SuperBlock:
    def __init__(self, root_dir_inode_number=2):
        self.magic_number = b"0x5a"
        self.block_size = BLOCKSIZE
        self.number_of_blocks = DEFAULT_DISK_SIZE // BLOCKSIZE
        self.root_dir_inode_number = root_dir_inode_number
        self.free_block_bitmap = [0] * self.number_of_blocks

    def toBytes(self):
        return self.magic_number + \
                self.block_size.to_bytes(4, byteorder='big') + \
                self.number_of_blocks.to_bytes(4, byteorder='big') + \
                self.root_dir_inode_number.to_bytes(4, byteorder='big') + \
                bytearray(self.free_block_bitmap)
    
    

class Inode:
    def __init__(self, name, data):
        self.name = name
        self.size = len(data)
        self.direct_blocks = []
        self.indirect_block = []
        self.max_data_size = 12 * 256 + 256 * 256       #In bytes

    def initial_write(self, data):
        #Checks to see if data is larger than max data size, if not
        #Writes data to 12 direct blocks then to indirect block
        if len(data) > self.max_data_size:
            return DISK_ERROR
        
        self.size = len(data)
        
        for i in range(12):
            #If we have data to write
            if len(data) > 0:
                #If data is not a full block
                if len(data) < 256:
                    self.direct_blocks[i] = data
                #If data is a full block
                else:
                    self.direct_blocks[i] = data[:256]
                    data = data[256:]
            else:
                break

class TinyFS:
    def __init__(self, filename, disk, sb):
        self.filename = filename
        self.disk = disk
        self.sb = sb


def main():

    sb = SuperBlock(10)
    print(sb.toBytes().hex(":"))

if __name__ == "__main__":
    main()
