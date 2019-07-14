#!/bin/bash

there=../../../..

rm -f *out 2>/dev/null


$there/framer.py --verbose=5 test.pack test.dat | tee framer.out |
$there/viewer.py > out.out

echo
echo
cut -f2,7,8,9 out.out | sed 's/instrument/instr/'

echo
echo the second instrument should not have been extracted
echo
