#!/bin/bash

there=../../..

rm *.out 2>/dev/null

echo ocr binary
$there/framer.py ocr.package ocr-short.frame  |tee f.out | $there/viewer.py

echo 3x1m ascii
$there/framer.py 3x1m.package 3x1m-short.frame |tee f.out | $there/viewer.py
