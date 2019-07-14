#!/bin/bash

there=../../..

data=37sm.frame

strings $data

rm *.out 2>/dev/null

if $there/framer.py --verbose=99 package $data > frame.out
then
  echo past framer
  if cat frame.out | $there/fitter.py package > fit.out
  then
     echo past fitter
     if cat fit.out | $there/viewer.py > out.out
     then
       echo past viewer, out.out
     fi
  fi
fi
