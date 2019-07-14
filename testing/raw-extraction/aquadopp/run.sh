#!/bin/bash

there=../../..

rm -f *.out 2>/dev/null

$there/framer.py --verbose=99 package adcp.frame |
cat > frame.out

cat frame.out |
$there/reduce-selection.py package |
$there/fitter.py package |
cat > fit.out

cat fit.out |
$there/viewer.py > out.out

