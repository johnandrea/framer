#!/bin/bash

there=../../..

rm -f *.out 2>/dev/null

data=one.frame

$there/framer.py --verbose=9 package $data |
cat > frame.out
