# NAME: Xiao Yang,Zhengyuan Liu
# EMAIL: avadayang@icloud.com,zhengyuanliu@ucla.edu
# ID: 104946787,604945064


.SILENT:

default:
	echo "#!/bin/bash" > lab3b
	echo 'python lab3b.py $$1' >> lab3b
	chmod a+x lab3b
	
build: default

clean:
	rm -f lab3b-104946787.tar.gz lab3b

dist: 
	tar -czf lab3b-104946787.tar.gz lab3b.py Makefile README
