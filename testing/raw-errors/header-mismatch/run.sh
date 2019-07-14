#!/bin/bash

there=../../..

rm -f *out 2>/dev/null

$there/framer.py --verbose=6 3.package aquadopp-vs-seafet.raw | tee framer.out |
$there/reduce-selection.py 3.package |
$there/viewer.py > out.out

echo
echo expecting frames: 1 storx, 1 seafet, then 1 storx
echo
cat out.out
