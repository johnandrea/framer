#!/usr/local/bin/python3

# Arguments
# --interval = minutes to average, default 4
# Input on stdin
# Output to stdout
#
# Given a framer output file and config files,
# spit out a new file with fields averaged to the given time interval.
#
# The interval specifies how an hour is broken into averaging bins.
#   The given interval is either less than 1, meaning no averaging,
# or up to 60. Where 60 or more means average over a whole hour.
#   Intervals from 31 to 59 are possible but probably not useful.
#
# For example, an interval of 15 has bins of minutes of
#  0 to 14,  15 to 29,  30 to 44, and 45 to 59

# Copyright John Andrea, 2019

import sys
import os
import json
import copy

# setup a few library files
dir_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append( dir_path + '/lib/')

from framer_util import get_header_key,get_command_options,read_framer_results,field_is_a_string,get_float_format,is_number

def precompute_every_minute( interval ):
    # pre-compute the minute to which any minute will snap as a lookup table
    # based on the given snapping interval
    # the results are actually strings for appending to an hour string
    #
    # assuming interval is >=1

    lookup = []

    if interval == 1:
       # each minute, 0->00, 1->01, 2->02, .. 59->59
       for i in range(60):
          lookup.append( '%02d' % (i) )

    elif interval > 59:
       # hourly, everything to zero
       for i in range(60):
          lookup.append( '00' )

    else:
       # each minute set to fit withing previous interval
       # i.e. if interval = 20
       #  0 to 19 -> 00, 20 to 39 -> 20, 40 to 59 -> 40

       # initialize zero to prevent the modulus being off by 1
       lookup.append( '00' )

       prev = 0
       for i in range(1,60):
          if i % interval == 0:
             prev += interval
          lookup.append( '%02d' % (prev) )

    return lookup

options = get_command_options( 'average',
                               'Average over selected interval. Input on stdin. Output to stdout.' )

interval = options['interval']
verbose  = int( options['verbose'] )

error,data = read_framer_results()
if error:
  print( error, file=sys.stderr )
  sys.exit( 1 )

if interval < 1:
   # no work to do, output = input
   json.dump( data, sys.stdout, indent=1 )
   sys.exit( 0 )

minute_to_snap = precompute_every_minute( interval )

out_format = get_float_format()

# average the data one instrument at a time

header_key = get_header_key()
results    = dict()

for instrument in sorted( data.keys() ):
    if instrument == header_key:
       results[instrument] = copy.deepcopy( data[instrument] )
       results[instrument]['averaged'] = True
       results[instrument]['averaged interval'] = interval
       if 'operations' in results[instrument]:
          op = results[instrument]['operations']
          results[instrument]['operations'] = op + '/averaged'
       else:
          results[instrument]['operations'] = 'averaged'

    else:

       field_names = dict()

       # all the times for this instrument

       old_time_to_new = dict()
       new_times       = dict()
       for time in data[instrument]:
           # assume its a valid time
           datetime = time.split()
           hms      = datetime[1].split( ':' )
           new_time = '%s %s:%s:00' % (datetime[0], hms[0], minute_to_snap[int( hms[1] )] )

           new_times[new_time]   = True
           old_time_to_new[time] = new_time

           # collect every field for this instrument
           # but skip the strings
           #
           # ok, times with only string types will have zero outputs
           # and will not be output

           for field in data[instrument][time]:
               if not field_is_a_string( instrument, field, data[header_key] ):
                  field_names[field] = True

       results[instrument] = dict()

       # might as well sort times too

       for new_time in sorted( new_times.keys() ):
           # save every field at this time

           n    = dict()
           sums = dict()

           for field in field_names:
               n[field]   = 0
               sums[field] = 0

           found_some = False

           for old_time in data[instrument]:
               if new_time == old_time_to_new[old_time]:

                  for field in field_names:
                      if field in data[instrument][old_time]:
                         value = data[instrument][old_time][field]
                         # allow for zero
                         if (value is not None) and is_number( value ):
                            found_some = True
                            n[field]    += 1
                            sums[field] += float( value )

           if found_some:
              results[instrument][new_time] = dict()
              for field in field_names:
                  # don't do the math, or do it, or do nothing
                  if n[field] == 1:
                     results[instrument][new_time][field] = sums[field]
                  elif n[field] > 1:
                     results[instrument][new_time][field] = out_format % ( sums[field]/n[field] )

json.dump( results, sys.stdout, indent=1 )
