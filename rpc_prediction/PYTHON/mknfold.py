#!/usr/bin/python
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
for l in fi:
    w = fiw.readline()
    if random.randint( 1 , nfold ) == k:
        fte.write( l )
    else:
        ftr.write( l )
        ftw.write(w)
fi.close()
ftr.close()
fte.close()
ftw.close()
fiw.close()

struct EvalWRMSE : public EvalEWiseBase<EvalWRMSE> {
  virtual const char *Name(void) const {
    return "rmse";
  }
  inline static float EvalRow(float label, float pred) {
    float diff = label - pred;
    return diff * diff;
  }
  inline static float GetFinal(float esum, float wsum) {
    return std::sqrt(esum / wsum);
  }
};

