#!/usr/local/bin/python3

# Arguments
# An input file on stdin, optional.
# A set of filenames on the command line, optional.
# Output to stdout
#
# Copyright John Andrea, 2019

import sys
import os
import json
import copy

# setup a few library files
dir_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append( dir_path + '/lib/')

from framer_util import get_command_options,get_header_key,read_framer_results_from_file,read_framer_results_allow_empty_stdin

options = get_command_options( 'multi-files',
                               'Join data files. Input on stdin and/or command line. Output to stdout.' )

verbose = int( options['verbose'] )
files   = options['files']

header_key = get_header_key()

# treat the file from stdin as rhe first file

error,data = read_framer_results_allow_empty_stdin()
if error:
  print( error, file=sys.stderr )
  sys.exit( 1 )

# get the others which might occur on the command line

if sys.argv:
   #for i, name in enumerate( sys.argv ):
   #    if i == 0: continue
   for name in files:
       # if the input file does not exist, skip it
       if os.path.isfile( name ):
          error,moredata = read_framer_results_from_file( name )
          if error:
             print( error, file=sys.stderr )
             sys.exit( 1 )

          if not data:
             data = copy.deepcopy( moredata )

          else:
             # use of built-in "update" function will not work as it
             # replaces values with matching keys, so whole sub-dicts go away

             # the same problem may occur with deepcopy to attempt to merge
             # the whole thing

             for instrument in moredata:
                 if instrument == header_key:
                    strings = 'strings'
                    if strings in moredata[header_key]:
                       if strings in data[header_key]:
                          for item in moredata[header_key][strings]:
                              if item in data[header_key][strings]:
                                 for value in moredata[header_key][strings][item]:
                                     if value not in data[header_key][strings][item]:
                                        data[header_key][strings][item].append( value )
                              else:
                                 data[header_key][strings][item] = copy.deepcopy( moredata[header_key][strings][item] )
                       else:
                          data[header_key][strings] = copy.deepcopy( moredata[header_key][strings] )

                 else:
                    if instrument in data:
                       for time in moredata[instrument]:
                           if time in data[instrument]:
                              for field in moredata[instrument][time]:
                                  if field not in data[instrument][time]:
                                     data[instrument][time][field] = moredata[instrument][time][field]
                           else:
                              data[instrument][time] = copy.deepcopy( moredata[instrument][time] )
                    else:
                       data[instrument] = copy.deepcopy( moredata[instrument] )

json.dump( data, sys.stdout, indent=1 )
