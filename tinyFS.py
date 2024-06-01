from tinyFSObjects import *
from libDisk import *
from tinyFSHelpers import *

def tfs_mkfs(filename, nBytes):

    #NOTE: 
    disk = open_disk(filename, nBytes)

    #Check magic number to see if this TFS has been initialized
    if nBytes == 0:
        if has_superblock(disk):
            return DISK_OK
        else:
            return DISK_ERROR

    #Otherwise create a new TFS
    #At this point, the classes just help organize thoughts
    sb = SuperBlock()
    tfs = TinyFS(filename, disk, sb)

    #Zero out all bytes on disk
    for i in range(tfs.sb.number_of_blocks):
        write_block(disk, i, bytes(256))

    #Write superblock to disk
    if write_superblock(tfs) == DISK_OK:
        return tfs
    else:
        return DISK_ERROR


def main():
    tfs = tfs_mkfs(DEFAULT_DISK_NAME, DEFAULT_DISK_SIZE)

if __name__ == "__main__":
    main()