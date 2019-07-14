#!/bin/bash

there=../../..

rm -f *.out *.log 2>/dev/null

$there/framer.py --verbose=99 suna.649.package suna.649.raw 2>verbose.log | tee frame.out |
$there/reduce-selection.py suna.649.package |tee reduce.out |
$there/averager.py |
$there/fitter.py suna.649.package |
$there/validator.py suna.649.package |
$there/viewer.py > out.out

cat out.out
