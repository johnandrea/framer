#!/bin/bash

there=../../../..

rm -f *out 2>/dev/null

$there/framer.py --verbose=5 test.pack test.dat | tee framer.out |
$there/viewer.py > out.out

echo
echo
cat out.out

echo
echo the second instrument should be extracted because the
echo surrounding one doesnt have enough fields
echo
