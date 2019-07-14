#!/bin/bash

for name in *.conf
do
  echo $name
  ../../check-config.py $name
done
