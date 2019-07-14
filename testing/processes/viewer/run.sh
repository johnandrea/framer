#!/bin/bash

there=../../..

cat frame.dat | $there/viewer.py | tee combine.out | tr '\t' '@' > combine.tab.out
