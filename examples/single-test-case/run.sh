#!/bin/bash

there=../..

rm -f *out 2>/dev/null

if $there/check-package.py package.list
then
   if $there/framer.py package.list data.raw > frames.out
   then

      cat frames.out |
      $there/fitter.py package.list |
      $there/validator.py package.list |
      $there/reduce-selection.py package.list |
      $there/averager.py > averaged.out

      cat averaged.out |
      $there/viewer.py > out.out

      cat averaged.out |
      $there/data-ranges.py > ranges.out

      cat averaged.out |
      $there/data-stats.py > stats.out

      ls *.out

   else
      echo
      echo framer failed
      exit 1
   fi
else
  echo
  echo configuration check failed
  exit 1
fi
