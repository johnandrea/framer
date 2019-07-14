#!/usr/local/bin/python3

# Input on stdin
# Output to stdout
# Other options for configpath and packagefile

# Copyright John Andrea, 2019

import sys
import os
import json
import copy

# setup a few library files
dir_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append( dir_path + '/lib/')

from framer_util   import get_header_key,get_command_options,read_framer_results
from framer_config import get_configurations

def is_field_validated( log_this, frame_id, timestamp, field, value, validator ):
    ok = True

    for section in validator:
        if section['is_enabled']:

           op    = section['op']
           check = float( section['value'] )

           if op in ['=', '==']:
              ok = (value == check)
           elif op in ['!=', '<>']:
              ok = (value != check)
           elif op == '>':
              ok = ( value > check )
           elif op in ['>=', '=>']:
              ok = ( value >= check )
           elif op == '<':
              ok = ( value < check )
           elif op in ['<=', '=<']:
              ok = ( value <= check )

        if not ok:
           if log_this:
              print( frame_id, timestamp, field, 'Failed validity', value, file=sys.stderr )
           break

    return ok

options = get_command_options( 'validator',
                               'Remove values which fail verify rules. Input on stdin. Output to stdout.' )

packagefile= options['packagefile']
configpath = options['configpath']
verbose    = int( options['verbose'] )
enable_tests = options['enable tests']

log_it = verbose > 3

if not os.path.isfile( packagefile ):
   print( 'package file does not exist', file=sys.stderr )
   sys.exit( 1 )
if not os.path.isdir( configpath ):
   print( 'data file does not exist', file=sys.stderr )
   sys.exit( 1 )

error, configs = get_configurations( enable_tests, packagefile, configpath )

if error:
   print( error, file=sys.stderr )
   sys.exit( 1 )

error,data = read_framer_results()
if error:
  print( error, file=sys.stderr )
  sys.exit( 1 )

# either no verifying defined, or some of the instruments in the
# data don't have loaded configurations (which is ok)

n_validity = 0
for instrument in data.keys():
    if instrument in configs.keys():
       if configs[instrument]['enabled_field_validity']:
          n_validity += 1
       if configs[instrument]['enabled_duplicates_field_validity']:
          n_validity += 1

if n_validity < 1:
   # no work to do, input directly to output
   json.dump( data, sys.stdout, indent=1 )
   sys.exit( 0 )

header_key = get_header_key()
results    = dict()

for instrument in sorted( data.keys() ):
    if instrument == header_key:
       results[header_key] = copy.deepcopy( data[header_key] )
       # add metadata
       results[header_key]['field validation'] = True
       if 'operations' in results[instrument]:
          op = results[instrument]['operations']
          results[instrument]['operations'] = op + '/field validate'
       else:
          results[instrument]['operations'] = 'field validate'

    elif instrument not in configs:
       # if no config for a found instrument, then nothing to change
       results[instrument] = copy.deepcopy( data[instrument] )

    elif not ( configs[instrument]['enabled_field_validity'] or configs[instrument]['enabled_duplicates_field_validity'] ):
       # maybe none turned on
       results[instrument] = copy.deepcopy( data[instrument] )

    else:

       found_validation = 0
       fields_with_validation = dict()
       name_to_tag = dict()

       for tag in ['fields', 'duplicates']:
           for i in range( configs[instrument]['n_' + tag] ):
               if configs[instrument][tag][i]['enabled_validity']:
                  found_validation = True
                  name = configs[instrument][tag][i]['name']
                  fields_with_validation[name] = i
                  name_to_tag[name] = tag

       if not found_validation:
          # nothing to do
          results[instrument] = copy.deepcopy( data[instrument] )

       else:

          added_this_instrument = False

          for time in sorted( data[instrument].keys() ):
              added_this_time = False

              for name in data[instrument][time]:
                  value = data[instrument][time][name]

                  if name in fields_with_validation:
                     i = fields_with_validation[name]
                     tag = name_to_tag[name]
                     if not is_field_validated( log_it, instrument, time, name, float(value),
                                                configs[instrument][tag][i]['validity'] ):
                        value = None

                  if not added_this_instrument:
                     results[instrument] = dict()
                     added_this_instrument = True
                  if not added_this_time:
                     results[instrument][time] = dict()
                     added_this_time = True

                  # don't copy if its been erased

                  if value is not None:
                     results[instrument][time][name] = value

json.dump( results, sys.stdout, indent=1 )
