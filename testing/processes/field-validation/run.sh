#!/bin/bash

there=../../..

$there/framer.py --verbose=99 package modem.raw | tee enabled.out |
$there/validator.py --verbose=3 package | tee val.out |
$there/reduce-selection.py package |
$there/viewer.py > out.out

$there/data-stats.py < val.out
