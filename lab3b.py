import sys
import csv

superblock = None
inodes = []
inode_freelist = {}
allocated_inodes = {}
link_counts = {}  # actual link counts
parent_dir = {2: 2}  # 2 is the reserved inode number for root directory
dir_entries = []
has_error = False


class Superblock:
    def __init__(self, line):
        self.n_blocks = int(line[1])
        self.n_inodes = int(line[2])
        self.first_inode_no = int(line[7])


class Inode:
    def __init__(self, line):
        self.index = int(line[1])
        self.file_type = line[2]
        self.group = int(line[5])
        self.link_count = int(line[6])
        self.file_size = int(line[10])
        self.n_blocks = int(line[11])
        self.block_pointers = map(int, line[12:])


class DirectoryEntries:
    def __init__(self, line):
        self.parent_inode_no = int(line[1])
        self.inode_no = int(line[3])
        self.name = line[6]


def init():
    global superblock
    try:
        with open(sys.argv[1], 'r') as csvfile:
            lines = csv.reader(csvfile, delimiter=',')
            for line in lines:
                if line[0] == "SUPERBLOCK":
                    superblock = Superblock(line)
                elif line[0] == "IFREE":
                    inode_freelist[int(line[1])] = None
                elif line[0] == "INODE":
                    allocated_inodes[int(line[1])] = Inode(line)
                    inodes.append(Inode(line))
                elif line[0] == "DIRENT":  # directory entries
                    inode_no = int(line[3])
                    if inode_no in link_counts:
                        link_counts[inode_no] += 1
                    else:
                        link_counts[inode_no] = 1
                    dir_entry = DirectoryEntries(line)
                    dir_entries.append(dir_entry)
                    if dir_entry.name != "'.'" and dir_entry.name != "'..'":
                        parent_dir[dir_entry.inode_no] = dir_entry.parent_inode_no
    except:
        sys.stderr.write('Error: failed to open the csv file\n')
        exit(1)


def audit_inode_allocation():
    global has_error
    for key in allocated_inodes:
        if key in inode_freelist:
            print("ALLOCATED INODE "+str(key)+" ON FREELIST")
            has_error = True
    for i in range(superblock.first_inode_no, superblock.n_inodes+1):
        if i not in allocated_inodes and i not in inode_freelist:
            print("UNALLOCATED INODE "+str(i)+" NOT ON FREELIST")
            has_error = True


def audit_directory_consistency():
    global has_error
    for key in allocated_inodes:
        temp = allocated_inodes[key].link_count
        if key not in link_counts:
            print("INODE "+str(key)+" HAS 0 LINKS BUT LINKCOUNT IS "+str(temp))
            has_error = True
        elif temp != link_counts[key]:
            print("INODE "+str(key)+" HAS "+str(link_counts[key])+" LINKS BUT LINKCOUNT IS "+str(temp))
            has_error = True
    for dir_entry in dir_entries:
        if dir_entry.inode_no < 1 or dir_entry.inode_no > superblock.n_inodes:
            print("DIRECTORY INODE "+str(dir_entry.parent_inode_no)+" NAME "+dir_entry.name+" INVALID INODE "
                  + str(dir_entry.inode_no))
            has_error = True
        elif dir_entry.inode_no not in allocated_inodes:
            print("DIRECTORY INODE "+str(dir_entry.parent_inode_no)+" NAME "+dir_entry.name+" UNALLOCATED INODE "
                  + str(dir_entry.inode_no))
            has_error = True
        if dir_entry.name == "'..'":  # link to its parent
            if dir_entry.inode_no != parent_dir[dir_entry.inode_no]:
                print("DIRECTORY INODE "+str(dir_entry.parent_inode_no)+" NAME '..' LINK TO INODE "
                      + str(dir_entry.inode_no)+" SHOULD BE "+str(parent_dir[dir_entry.inode_no]))
                has_error = True
        elif dir_entry.name == "'.'":  # link to itself
            if dir_entry.inode_no != dir_entry.parent_inode_no:
                print("DIRECTORY INODE "+str(dir_entry.parent_inode_no)+" NAME '.' LINK TO INODE "
                      + str(dir_entry.inode_no)+" SHOULD BE "+str(dir_entry.parent_inode_no))
                has_error = True


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.stderr.write('Error: invalid arguments\n')
        sys.stderr.write('Usage: lab3b filename_of_summary\n')
        exit(1)

    init()
    audit_inode_allocation()
    audit_directory_consistency()

    if has_error is True:
        exit(2)
    else:
        exit(0)
