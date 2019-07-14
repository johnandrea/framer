#!/bin/bash

there=../../..

data=data.raw

rm -f *.out 2>/dev/null

$there/framer.py --verbose=99 package $data > frame.out

cat frame.out | $there/fitter.py package > fit.out

cat fit.out | $there/averager.py --interval=5> ave.out

cat ave.out | $there/viewer.py > out.out
