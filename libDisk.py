import os

BLOCKSIZE = 256

# errors
DISK_OK = 0
DISK_ERROR = -1



def main():
    filename = "disk.img"
    disk = open_disk(filename, 1024)  # 1KB disk for now...
    
    if disk == DISK_ERROR:
        print("Failed to open disk")
        return 1
    
    # write
    write_data = bytearray("Hey, Joe. What you doing with that gun in your hand?!".ljust(BLOCKSIZE, '\x00'), 'utf-8')
    if write_block(disk, 0, write_data) != DISK_OK: # cehck write OK
        print("Failed to write block")
        close_disk(disk)
        return 1

    # read
    read_data = bytearray(BLOCKSIZE)
    if read_block(disk, 0, read_data) != DISK_OK:
        print("Failed to read block")
        close_disk(disk)
        return 1
    
    print("Read:", read_data.decode('utf-8').rstrip('\x00'))

    close_disk(disk)
    return 0




def open_disk(filename, nBytes):
    # his function opens a regular UNIX file and designates the first 
    # nBytes of it as space for the emulated disk.
    try:
        #check byte
        if nBytes > 0:
            with open(filename, 'wb') as f:
                f.truncate(nBytes)
            fd = open(filename, 'r+b')
        else:
            fd = open(filename, 'r+b')
        return fd
    except Exception as e:
        print(f"Error opening file: {e}")
        return DISK_ERROR


def read_block(disk, bNum, block):
    # readBlock() reads an entire block of BLOCKSIZE bytes from the open disk 
    # (identified by ‘disk’) and copies the result into a local buffer (must 
    # be at least of BLOCKSIZE bytes).
    try:
        if disk.closed:
            raise ValueError("Disk not open")
        offset = bNum * BLOCKSIZE
        disk.seek(offset)
        data = disk.read(BLOCKSIZE)
        if len(data) != BLOCKSIZE:
            raise IOError("Error reading block")
        block[:] = data
        return DISK_OK
    except Exception as e:
        print(f"Error reading block: {e}")
        return DISK_ERROR


def write_block(disk, bNum, block):
    # writeBlock() takes disk number ‘disk’ and logical block number ‘bNum’
    # and writes the content of the buffer ‘block’ to that location.
    try:
        if disk.closed:
            raise ValueError("Disk not open")
        if len(block) != BLOCKSIZE:
            raise ValueError("Block size must be 256 bytes")
        offset = bNum * BLOCKSIZE
        disk.seek(offset)
        disk.write(block)
        disk.flush()
        return DISK_OK
    except Exception as e:
        print(f"Error writing block: {e}")
        return DISK_ERROR


def close_disk(disk):
    # closeDisk() takes a disk number ‘disk’ and makes
    # the disk closed to further I/O;
    try:
        if not disk.closed:
            disk.close()
    except Exception as e:
        print(f"Error closing disk: {e}")




if __name__ == "__main__":
    main()