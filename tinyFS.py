from superblock import *
from libDisk import *
from tinyFSHelpers import *
from inode import *
from utils import to_bytes, read_int_bytes

# Global variables
current_disk = None
open_files = []

#Writes the superblock and root inode to block 0
def write_block0(disk):
    superblock = SuperBlock()
    root_inode = Inode(b'')
    block_data = make_blocksize(superblock.toBytes() + root_inode.toBytes())
    return write_block(disk, 0, block_data)
    #return write_block(disk, 0, make_blocksize(SuperBlock().toBytes() + ROOT_INODE))

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


def tfs_mount(filename):
    global current_disk
    current_disk = open_disk(filename, 0)
    if current_disk == DISK_ERROR:
        return DISK_ERROR

    data = bytearray(BLOCKSIZE)
    read_block(current_disk, 0, data)
    if data[0] != MAGIC_NUMBER:
        return DISK_ERROR
    return DISK_OK

def tfs_unmount():
    global current_disk
    if current_disk:
        close_disk(current_disk)
        current_disk = None
    return DISK_OK


def find_inode_by_name(name):
    # This function should search the root directory inode for the file name and return its inode number
    # For simplicity, assume root directory inode is at block 1 and contains a simple mapping of file names to inode numbers
    # This is a placeholder implementation
    root_dir_block = bytearray(BLOCKSIZE)
    read_block(current_disk, 1, root_dir_block)
    # Assume fixed size entries for file names (8 bytes) and inode numbers (4 bytes)
    entry_size = 12
    for i in range(0, len(root_dir_block), entry_size):
        if root_dir_block[i:i+8].decode('utf-8').strip('\x00') == name:
            return int.from_bytes(root_dir_block[i+8:i+12], 'big')
    return DISK_ERROR


def create_inode(name):
    # This function should create a new inode for the file and return its inode number
    # For simplicity, assume we can add the new inode at the first free slot in the root directory inode
    # This is a placeholder implementation
    root_dir_block = bytearray(BLOCKSIZE)
    read_block(current_disk, 1, root_dir_block)
    entry_size = 12
    for i in range(0, len(root_dir_block), entry_size):
        if root_dir_block[i:i+8] == bytearray(8):
            inode_num = i // entry_size + 2  # First inode number is 2 (superblock is 0, root directory is 1)
            root_dir_block[i:i+8] = name.ljust(8, '\x00').encode('utf-8')
            root_dir_block[i+8:i+12] = inode_num.to_bytes(4, 'big')
            write_block(current_disk, 1, root_dir_block)
            return inode_num
    return DISK_ERROR


def tfs_open(name):
    global open_files, current_disk

    inode_num = find_inode_by_name(name)
    # if cant find Inode, make a new one
    if inode_num == DISK_ERROR:
        inode_num = create_inode(name)
    if inode_num == DISK_ERROR:
        return DISK_ERROR

    fd = len(open_files)
    open_files.append({"inode": inode_num, "pointer": 0})
    return fd

def tfs_close(fd):
    global open_files
    if fd >= len(open_files):
        return DISK_ERROR
    open_files.pop(fd)
    return DISK_OK
    

def tfs_write(fd, buffer, size):
    global open_files, current_disk
    if fd >= len(open_files):
        return DISK_ERROR

    inode_num = open_files[fd]["inode"]
    inode = read_inode(current_disk, inode_num)
    if inode is None:
        return DISK_ERROR

    blocks_needed = (size + BLOCKSIZE - 1) // BLOCKSIZE
    if blocks_needed > len(inode.direct_blocks):
        return DISK_ERROR

    for i in range(blocks_needed):
        block_data = buffer[i * BLOCKSIZE:(i + 1) * BLOCKSIZE]
        block_num = inode.direct_blocks[i]
        if block_num == 0:
            block_num = allocate_block(current_disk)
            if block_num == DISK_ERROR:
                return DISK_ERROR
            inode.direct_blocks[i] = block_num
        write_block(current_disk, block_num, make_blocksize(block_data))

    inode.size = size
    write_inode(current_disk, inode_num, inode)
    open_files[fd]["pointer"] = 0
    return DISK_OK


def tfs_delete(fd):
    global open_files, current_disk
    if fd >= len(open_files):
        return DISK_ERROR

    inode_num = open_files[fd]["inode"]
    inode = read_inode(current_disk, inode_num)
    if inode is None:
        return DISK_ERROR

    for block_num in inode.direct_blocks:
        if block_num != 0:
            free_block(current_disk, block_num) #still need these functions

    remove_inode(current_disk, inode_num) #still need these functions
    open_files.pop(fd)
    return DISK_OK

