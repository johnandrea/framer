#!/bin/bash

exe=../../../data-join.py

rm -f *out 2>/dev/null
rm -f 1.replaced 2>/dev/null

cat test.1.dat | $exe test.2.dat | $exe test.3.dat > 1-2-3.out

cat test.1.dat | $exe test.update1.dat > 1.replaced
