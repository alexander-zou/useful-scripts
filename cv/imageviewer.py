#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

'''

@File   : imageviewer.py   
@Author : alexander.here@gmail.com
@Date   : 2020-03-09 11:10 CST(+0800)   
@Brief  :  

'''

import os
import sys
import argparse
import numpy as np
import cv2 as cv

ERR_ARGS = 1
ERR_SYS = 2
ERR_DATA = 3
ERR_INTERAL = 4

DESC_STR = "Show image(s) within terminal."
USAGE_STR = "imageviewer.py [-h] [-i] [-f FORMAT] [-c COL] [-r ROW] [-s SCALE]" + \
            " [--] [FILE ...] [DIR ...]"

MODE_AUTO = 0
MODE_FIXED_WIDTH = 1
MODE_FIXED_HEIGHT = 2
MODE_FIXED_RESOLUTION = 3
MODE_SCALING = 4
MODE_INTERACTIVE = 5

# UPPER(R,G,B), LOWER(R,G,B):
PIXEL_FMT = u'\033[48;2;%d;%d;%dm\033[38;2;%d;%d;%dm\u2584\033[0m'
CHECKERED_PATTERN = ( 196, 156)

def is_picture_suffix( str):
    str = str.upper()
    for suffix in ( '.JPG', '.JPEG', '.GIF', '.BMP', '.PNG', '.TIF', '.TIFF'):
        if str.endswith( suffix):
            return True
    return False

def load_bgra( path):
    with open( path, 'rb') as inf:
        data = np.frombuffer( inf.read(), dtype = np.uint8)
    mat = cv.imdecode( data, cv.IMREAD_UNCHANGED)
    height = int( mat.shape[ 0])
    width = int( mat.shape[ 1])

    if mat.dtype == np.uint8:
        pass
    elif mat.dtype == np.uint16:
        mat = ( mat / 256.0 + 0.5).astype( np.uint8)
    elif mat.dtype == np.float32:
        mat = ( mat * 255 + 0.5).astype( np.uint8)
    else:
        raise Exception( 'unsupported data type: ' + str( mat.dtype))

    try:
        channel = int( mat.shape[ 2])
    except:
        channel = 1

    if channel == 1:
        y = mat
        a = np.full( ( height, width), 255, dtype = np.uint8)
        return cv.merge( ( y, y, y, a))
    elif channel == 2:
        y = mat[ :, :, 0]
        a = mat[ :, :, 1]
        return cv.merge( ( y, y, y, a))
    elif channel == 3:
        b = mat[ :, :, 0]
        g = mat[ :, :, 1]
        r = mat[ :, :, 2]
        a = np.full( ( height, width), 255, dtype = np.uint8)
        return cv.merge( ( b, g, r, a))
    elif channel == 4:
        return mat
    else:
        raise Exception( 'unsupported channels count: %d' % ( channel))

def render_checkered_pattern( img, i, j):
    b = img[ i, j, 0]
    g = img[ i, j, 1]
    r = img[ i, j, 2]
    a = img[ i, j, 3] / 255.0
    background = CHECKERED_PATTERN[ ( i + j) % 2]
    b = int( background * ( 1 - a) + b * a + 0.5)
    g = int( background * ( 1 - a) + g * a + 0.5)
    r = int( background * ( 1 - a) + r * a + 0.5)
    return b, g, r


