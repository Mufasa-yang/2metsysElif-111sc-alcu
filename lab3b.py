#!/usr/local/cs/bin/python

# NAME:Xiao Yang,Zhengyuan Liu
# EMAIL:avadayang@icloud.com,zhengyuanliu@ucla.edu
# ID:104946787,604945064


import csv
import sys
import os

exit_consistent = 0
exit_error = 1
exit_inconsistent = 2

consistent=1

groupDesc=[]

# free block number
freeBlock=[]
inodes = []
inode_freelist = {}
allocated_inodes = {}
link_counts = {}  # actual link counts
parent_dir = {2: 2}  # 2 is the reserved inode number for root directory
dir_entries = []
has_error = False
superBlock=None
inodeSummary=[]
indirects=[]

blockMap={}
#key:block number
#value: [level, inode #, offset]
levelName = ["", "INDIRECT ", "DOUBLE INDIRECT ", "TRIPLE INDIRECT "]
class SuperBlock:
    numOfFields = 8#how many fields a row should have
    def __init__(self, row):
		self.n_blocks=int(row[1])
		self.n_inodes=int(row[2])
		self.blockSize=int(row[3])
		self.s_inode_size=int(row[4])
		self.s_blocks_per_group=int(row[5])
		self.s_inodes_per_group=int(row[6])
		self.first_inode_no=int(row[7])

class GroupDesc:
    numOfFields = 9#how many fields a row should have
    def __init__(self,row):
        self.i=int(row[1])
        self.numOfBlocksInGroup=int(row[2])
        self.numOfInodesInGroup=int(row[3])
        self.bg_free_blocks_count=int(row[4])
        self.bg_free_inodes_count=int(row[5])
        self.bg_block_bitmap=int(row[6])
        self.bg_inode_bitmap=int(row[7])
        self.bg_inode_table=int(row[8])

class Inode:
    numOfFields=27#how many fields a row should have
    def __init__(self,row):
        self.i=int(row[1])
        self.type=row[2]
        self.gid=int(row[5])
        self.link_count=int(row[6])
        self.blocks=map(int, row[12:27])

class DirectoryEntries:
    def __init__(self, line):
        self.parent_inode_no = int(line[1])
        self.inode_no = int(line[3])
        self.name = line[6]

class Indirect:
    numOfFields = 6  # how many fields a row should have
    def __init__(self,row):
        self.inode=int(row[1])
        self.level=int(row[2])
        self.offset=int(row[3])
        self.blockNumber=int(row[4])
        self.pointedBlockNumber=int(row[5])



def checkRowLength(num,title,row):
    if len(row) != num :
        exitWithError("row length wrong for" + title)

def readNparse(filename):
    global superBlock ,groupDesc,freeBlock, inodeSummary, indirects
    try:
        with open(filename, 'r') as csvfile:
            rows = csv.reader(csvfile, delimiter=',')
            for row in rows:
                if (len(row) <= 0):
                    exitWithError("row length is 0")
                title = row[0]
                if title == 'SUPERBLOCK':
                    checkRowLength(SuperBlock.numOfFields, "SUPERBLOCK", row)
                    superBlock = SuperBlock(row)
                elif title == 'GROUP':
                    checkRowLength(GroupDesc.numOfFields, "GROUP", row)
                    groupDesc.append(GroupDesc(row))
                elif title == 'BFREE':
                    if (len(row) != 2):
                        exitWithError("BFREE format wrong")
                    freeBlock.append(int(row[1]))
                elif title == 'INODE':
                    allocated_inodes[int(row[1])] = Inode(row)
                    inodes.append(Inode(row))
                    if (len(row) < 13):
                        exitWithError("INODE format wrong")
                    if (row[2] == 'd' or row[
                        2] == 'f'):  # according to piazza, only look into pointers for file/directory
                        checkRowLength(Inode.numOfFields, "INODE", row)
                        inodeSummary.append(Inode(row))
                elif title == 'INDIRECT':
                    checkRowLength(Indirect.numOfFields, "INDIRECT", row)
                    indirects.append(Indirect(row))
                elif title == "IFREE":
                    inode_freelist[int(row[1])] = None
                elif title == "DIRENT":  # directory entries
                    inode_no = int(row[3])
                    if inode_no in link_counts:
                        link_counts[inode_no] += 1
                    else:
                        link_counts[inode_no] = 1
                    dir_entry = DirectoryEntries(row)
                    dir_entries.append(dir_entry)
                    if dir_entry.name != "'.'" and dir_entry.name != "'..'":
                        parent_dir[dir_entry.inode_no] = dir_entry.parent_inode_no
                else:
                    exitWithError("error wrong data in csv\n")
    except:
        sys.stderr.write('Error: failed to open the csv file\n')
        exit(1)



