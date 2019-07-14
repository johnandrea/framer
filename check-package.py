#!/usr/local/bin/python3

# Arguments:
# 1 name of package file
# 2 configpath option
# Output:
# error code and messages to stderr

# Copyright John Andrea, 2019

import sys
import os

# setup a few library files
dir_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append( dir_path + '/lib/')

from framer_util   import get_command_options
from framer_config import get_configurations

options = get_command_options( 'check package',
                               'Check validity of package and configs.' )

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
