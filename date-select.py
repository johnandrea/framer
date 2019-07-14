#!/usr/local/bin/python3

# Arguments
# --mindate = "yyyy-mm-dd", default 1900-01-01
# --maxdate   = "yyyy-mm-dd", default 2999-01-01
# Input on stdin
# Output to stdout
#
# Output a file with the dates within the specified range

# Copyright John Andrea, 2019

import sys
import os
import json
import copy

# setup a few library files
dir_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append( dir_path + '/lib/')

from framer_util import get_header_key,get_command_options,read_framer_results,string_looks_like_time
from framer_config import is_valid_timestamp_string

def date_is_ok( title, date ):
    error = ''

    # do the testing with the time added
    time = date + ' 00:00:00'

    if string_looks_like_time( time ):
       if not is_valid_timestamp_string( time ):
          error += title + ' date is not a valid date.\n'
    else:
       error += title + ' date does not appear to be a date YYYY-MM-DD.'
       error += ' Note that only dates should be specified, without time.\n'

    return error

options = get_command_options( 'date-select',
                               'Exclude data outside the specified range. Input on stdin. Output to stdout.' )

min_date = options['mindate']
max_date = options['maxdate']
verbose  = int( options['verbose'] )

error = ''

error += date_is_ok( 'Minimum', min_date )
error += date_is_ok( 'Maximum', max_date )
if error:
  print( error, file=sys.stderr )
  sys.exit( 1 )
else:
  if min_date > max_date:
     print( 'Min date greater than max date', file=sys.stderr )
     sys.exit( 1 )

error,data = read_framer_results()
if error:
  print( error, file=sys.stderr )
  sys.exit( 1 )

header_key = get_header_key()

# make a new file

results = dict()

for instrument in sorted( data.keys() ):
    if instrument == header_key:
       results[instrument] = copy.deepcopy( data[instrument] )
       results[instrument]['date select'] = True
       results[instrument]['min date'] = min_date
       results[instrument]['max date'] = max_date
       if 'operations' in results[instrument]:
          op = results[instrument]['operations']
          results[instrument]['operations'] = op + '/date-select'
       else:
          results[instrument]['operations'] = 'date-select'

    else:

       instrument_not_yet_added = True

       for time in data[instrument]:
           # get just the date section from yyyy-mm-dd hh:mm:ss[:mm]
           # assuming that this is a properly formatted date
           date = time.strip().split()[0]

           if min_date <= date <= max_date:
              if instrument_not_yet_added:
                 results[instrument] = dict()
                 instrument_not_yet_added = False

              results[instrument][time] = copy.deepcopy( data[instrument][time] )

json.dump( results, sys.stdout, indent=1 )
