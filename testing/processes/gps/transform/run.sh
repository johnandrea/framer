#!/bin/bash

there=../../../..

$there/framer.py --verbose=99 package ../1ok-2wrongcheck-3badstatus-4badcheck.raw |tee frame.out |
$there/reduce-selection.py package |
$there/viewer.py > out.out

cat out.out
