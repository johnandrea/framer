#!/bin/bash

there=../../..

rm -f *.out 2>/dev/null

$there/framer.py --verbose=99 package eco.frame |tee framer.out|
$there/reduce-selection.py package |
$there/viewer.py > out.out
