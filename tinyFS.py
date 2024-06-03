from superblock import *
from libDisk import *
from tinyFSHelpers import *
from inode import *

#Writes the superblock and root inode to block 0
def write_block0(disk):
    return write_block(disk, 0, make_blocksize(SuperBlock().toBytes() + ROOT_INODE))

def tfs_mkfs(filename, nBytes):

    #NOTE: 
    disk = open_disk(filename, nBytes)

    #Check magic number to see if this TFS has been initialized
    if nBytes == 0:
        if has_superblock(disk):
            return DISK_OK
        else:
            return DISK_ERROR

    #Zero out all bytes on disk
    for i in range(NUMBER_OF_BLOCKS):
        write_block(disk, i, bytes(BLOCKSIZE))

    #Write superblock to disk
    if write_block0(disk) == DISK_OK:
        #Write inodes to disk
        return write_initial_inodes(disk)
    else:
        return DISK_ERROR


def main():
    tfs_mkfs(DEFAULT_DISK_NAME, DEFAULT_DISK_SIZE)
    disk = open_disk(DEFAULT_DISK_NAME, 0)
    print_disk(disk)

    #Writes data to inode 1, should be contiguous because they are all allocated in a row
    write_data_to_inode(disk, 1, b"Hello, World!Hello, World!Hello, World!Hello, World!Hello, World!Hello, World!Hello, World!Hello, World!Hello, World!Hello, World!Hello, World!Hello, World!Hello, World!Hello, World!Hello, World!Hello, World!Hello, World!Hello, World!Hello, World!Hello, World!Hello, World!Hello, World!Hello, World!Hello, World!Hello, World!Hello, World!Hello, World!Hello, World!Hello, World!Hello, World!Hello, World!Hello, World!Hello, World!Hello, World!Hello, World!Hello, World!Hello, World!Hello, World!Hello, World!Hello, World!Hello, World!")
    write_data_to_inode(disk, 1, b"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa")
    write_data_to_inode(disk, 1, b"Hello, World!Hello, World!Hello, World!Hello, World!Hello, World!Hello, World!Hello, World!Hello, World!Hello, World!Hello, World!Hello, World!Hello, World!Hello, World!Hello, World!Hello, World!Hello, World!Hello, World!Hello, World!Hello, World!Hello, World!Hello, World!Hello, World!Hello, World!Hello, World!Hello, World!Hello, World!Hello, World!Hello, World!Hello, World!Hello, World!Hello, World!Hello, World!Hello, World!Hello, World!Hello, World!Hello, World!Hello, World!Hello, World!Hello, World!Hello, World!Hello, World!")

    #Writes data to inode 2, small enough that they will be in the same block, but a different block than inode 1
    write_data_to_inode(disk, 2, b"new data for inode 2")
    write_data_to_inode(disk, 2, b"Bello, Borld!")

    #Writes data to inode 1 again, but fills out the previous block and goes to the next block, notice the gap between 
    # inode 2's block and the new inode 1 block
    write_data_to_inode(disk, 1, b"a new block for 1a new block for 1a new block for 1a new 1a new block for 1a new1a new block for 1a new ")

    #Uncomment this if you want to see the inode's limits. This will pass the limit of 6 blocks per inode, and will return an error
    #write_data_to_inode(disk, 1, b"a new block for 1a new block for 1a new block for 1a new block for 1a new block for 1a new block for 1a new block for 1a new block for 1a new block for 1a new block for 1a new block for 1a new block for 1a new block for 1a new block for 1a new block for 1a new block for 1a new block for 1a new block for 1a new block for 1a new block for 1a new block for 1a new block for 1a new block for 1a new block for 1a new block for 1a new block for 1a new block for 1a new block for 1a new block for 1a new block for 1a new block for 1a new block for 1a new block for 1a new block for 1a new block for 1")

if __name__ == "__main__":
    main()