#!/usr/local/bin/python3

# Arguments
# Input on stdin
# Output to stdout
#
# Show some stats about one of the intermediate data files.
# number of records, min,max,median,stddev

# Copyright John Andrea, 2019

import sys
import os
from math import sqrt

# setup a few library files
dir_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append( dir_path + '/lib/')

from framer_util import get_header_key,get_final_float_format,get_command_options,read_framer_results,field_is_a_string

def len_of_int( value ):
    return len( str( value ) )

def len_of_num( float_format, value ):
    return len( float_format % (value ) )

def output_as_table( float_format, data ):
    pre_stats = ['instrument', 'field', 'records']
    stats     = ['min', 'max', 'mean', 'std dev']

    # find the longest instrument
    # and the longest field name
    # etc

    sizes = dict()
    for item in pre_stats:
        sizes[item] = len( item )
    for item in stats:
        sizes[item] = len( item )

    for instrument in data:
        sizes['instrument'] = max( sizes['instrument'], len(instrument) )

        for field in data[instrument]:
            sizes['field']   = max( sizes['field'], len(field) )
            sizes['records'] = max( sizes['records'], len_of_int(data[instrument][field]['n']) )

            for item in stats:
                sizes[item] = max( sizes[item], len_of_num(float_format, data[instrument][field][item]) )

    # make the format for the output, space filled parts
    out_format = dict()
    space = ''
    for item in pre_stats:
        out_format[item] = space + '% ' + str( sizes[item] ) + 's'
        space = ' ' #add spaces after the first item
    for item in stats:
        out_format[item] = space + '% ' + str( sizes[item] ) + 's'

    # title
    output = ''
    for item in pre_stats:
        output += out_format[item] % (item)
    for item in stats:
        output += out_format[item] % (item)
    print( output )

    # bar under the column names
    output = ''
    for item in pre_stats:
        output += out_format[item] % ( '-' * sizes[item] )
    for item in stats:
        output += out_format[item] % ( '-' * sizes[item] )
    print( output )

    for instrument in sorted( data.keys() ):
        for field in sorted( data[instrument].keys() ):
            output = out_format['instrument'] % (instrument)
            output += out_format['field'] % (field)
            output += out_format['records'] % (str(data[instrument][field]['n']))
            for item in stats:
                # format with precision, then set the string into the column width
                output += out_format[item] % (float_format % (data[instrument][field][item]))

            print( output )


options = get_command_options( 'none',
                               'Show stats of a data file. Input on stdin. Output to stdout.' )

verbose  = int( options['verbose'] )

error,data = read_framer_results()
if error:
  print( error, file=sys.stderr )
  sys.exit( 1 )

results    = dict()
header_key = get_header_key()

for instrument in data:
    if instrument == header_key:
       pass

    else:

       results[instrument] = dict()

       for time in data[instrument]:
           for field in data[instrument][time]:
               if not field_is_a_string( instrument, field, data[header_key] ):

                  value = float( data[instrument][time][field] )

                  if field in results[instrument]:
                     results[instrument][field]['n']   += 1
                     results[instrument][field]['sum'] += value
                     results[instrument][field]['min'] = min( value, results[instrument][field]['min'] )
                     results[instrument][field]['max'] = max( value, results[instrument][field]['max'] )
                  else:
                     results[instrument][field] = dict()
                     results[instrument][field]['n']   = 1
                     results[instrument][field]['sum'] = value
                     results[instrument][field]['min'] = value
                     results[instrument][field]['max'] = value

# prepare for 2 step std dev, hoping that values don't overflow
for instrument in results:
    for field in results[instrument]:
        total = results[instrument][field]['sum']
        n     = results[instrument][field]['n']
        results[instrument][field]['mean'] = total / float(n)
        results[instrument][field]['dev_sq'] = 0.0
for instrument in results:
    for time in data[instrument]:
        # check the field in the data because the loop is over the time items
        for field in data[instrument][time]:
            if not field_is_a_string( instrument, field, data[header_key] ):
               value  = float( data[instrument][time][field] )
               mean   = results[instrument][field]['mean']
               results[instrument][field]['dev_sq'] += ( value - mean ) * ( value - mean )
for instrument in results:
    for field in results[instrument]:
        n      = results[instrument][field]['n']
        dev_sq = results[instrument][field]['dev_sq']
        results[instrument][field]['std dev'] = sqrt( dev_sq / float(n) )

output_as_table( get_final_float_format(), results )
