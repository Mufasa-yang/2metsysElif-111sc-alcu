# NAME: Xiao Yang,Zhengyuan Liu
# EMAIL: avadayang@icloud.com,zhengyuanliu@ucla.edu
# ID: 104946787,604945064


.SILENT:

default:
	
	
build: default

clean:
	rm -f lab3b-104946787.tar.gz

dist: 
	tar -czf lab3b-104946787.tar.gz lab3b.py Makefile README
