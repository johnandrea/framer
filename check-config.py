#!/usr/local/bin/python3

# Arguments:
# 1 name of config file, full path
# Output:
# error code and messages to stderr

# Copyright John Andrea, 2019

import sys
import os
import json
#from pprint import pprint

# setup a few library files
dir_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append( dir_path + '/lib/')

from framer_util   import get_command_options
from framer_config import specific_lower_and_trim,get_changable_config_keys,config_file_verify

options = get_command_options( 'check config',
                               'Check validity of a single config file.' )

file    = options['configfile']
verbose = int( options['verbose'] )

if not os.path.isfile( file ):
   print( 'Config file does not exist:' + file, file=sys.stderr )
   sys.exit( 1 )

try:
   with open( file ) as f:
        json_contents = json.load( f )
except:
   print( 'Error loading config file. Is it valid JSON:' + file, file=sys.stderr )
   sys.exit( 1 )

config = specific_lower_and_trim( get_changable_config_keys(), '', json_contents )

error = config_file_verify( config )

if error != '':
   print( error, file=sys.stderr )
   sys.exit( 1 )
