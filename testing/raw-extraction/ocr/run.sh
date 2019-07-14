#!/bin/bash

there=../../..

rm *.out 2>/dev/null

$there/framer.py --verbose=99 package ocr.frame |tee framer.out|
$there/reduce-selection.py package > reduce.out

cat reduce.out |
$there/fitter.py package |
cat > fit.out

cat fit.out |
$there/viewer.py > out.out

