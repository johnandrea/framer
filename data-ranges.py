#!/usr/local/bin/python3

# Arguments
# Input on stdin
# Output to stdout
#
# Show some info about one of the intermediate data files.
# number of records, time range, etc.

# Copyright John Andrea, 2019

import sys
import os
import re

# setup a few library files
dir_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append( dir_path + '/lib/')

from framer_util import get_header_key,get_command_options,read_framer_results

def output_as_table( total_key, data ):
    # find the longest word
    name_size = len( 'instrument' )
    for name in data:
        if len(name) > name_size:
           name_size = len(name)

    # the longest number ought to be the total
    num_size = len( 'records' )
    if len( str( data[total_key]['records'] ) ) > num_size:
       num_size = len( str( data[total_key]['records'] ) )

    # similarly for the dates
    date_size = len( 'max date' )
    for name in data:
        if len( data[name]['min'] ) > date_size:
           date_size = len( data[name]['min'] )
        if len( data[name]['max'] ) > date_size:
           date_size = len( data[name]['max'] )

    # make the format for the output, space filled parts
    line_format =   '% '  + str( name_size ) + 's'
    line_format += ' % '  + str( num_size )  + 's'
    line_format += ' % -' + str( date_size ) + 's'
    line_format += ' % -' + str( date_size ) + 's'

    # title
    print( line_format % ('instrument', 'records', 'min date', 'max date') )
    print( line_format % ('-'*name_size, '-'*num_size, '-'*date_size, '-'*date_size) )

    # save the total for last
    for name in sorted( data.keys() ):
        if name != total_key:
           print( line_format % (name, data[name]['records'], data[name]['min'], data[name]['max']) )

    name = total_key
    print( line_format % ('-'*name_size, '-'*num_size, '-'*date_size, '-'*date_size) )
    print( line_format % (name, data[name]['records'], data[name]['min'], data[name]['max']) )

options = get_command_options( 'none',
                               'Show ranges in a data file. Input on stdin. Output to stdout.' )

verbose  = int( options['verbose'] )

error,data = read_framer_results()
if error:
  print( error, file=sys.stderr )
  sys.exit( 1 )

results = dict()

results['total'] = dict()
results['total']['records'] = 0
results['total']['min'] = ''
results['total']['max'] = ''
total_first_time= True
total_sortable_min = ''
total_sortable_max = ''

for instrument in sorted( data.keys() ):
    if instrument == get_header_key():
       pass

    else:

       n_records = 0
       min_time  = ''
       max_time  = ''
       first_time= True

       sortable_min = ''
       sortable_max = ''

       for time in data[instrument]:
           n_records += 1

           # assume its a valid time
           # and turn it into something sortable

           # remove millisec, then non-numbers
           sortable_time = re.sub( r'\.\d+$', '', time ).replace(':','').replace('-','').replace(' ','')

           if first_time:
              first_time   = False
              sortable_min = sortable_time
              sortable_max = sortable_time
              min_time     = time
              max_time     = time

           else:
             if sortable_time < sortable_min:
                sortable_min = sortable_time
                min_time     = time
             if sortable_time > sortable_max:
                sortable_max = sortable_time
                max_time     = time

       results[instrument] = dict()
       results[instrument]['records'] = n_records
       results[instrument]['min']     = min_time
       results[instrument]['max']     = max_time

       results['total']['records'] += n_records
       if total_first_time:
          total_first_time   = False
          total_sortable_min = sortable_min
          total_sortable_max = sortable_max
          results['total']['min'] = min_time
          results['total']['max'] = max_time

       else:
         if sortable_min < total_sortable_min:
            total_sortable_min = sortable_min
            results['total']['min'] = min_time
         if sortable_max > total_sortable_max:
            total_sortable_max = sortable_max
            results['total']['max'] = max_time

output_as_table( 'total', results )
