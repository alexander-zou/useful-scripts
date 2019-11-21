#!/usr/bin/env python3

'''

@File   : json_prettier.py   
@Author : zoujiachen@megvii.com   
@Date   : 2019-11-21 13:56   
@Brief  :  

'''

import sys
import json
import argparse

parser = argparse.ArgumentParser()
parser.add_argument( '-i', '--indent', type = int, default = 4,
                        help = 'indent level when printing')
parser.add_argument( '-k', '--sort-keys', action="store_true",
                        help = 'if given, dictionaries will be sorted by key')
args = parser.parse_args()
sort_keys = True if args.sort_keys else False

data = json.load( sys.stdin)
json.dump( data, sys.stdout, indent=args.indent, sort_keys=sort_keys)
print()


# End of 'json_prettier.py' 

