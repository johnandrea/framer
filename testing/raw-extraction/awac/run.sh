#!/bin/bash

there=../../..

rm -f out.out 2>/dev/null

$there/framer.py all.package awac.frame |
$there/reduce-selection.py all.package |
$there/viewer.py > out.out