def tfs_readByte(fd, buffer):
    global open_files, current_disk
    if fd >= len(open_files):
        return DISK_ERROR

    file_info = open_files[fd]
    inode = read_inode(current_disk, file_info["inode"])
    if inode is None:
        return DISK_ERROR

    if file_info["pointer"] >= inode.size:
        return DISK_ERROR

    block_num = file_info["pointer"] // BLOCKSIZE
    block_offset = file_info["pointer"] % BLOCKSIZE
    data_block_num = inode.direct_blocks[block_num]
    if data_block_num == 0:
        return DISK_ERROR

    data = bytearray(BLOCKSIZE)
    read_block(current_disk, data_block_num, data)
    buffer[0] = data[block_offset]
    open_files[fd]["pointer"] += 1
    return DISK_OK

def tfs_seek(fd, offset):
    global open_files
    if fd >= len(open_files):
        return DISK_ERROR
    open_files[fd]["pointer"] = offset
    return DISK_OK




def main():
    DEFAULT_DISK_NAME = "tinyfs.disk"
    DEFAULT_DISK_SIZE = 1024  

    # Create a TinyFS file system and mount the TinyFS file system
    tfs_mkfs(DEFAULT_DISK_NAME, DEFAULT_DISK_SIZE)
    tfs_mount(DEFAULT_DISK_NAME)

    #open the disk to test
    disk = open_disk(DEFAULT_DISK_NAME, 0)
    print_disk(disk)

    #pen a file named file1 on current mounted file system
    fd1 = tfs_open("file1")
    # Write a repeated "Hello, World!" to file1. message is > one block
    tfs_write(fd1, b"Hello, World!" * 20, len(b"Hello, World!" * 20))
    
    # buffer to read a single byte at a time and seek file1
    buffer = bytearray(1)
    tfs_seek(fd1, 0)
    
    # Read and print each byte from "file1" until reaching the end of the file
    while tfs_readByte(fd1, buffer) == DISK_OK:
        print(buffer.decode('utf-8'), end="")
    print_disk(disk)

    tfs_close(fd1)

    #same for file 2
    fd2 = tfs_open("file2")
    tfs_write(fd2, b"inode 2 having more daata here", len(b"inode 2 having more daata here"))
    print_disk(disk)

    tfs_close(fd2)
    # Unmount the TinyFS
    tfs_unmount()





# def main():
#     tfs_mkfs(DEFAULT_DISK_NAME, DEFAULT_DISK_SIZE)
#     disk = open_disk(DEFAULT_DISK_NAME, 0)
#     print_disk(disk)

#     #Writes data to inode 1, should be contiguous because they are all allocated in a row
#     write_data_to_inode(disk, 1, b"Hello, World!Hello, World!Hello, World!Hello, World!Hello, World!Hello, World!Hello, World!Hello, World!Hello, World!Hello, World!Hello, World!Hello, World!Hello, World!Hello, World!Hello, World!Hello, World!Hello, World!Hello, World!Hello, World!Hello, World!Hello, World!Hello, World!Hello, World!Hello, World!Hello, World!Hello, World!Hello, World!Hello, World!Hello, World!Hello, World!Hello, World!Hello, World!Hello, World!Hello, World!Hello, World!Hello, World!Hello, World!Hello, World!Hello, World!Hello, World!Hello, World!")
#     write_data_to_inode(disk, 1, b"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa")
#     write_data_to_inode(disk, 1, b"Hello, World!Hello, World!Hello, World!Hello, World!Hello, World!Hello, World!Hello, World!Hello, World!Hello, World!Hello, World!Hello, World!Hello, World!Hello, World!Hello, World!Hello, World!Hello, World!Hello, World!Hello, World!Hello, World!Hello, World!Hello, World!Hello, World!Hello, World!Hello, World!Hello, World!Hello, World!Hello, World!Hello, World!Hello, World!Hello, World!Hello, World!Hello, World!Hello, World!Hello, World!Hello, World!Hello, World!Hello, World!Hello, World!Hello, World!Hello, World!Hello, World!")

#     #Writes data to inode 2, small enough that they will be in the same block, but a different block than inode 1
#     write_data_to_inode(disk, 2, b"new data for inode 2")
#     write_data_to_inode(disk, 2, b"Bello, Borld!")

#     #Writes data to inode 1 again, but fills out the previous block and goes to the next block, notice the gap between 
#     # inode 2's block and the new inode 1 block
#     write_data_to_inode(disk, 1, b"a new block for 1a new block for 1a new block for 1a new 1a new block for 1a new1a new block for 1a new ")

#     #Uncomment this if you want to see the inode's limits. This will pass the limit of 6 blocks per inode, and will return an error
#     #write_data_to_inode(disk, 1, b"a new block for 1a new block for 1a new block for 1a new block for 1a new block for 1a new block for 1a new block for 1a new block for 1a new block for 1a new block for 1a new block for 1a new block for 1a new block for 1a new block for 1a new block for 1a new block for 1a new block for 1a new block for 1a new block for 1a new block for 1a new block for 1a new block for 1a new block for 1a new block for 1a new block for 1a new block for 1a new block for 1a new block for 1a new block for 1a new block for 1a new block for 1a new block for 1a new block for 1a new block for 1a new block for 1")

if __name__ == "__main__":
    main()