def insertBlockMap(level,blockNum,nodeI,offset):
    global superBlock, groupDesc, freeBlock, inodeSummary, indirects, blockMap, consistent, levelName
    if(blockNum!= 0):
        if(blockNum<0 or blockNum>superBlock.n_blocks-1):
            print("INVALID {}BLOCK {} IN INODE {} AT OFFSET {}".format(
                levelName[level], blockNum, nodeI, offset))
            consistent=0
        elif(blockNum<5+int(superBlock.s_inodes_per_group/(superBlock.blockSize/superBlock.s_inode_size))):
            print("RESERVED {}BLOCK {} IN INODE {} AT OFFSET {}".format(
                levelName[level], blockNum, nodeI, offset))
            consistent=0
        elif blockNum not in blockMap:
            blockMap[blockNum] = []
            blockMap[blockNum].append([level, nodeI, offset])
        else:
            blockMap[blockNum].append([level, nodeI, offset])

def constrBlockMap():
    global inodeSummary,superBlock,indirects
    numPointerPerBlock = int(superBlock.blockSize / 4)
    #first tke care of nodeSummary
    for node in inodeSummary:
        for i in range(0, 15):
            if (i < 12):
                level = 0
                offset = i
            if (i == 12):
                level = 1
                offset = 12
            if (i == 13):
                level = 2
                offset = 12 + numPointerPerBlock
            if (i == 14):
                level = 3
                offset = 12 + numPointerPerBlock + numPointerPerBlock * numPointerPerBlock
            insertBlockMap(level,node.blocks[i],node.i,offset)
    for indirect in indirects:
        insertBlockMap(indirect.level,indirect.pointedBlockNumber,indirect.inode,indirect.offset)

def exitWithError(message):
    sys.stderr.write(message)
    exit(exit_error)

def blockAudit():
    global consistent,blockMap,freeBlock,superBlock
    start = 5 + int(superBlock.s_inodes_per_group / (superBlock.blockSize / superBlock.s_inode_size))
    end = superBlock.n_blocks
    constrBlockMap()
    for block in range(start,end):
        if (block not in blockMap) and (block not in freeBlock):
            print("UNREFERENCED BLOCK {}".format(block))
            consistent=0
        elif block in blockMap and block in freeBlock:
            print("ALLOCATED BLOCK {} ON FREELIST".format(block))
            consistent = 0
        elif block in blockMap and len(blockMap[block])>1:
            for entry in blockMap[block]:
                print("DUPLICATE {}BLOCK {} IN INODE {} AT OFFSET {}".format(
                    levelName[entry[0]], block, entry[1], entry[2]))
                consistent = 0

def audit_inode_allocation():
    global has_error
    for key in allocated_inodes:
        if key in inode_freelist:
            print("ALLOCATED INODE "+str(key)+" ON FREELIST")
            has_error = True
    for i in range(superBlock.first_inode_no, superBlock.n_inodes+1):
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
        if dir_entry.inode_no < 1 or dir_entry.inode_no > superBlock.n_inodes:
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





if __name__ == '__main__':
    #check argument
    if (len(sys.argv)) != 2:
        sys.stderr.write("bad argument\n")
        sys.stderr.write('Usage: lab3b filename_of_summary\n')
        exit(exit_error)

    #read and parse
    filename = sys.argv[1]
    if not os.path.isfile(filename):
        sys.stderr.write("file not exist\n")
        exit(exit_error)

    readNparse(filename)
    #readNparse("P3B-test_11.csv")

    blockAudit()
    audit_inode_allocation()
    audit_directory_consistency()

    if(consistent == 1 or has_error ==False):
        exit(exit_consistent)

    exit(exit_inconsistent)

