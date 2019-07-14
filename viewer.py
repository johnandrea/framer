#!/usr/local/bin/python3

# Arguments none
# Input on stdin
# Output to stdout

# Copyright John Andrea, 2019

import sys
import os

# setup a few library files
dir_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append( dir_path + '/lib/')

from framer_util import get_header_key,get_command_options,read_framer_results,get_final_float_format

options = get_command_options( 'viewer',
                               'View output from framer. Input on stdin. Output to stdout as tsv.' )

verbose = int( options['verbose'] )

is_separate_style = ( options['style'].lower().strip() != 'combined' )

error,data = read_framer_results()
if error:
  print( error, file=sys.stderr )
  sys.exit( 1 )

# the output will be tab separated
# get all the timestamps to be sorted that way
# all the field names
# all the instruments

field_names = dict()
times       = dict()
instruments = dict()

# if there is an error while handling the data, just let it go
# because this data format should be well defined
# and not going to strip the strings either

for instrument in data:
    # skip this metadata item
    if instrument == get_header_key(): continue

    instruments[instrument] = True

    for time in data[instrument]:
        times[time] = True

        for field in data[instrument][time]:
            field_names[field] = True

# make sorted arrays out of those unique keys
sorted_field_names = []
sorted_times       = []
sorted_instruments = []

for item in sorted( field_names.keys() ):
    sorted_field_names.append( item )
for item in sorted( times.keys() ):
    sorted_times.append( item )
for item in sorted( instruments.keys() ):
    sorted_instruments.append( item )

header = 'time'
if is_separate_style:
   # need to show each instrument
   header += '\t'
   header += 'instrument'

n_fields = 0
header_names = dict()
for field in sorted_field_names:
    n_fields += 1
    header += '\t'
    header += field
    # zero is always time
    header_names[field] = n_fields

print( header )

out_format = get_final_float_format()

# multiple loops, but with all the data in memory it should be quick

if is_separate_style:
   for time in sorted_times:
       # at least one instrument had this time
       for instrument in sorted_instruments:
           for record_time in data[instrument]:
               if time == record_time:
                  output = time + '\t' + instrument

                  for field in sorted_field_names:
                      output += '\t'
                      if field in data[instrument][time]:
                         value = data[instrument][time][field]

                         # for better speed, do the test for a number here rather than calling another function
                         try:
                            output += (out_format) % (float(data[instrument][time][field]))
                         except ValueError:
                            output += data[instrument][time][field]

                  print( output )

else:
   # not separate by instrument

   for time in sorted_times:
       output = []
       for i in range( n_fields + 1):
           output.append( '' )

       output[0] = time

       # at least one instrument had this time
       for instrument in sorted_instruments:
           for record_time in data[instrument]:
               if time == record_time:
                  for field in sorted_field_names:
                      pos = header_names[field]
                      if field in data[instrument][time]:
                         value = data[instrument][time][field]

                         # for better speed, do the test for a number here rather than calling another function
                         try:
                            output[pos] = (out_format) % (float(data[instrument][time][field]))
                         except ValueError:
                            output[pos] = data[instrument][time][field]

       tab = ''
       out_line = ''
       for i in range( n_fields + 1 ):
           out_line += tab + output[i]
           tab = '\t'
       print( out_line )
