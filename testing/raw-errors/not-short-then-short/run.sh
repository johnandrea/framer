#!/bin/bash

there=../../..

rm -f *out 2>/dev/null

$there/framer.py --verbose=6 storx.package test.raw | tee framer.out |
$there/reduce-selection.py storx.package |
$there/viewer.py > out.out

echo
echo expecting frames: 2 storx, one too short
echo
cat out.out
