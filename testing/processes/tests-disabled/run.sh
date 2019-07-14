#!/bin/bash

there=../../..

echo enabled

$there/framer.py package modem.raw | tee enabled.data.out |
$there/viewer.py > enabled.out
$there/data-stats.py < enabled.data.out

echo
echo disabled

$there/framer.py --enable-tests=no package modem.raw | tee disabled.data.out |
$there/viewer.py > disabled.out
$there/data-stats.py < disabled.data.out

