#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

'''
Copyright (c) 2020 JIIOV. All Rights Reserved

@File   : image2gif.py   
@Author : alexander.here@gmail.com 
@Date   : 2020-07-01 14:39 CST(+0800)   
@Brief  : generate GIF out of a serials of images

'''

import os, sys
import glob
import numpy as np
import cv2
import imageio

TITLE_HEIGHT = 12
TITLE_SCALE = 0.4

def prompt( msg, default) :
    if sys.version_info.major <= 2:
        result = raw_input( msg + " [Y/n]" if default else " [y/N]")
    else:
        result = input( msg + " [Y/n]" if default else " [y/N]")
    if len( result) <= 0 :
        return default
    elif result.lower().startswith( "y") :
        return True
    elif result.lower().startswith( "n") :
        return False
    else :
        return prompt( msg, default)

def load_images( files, title = 'none'):
    result = []
    for idx, path in enumerate( files):
        print( '[%2d%%] %s ...' % ( idx * 100 / len( files), path))
        with open( path, 'rb') as inf: # use open() so we can read from pipes
            data = np.frombuffer( inf.read(), dtype = np.uint8)
            raw = cv2.imdecode( data, cv2.IMREAD_UNCHANGED)
            if raw is None:
                print( "WARNING: failed decoding image '%s', skipped!" % ( path), file = sys.stderr)
                continue
            # convert to rgb:
            if len( raw.shape) <= 2 or raw.shape[ 2] <= 2:
                raw = cv2.cvtColor( raw, cv2.COLOR_GRAY2RGB)
            elif raw.shape[ 2] == 4:
                raw = cv2.cvtColor( raw, cv2.COLOR_BGRA2RGB)
            else:
                raw = cv2.cvtColor( raw, cv2.COLOR_BGR2RGB)
        if title != 'none':
            title_mat = np.zeros( ( TITLE_HEIGHT + 4, raw.shape[ 1], 3), dtype = np.uint8)
            if title == 'name':
                title_text = os.path.basename( path)
            elif title == 'path':
                title_text = path
            elif title == 'abspath':
                title_text = os.path.abspath( path)
            else:
                title_text = ''
            cv2.putText( title_mat, title_text, ( 0, TITLE_HEIGHT), cv2.FONT_HERSHEY_SIMPLEX, TITLE_SCALE, [ 65535, 65535, 65535])
            raw = np.vstack( ( raw, title_mat))
        result.append( raw)

    return result

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument( '-o', '--output', type = str, default = 'output.gif', help = 'path to save spectrum image.')
    parser.add_argument( '-f', '--force', action = 'store_true', help = 'force to rewrite existing file(s)')
    parser.add_argument( '-k', '--keep-order', action = 'store_true', help = 'do NOT sort images by their path')
    parser.add_argument( '-t', '--title', choices = [ 'none', 'name', 'path', 'abspath'], default = 'none', help = 'type of title add to each frame')
    parser.add_argument( '-r', '--framerate', type = float, default = 1.0, help = 'how many images per sencond')
    args, files = parser.parse_known_args( sys.argv[ 1:])
    try :
        files.remove( '--')
    except:
        pass

    if os.name != 'posix':
        expanded_files = []
        for raw_path in files:
            if '*' in raw_path:
                expanded_files += glob.glob( raw_path)
            else:
                expanded_files.append( raw_path)
        files = expanded_files
    
    if not args.keep_order:
        files.sort()
    
    images = load_images( files, args.title)
    if os.path.isfile( args.output) \
            and not args.force \
            and not prompt( "File '" + args.output + "' already exists, overwrite?", True):
        print( 'Canceled.', file = sys.stderr)
        exit( 1)
    print( "saving '" + args.output + "' ...")
    folder = os.path.dirname( args.output)
    if len( folder) > 0:
        os.makedirs( os.path.dirname( args.output), exist_ok = True)
    imageio.mimsave( args.output, images, 'GIF', duration = 1/args.framerate)


# End of 'image2gif.py' 

