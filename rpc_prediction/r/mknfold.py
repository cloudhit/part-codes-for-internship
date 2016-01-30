#!/usr/bin/env python
import sys
import random

if len(sys.argv) < 2:
    print ('Usage:<filename> <k> [nfold = 5]')
    exit(0)

random.seed( 10 )

k = int( sys.argv[2] )
if len(sys.argv) > 3:
    nfold = int( sys.argv[3] )
else:
    nfold = 5

fi = open( sys.argv[1], 'r' )
fiw = open(sys.argv[1] + '.weight', 'r')
ftw = open( sys.argv[1] + '.train.weight', 'w')
ftr = open( sys.argv[1]+'.train', 'w' )
fte = open( sys.argv[1]+'.test', 'w' )
few = open(sys.argv[1] + '.test.weight', 'w')
for l in fi:
    w = fiw.readline()
    if random.randint( 1 , nfold ) == k:
        fte.write( l )
        few.write(w)
    else:
        ftr.write( l )
        ftw.write(w)
fi.close()
ftr.close()
fte.close()
ftw.close()
fiw.close()
few.close()