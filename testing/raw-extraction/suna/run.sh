#!/bin/bash

there=../../..

rm -f *.out *.log 2>/dev/null

$there/framer.py --verbose=99 suna.649.package suna.649.raw | tee frame.out |
$there/reduce-selection.py suna.649.package |
$there/viewer.py |
cat > out.out
