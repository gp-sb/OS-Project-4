from superblock import *
from libDisk import *
from tinyFSHelpers import *
from inode import *
from utils import to_bytes, read_int_bytes, find_ranges

# Global variables
current_disk = None
open_files = []
MAX_FILES = MAX_INODES - 3

#Writes the superblock and root inode to block 0
def write_init_blocks(disk):
    superblock = SuperBlock()
    root_inode = Inode(b'')
    block_data = make_blocksize(superblock.toBytes())
    if write_block(disk, 0, block_data) == DISK_OK:
        block_data = make_blocksize((bytearray(8) + bytearray(2)) * MAX_FILES)
        return write_block(disk, 1, block_data)

def tfs_mkfs(filename, nBytes):
    global current_disk

    current_disk = open_disk(filename, nBytes)

    #Check magic number to see if this TFS has been initialized
    if nBytes == 0:
        if has_superblock(current_disk):
            return DISK_OK
        else:
            return DISK_ERROR

    #Zero out all bytes on disk
    for i in range(NUMBER_OF_BLOCKS):
        write_block(current_disk, i, bytes(BLOCKSIZE))

    #Write superblock to disk
    if write_init_blocks(current_disk) == DISK_OK:
        #Write inodes to disk
        return write_initial_inodes(current_disk)
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
    entry_size = 10
    for i in range(0, len(root_dir_block), entry_size):
        if root_dir_block[i:i+8].decode('utf-8').strip('\x00') == name:
            return read_int_bytes(root_dir_block, i+8, 2)
    return DISK_ERROR


def create_inode(name):
    # This function should create a new inode for the file and return its inode number
    # For simplicity, assume we can add the new inode at the first free slot in the root directory inode
    # This is a placeholder implementation
    root_dir_block = bytearray(BLOCKSIZE)
    read_block(current_disk, 1, root_dir_block)
    entry_size = 10
    for i in range(0, len(root_dir_block), entry_size):
        if root_dir_block[i:i+8] == bytearray(8):
            inode_num = i // entry_size
            root_dir_block[i:i+8] = name.ljust(8, '\x00').encode('utf-8')
            root_dir_block[i+8:i+10] = to_bytes(inode_num, 2)
            print(root_dir_block)
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
    open_files.append({"inode": inode_num, "byte_pointer": 0})
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
    if inode_num is None:
        return DISK_ERROR

    if write_data_to_inode(current_disk, inode_num, buffer) == DISK_ERROR:
        return DISK_ERROR
    
    open_files[fd]["byte_pointer"] = 0
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
            free_block(current_disk, block_num)

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

    if file_info["byte_pointer"] >= inode.size:
        return DISK_ERROR

    block_index = file_info["byte_pointer"] // BLOCKSIZE
    byte_offset = file_info["byte_pointer"] % BLOCKSIZE
    data_block_num = inode.direct_blocks[block_index]
    if data_block_num == 0 or data_block_num >= NUMBER_OF_BLOCKS:
        return DISK_ERROR

    data = bytearray(BLOCKSIZE)
    read_block(current_disk, data_block_num, data)
    buffer[0] = data[byte_offset]
    open_files[fd]["byte_pointer"] += 1
    return DISK_OK

def tfs_seek(fd, offset):
    global open_files
    if fd >= len(open_files):
        return DISK_ERROR
    open_files[fd]["byte_pointer"] = offset
    return DISK_OK

def tfs_displayfragments():
    global current_disk
    data = bytearray(BLOCKSIZE)
    read_block(current_disk, 0, data)
    print(data[BITMAP_OFFSET:BITMAP_OFFSET + 5])
    int_list = [int.from_bytes(data[i:i+1], byteorder="little") for i in range(BITMAP_OFFSET, BITMAP_OFFSET + NUMBER_OF_BLOCKS)]
    print("Contiguous block memory ranges:")
    print(find_ranges(int_list))

def tfs_defrag():
    global current_disk
    block_0 = bytearray(BLOCKSIZE)
    read_block(current_disk, 0, block_0)
    bit_map = block_0[BITMAP_OFFSET:BITMAP_OFFSET + NUMBER_OF_BLOCKS]
    first_index = 0
    last_index = len(bit_map) - 1

    while first_index < last_index:
        if bit_map[first_index] == 1:
            first_index += 1
        elif bit_map[last_index] == 0:
            last_index -= 1
        else:
            swap_blocks(current_disk, first_index, last_index)
            update_inode_block(current_disk, first_index, last_index)
            bit_map[first_index] = 1
            bit_map[last_index] = 0
            first_index += 1
            last_index -= 1


    insert_byte_data(block_0, BITMAP_OFFSET, bit_map)
    write_block(current_disk, 0, block_0)
    return DISK_OK



def main():

    # Create a TinyFS file system and mount the TinyFS file system
    tfs_mkfs(DEFAULT_DISK_NAME, DEFAULT_DISK_SIZE)
    tfs_mount(DEFAULT_DISK_NAME)

    #open the disk to test
    disk = open_disk(DEFAULT_DISK_NAME, 0)

    #pen a file named file1 on current mounted file system
    fd1 = tfs_open("file1")
    # Write a repeated "Hello, World!" to file1. message is > one block
    tfs_write(fd1, b"Hello, World!", len(b"Hello, World!"))
    
    # buffer to read a single byte at a time and seek file1
    buffer = bytearray(1)
    tfs_seek(fd1, 0)
    
    tfs_close(fd1)
    #same for file 2
    fd2 = tfs_open("file2")
    tfs_write(fd2, b"inode 2 having more daata here", len(b"inode 2 having more daata here"))
    tfs_close(fd2)


    fd3 = tfs_open("file3")
    tfs_write(fd3, b"allocate another file", len(b"inode 2 having more daata here"))
    tfs_close(fd3)

    fd4 = tfs_open("file4")
    tfs_write(fd4, b"allocate one last  file", len(b"inode 2 having more daata here"))
    tfs_close(fd4)

    
    fd2 = tfs_open("file2")
    tfs_delete(fd2)
    tfs_close(fd2)

    fd2 = tfs_open("file3")
    tfs_delete(fd2)
    tfs_close(fd2)

    tfs_displayfragments()
    fd1 = tfs_open("file4")
    tfs_defrag()
    while tfs_readByte(fd1, buffer) == DISK_OK:
        print(buffer.decode('utf-8'), end="")

    tfs_displayfragments()
    


    # Unmount the TinyFS
    tfs_unmount()

if __name__ == "__main__":
    main()