def main( args) :
    parser = argparse.ArgumentParser( description = DESC_STR, usage = USAGE_STR)
    parser.add_argument( "-c", "--cols", "--width", type = int,
                        help = "displaying width of image")
    parser.add_argument( "-r", "--rows", "--height", type = int,
                        help = "displaying height of image")
    parser.add_argument( "-s", "--scale", type = float,
                        help = "displaying scale of image")
    parser.add_argument( "-i", "--interactive", action = "store_true",
                        help = "interactive mode")
    parser.add_argument( "-t", "--transparent", action = "store_true",
                        help = "use checkered pattern to show transparency")
    parser.add_argument( "-e", "--recursive", action = "store_true",
                        help = "travel into folders recursively")
    args, arg_files = parser.parse_known_args( args)
    try :
        arg_files.remove( "--")
    except :
        pass

    # check arguments:
    if args.interactive:
        if args.cols is not None or args.rows is not None or args.scale is not None:
            print( "ERROR: cannot set resolution with interactive mode.")
            exit( ERR_ARGS)
        # TODO: import gui lib
        mode = MODE_INTERACTIVE
    elif args.scale is not None:
        if args.scale <= 0 or args.scale >= 1000:
            print( "ERROR: scale setting '%f' out of range!" % ( args.scale))
            exit( ERR_ARGS)
        if args.cols is not None:
            print( "ERROR: conflict settings of display scale and width")
            exit( ERR_ARGS)
        elif args.rows is not None:
            print( "ERROR: conflict settings of display scale and height")
            exit( ERR_ARGS)
        mode = MODE_SCALING
    elif args.cols is not None:
        if args.cols < 1:
            print( "ERROR: invalid width setting '%d' !" % ( args.cols))
            exit( ERR_ARGS)
        if args.rows is not None:
            if args.rows < 1:
                print( "ERROR: invalid height setting '%d' !" % ( args.rows))
                exit( ERR_ARGS)
            mode = MODE_FIXED_RESOLUTION
        else:
            mode = MODE_FIXED_WIDTH
    elif args.rows is not None:
        if args.rows < 1:
            print( "ERROR: invalid height setting '%d' !" % ( args.rows))
            exit( ERR_ARGS)
        mode = MODE_FIXED_HEIGHT
    else:
        mode = MODE_AUTO

    # check folders:
    expanded_files = list()
    for elem in arg_files:
        if os.path.isdir( elem):
            if args.recursive:
                for base, folders, files in os.walk( elem):
                    folders.sort(); files.sort()
                    for name in files:
                        if is_picture_suffix( name):
                            expanded_files.append( os.path.join( base, name))
            else:
                for name in os.listdir( elem):
                    path = os.path.join( elem, name)
                    if os.path.isfile( path) and is_picture_suffix( name):
                        expanded_files.append( path)
        elif os.path.isfile( elem) or os.path.islink( elem):
            expanded_files.append( elem)
        else:
            print( "WARNING: cannot locate file '%s', ignored." % ( elem))

    try:
        import shutil
        terminal_size = shutil.get_terminal_size( ( 80, 24))
        screen_height = terminal_size.lines
        screen_width = terminal_size.columns
    except:
        try:
            screen_height, screen_width = os.popen('stty size', 'r').read().split()
        except:
            screen_height, screen_width = 24, 80

    # process each file:
    if mode == MODE_INTERACTIVE:
        #TODO
        print( "ERROR: TODO")
        exit( ERR_INTERAL)
    else:
        for path in expanded_files:
            try:
                img = load_bgra( path)
                height = int( img.shape[ 0])
                width = int( img.shape[ 1])
            except Exception as e:
                import traceback
                print( traceback.format_exc())
                print( type( e))
                print( e)
                print( "WARNING: failed loading file '%s', ignored." % path)
                continue
            if len( expanded_files) > 1:
                print( "\n" + path)
            else:
                screen_height -= 1
            if mode == MODE_AUTO:
                if screen_width * height >= screen_height * 2 * width:
                    resize_height = screen_height * 2
                    resize_width = int( width * resize_height / height + 0.5)
                else:
                    resize_width = screen_width
                    resize_height = int( height * resize_width / width + 0.5)
            elif mode == MODE_FIXED_WIDTH:
                resize_width = args.cols
                resize_height = int( height * resize_width / width + 0.5)
            elif mode == MODE_FIXED_HEIGHT:
                resize_height = args.rows
                resize_width = int( width * resize_height / height + 0.5)
            elif mode == MODE_FIXED_RESOLUTION:
                resize_height = args.rows
                resize_width = args.cols
            elif mode == MODE_SCALING:
                resize_height = int( height * args.scale + 0.5)
                resize_width = int( width * args.scale + 0.5)
            else:
                raise Exception( 'ERROR: internal error with mode')
            resize_width = np.clip( resize_width, 1, 1000)
            resize_height = np.clip( resize_height, 1, 1000)
            resized_img = cv.resize( img, ( resize_width, resize_height), interpolation = cv.INTER_AREA)
            if resize_height % 2 == 1:
                line = np.zeros( ( 1, resize_width, 4), dtype = np.uint8)
                line[ :, :, 3] = 255
                resized_img = np.vstack( ( resized_img, line))
                resize_height = int( resized_img.shape[ 0])
            if args.transparent:
                for i in range( 0, resize_height, 2):
                    for j in range( resize_width):
                        up_b, up_g, up_r = render_checkered_pattern( resized_img, i, j)
                        lo_b, lo_g, lo_r = render_checkered_pattern( resized_img, i + 1, j)
                        print( PIXEL_FMT % ( up_r, up_g, up_b, lo_r, lo_g, lo_b), end='', sep='')
                    print()
            else:
                for i in range( 0, resize_height, 2):
                    for j in range( resize_width):
                        ( up_b, up_g, up_r) = resized_img[ i, j, 0:3]
                        ( lo_b, lo_g, lo_r) = resized_img[ i + 1, j, 0:3]
                        print( PIXEL_FMT % ( up_r, up_g, up_b, lo_r, lo_g, lo_b), end='', sep='')
                    print()

if __name__ == "__main__" :
    main( sys.argv[ 1:])


# End of 'imageviewer.py' 

