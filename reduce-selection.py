#!/usr/local/bin/python3

# Input on stdin
# Output to stdout
# Other options for configpath and packagefile

# Copyright John Andrea, 2019

import sys
import os
import json
import copy
from pprint import pprint

# setup a few library files
dir_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append( dir_path + '/lib/')

from framer_util   import get_header_key,get_command_options,read_framer_results
from framer_config import get_configurations

options = get_command_options( 'filter',
                               'Output only the selected set of instrument/sensors. Input on stdin. Output to stdout.' )

packagefile= options['packagefile']
configpath = options['configpath']
verbose    = int( options['verbose'] )

if not os.path.isfile( packagefile ):
   print( 'package file does not exist', file=sys.stderr )
   sys.exit( 1 )
if not os.path.isdir( configpath ):
   print( 'data file does not exist', file=sys.stderr )
   sys.exit( 1 )

error, configs = get_configurations( True, packagefile, configpath )

if error:
   print( error, file=sys.stderr )
   sys.exit( 1 )

if verbose >= 90:
    with open( 'reduce-selection.log', "w" ) as v:
         pprint( configs, v )

error,data = read_framer_results()
if error:
  print( error, file=sys.stderr )
  sys.exit( 1 )

header_key = get_header_key()
results    = dict()

for instrument in sorted( data.keys() ):
    if instrument == header_key:
       results[instrument] = copy.deepcopy( data[instrument] )
       # add metadata
       results[instrument]['reduced'] = True
       if 'operations' in results[instrument]:
          op = results[instrument]['operations']
          results[instrument]['operations'] = op + '/reduced'
       else:
          results[instrument]['operations'] = 'reduced'

    elif instrument not in configs:
       # in the data, but no config => don't save it
       continue

    elif configs[instrument]['has_reportable_fields']:

       fields_reportable = dict()

       for tag in ['fields', 'constants', 'duplicates']:
           for i in range( configs[instrument]['n_' + tag] ):
               if configs[instrument][tag][i]['is_reportable']:
                  fields_reportable[configs[instrument][tag][i]['name']] = i

       results[instrument] = dict()

       for time in data[instrument]:
           results[instrument][time] = dict()

           for field in data[instrument][time]:
               if field in fields_reportable:
                  results[instrument][time][field] = data[instrument][time][field]

# there could be an info:strings item for an instrument which no longer has
# any data, so remove that key
# need to store them for after the search loop
remove_frames = []
if 'strings' in results[header_key]:
   for frame_id in results[header_key]['strings']:
       if frame_id not in configs:
          remove_frames.append( frame_id )
for frame_id in remove_frames:
    del results[header_key]['strings'][frame_id]

json.dump( results, sys.stdout, indent=1 )
