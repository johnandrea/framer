#!/bin/bash

there=../../../..

rm -f *out 2>/dev/null

$there/framer.py --verbose=5 package ../1ok-2wrongcheck-3badstatus-4badcheck.raw | tee frame.out |
$there/reduce-selection.py package |
$there/viewer.py > out.out

cat out.out
