#!/usr/bin/env python

"""
Generate pdfs of labels for Coilcube Cases
"""

import os
import sys
import math
import glob
import random

try:
    import qrcode
    import qrcode.image.svg
except ImportError as e:
    print('Could not import qrcode.')
    print('sudo pip install qrcode')
    sys.exit(1)

import svgutils.transform as sg

import sh
from sh import pdftk
from sh import pdf2svg


# *** Settings ***
LABEL_PDF = 'sticker_logo_5.pdf'
RANDOMIZE = False
TEST_BOTTOM = False

QR_CODE_STR = '{}|coilcube|A|http://lab11.github.io/monjolo'
QR_COLOR = '#2A388F'
QR_IN_USE = False

POSITION_START_X = 0
POSITION_START_Y = 0
x = POSITION_START_X
y = POSITION_START_Y

label_specs = {}
label_specs['offset_x'] = 47.5
#25 45 47 46 46.1 47
label_specs['gap_x']    = 5.5
#9 6 5
label_specs['width_x']  = 53
label_specs['offset_y'] = 45.2
#36 38 45
label_specs['gap_y']    = 5.6
#0 6 5 5.5
label_specs['height_y'] = 53.5
#61
label_specs['y_count']  = 12
label_specs['x_count']  = 9

label_pdf = LABEL_PDF
label_pixels_x = 108
label_pixels_y = 72
label_id_pos_x = 27
label_id_pos_y = 26
label_id_font = 6
label_id_letterspacing = 0
label_rotate = False
if QR_IN_USE:
    label_qr_pos_x = 69
    label_qr_pos_y = 13
    label_qr_scale = 1

def main():
    # List of ids to make QR codes of
    ids = []

    if len(sys.argv) != 2:
        print('Usage: {} <64 bid id|file of ids>'.format(__file__))
        sys.exit(1)

    if os.path.exists(sys.argv[1]):
        with open(sys.argv[1]) as f:
            for l in f:
                nodeid = l.replace('"', '')
                if nodeid:
                    ids.append(nodeid)
    else:
        nodeid = sys.argv[1]
        if nodeid:
            ids.append(nodeid)

    if len(ids) == 0:
        print('No IDs to make labels of!')
        sys.exit(1)

    if RANDOMIZE:
        random.shuffle(ids)

    labels_per_page = (label_specs['y_count'] * label_specs['x_count'])
    num_pages = int(math.ceil(float(len(ids)) / labels_per_page))
    print("Printing " + str(num_pages) + " pages")
    for page_num in range(1, num_pages+1):
        id_list = ids[labels_per_page*(page_num-1):labels_per_page*page_num]
        create_label_page(id_list, page_num)

def get_coordinates ():
    global x, y

    xpx = label_specs['offset_x'] + (x*(label_specs['gap_x'] + label_specs['width_x']))
    ypx = label_specs['offset_y'] + (y*(label_specs['gap_y'] + label_specs['height_y']))

    do_add = True
    if TEST_BOTTOM:
        if not y < 3:
            do_add = False

    x += 1
    if x > label_specs['x_count']-1:
        x = 0
        y += 1

    return (round(xpx), round(ypx), do_add)

def position_label(label):
    x_mod = 0
    y_mod = 0

    # actually, these all look great as they are...

    return (x_mod, y_mod, label)


def create_label_page(ids, page_num):
    global x,y

    label_sheet = sg.SVGFigure('612', '792') # 8.5"x11" paper at 72dpi
    labels = []

    # Convert the base label pdf to svg
    pdf2svg(label_pdf, 'output/label.svg')

    for nodeid in ids:
        nodeidstr = nodeid.replace(':', '')

        if QR_IN_USE:
            # Create the QR code
            img = qrcode.make(QR_CODE_STR.format(nodeid),
                    image_factory=qrcode.image.svg.SvgPathImage,
                    box_size=7,
                    version=4,
                    border=0)
            img.save('output/qr_{}.svg'.format(nodeidstr))

            # Color the QR code
            with open('output/qr_{}.svg'.format(nodeidstr), 'r+') as f:
                svg = f.read()
                f.seek(0)
                svg = svg.replace('fill:#000000;', 'fill:{};'.format(QR_COLOR))
                f.write(svg)

        # Create the node specific svg
        fig = sg.SVGFigure('{}px'.format(label_pixels_x), '{}px'.format(label_pixels_y))

        rawlabel = sg.fromfile('output/label.svg')
        rawlabelr = rawlabel.getroot()

        if QR_IN_USE:
            qr = sg.fromfile('output/qr_{}.svg'.format(nodeidstr))
            qrr = qr.getroot()
            # position correctly (hand tweaked)
            qrr.moveto(label_qr_pos_x, label_qr_pos_y, label_qr_scale)

        # position modifications based on text
        (x_mod, y_mod, nodeid) = position_label(nodeid)

        #txt = sg.TextElement(100,318, nodeid, size=28, font='Courier')
        txt = sg.TextElement(label_id_pos_x+x_mod,
                             label_id_pos_y+y_mod,
                             nodeid,
                             size=label_id_font,
                             font='Droid Sans',
                             letterspacing=label_id_letterspacing,
                             anchor='middle')

        if QR_IN_USE:
            fig.append([rawlabelr, qrr, txt])
        else:
            fig.append([rawlabelr, txt])
        fig.save('output/label_{}.svg'.format(nodeidstr))

        if label_rotate:
                fig = sg.SVGFigure('{}px'.format(label_pixels_y), '{}px'.format(label_pixels_x))
                dlabel = sg.fromfile('output/label_{}.svg'.format(nodeidstr))
                dlabelr = dlabel.getroot()
                dlabelr.rotate(90, x=0, y=0)
                dlabelr.moveto(0, -1*label_pixels_y)
                fig.append([dlabelr])
                fig.save('output/label_{}.svg'.format(nodeidstr))

    #       labels.append(fig)

            # Convert the id specific image to pdf
    #       sh.rsvg_convert('-f', 'pdf', '-o', 'label_{}.pdf'.format(nodeidstr),
    #               'label_{}.svg'.format(nodeidstr))

            # Stamp the label with id specific image
    #       pdftk(CASE_LABEL, 'stamp', 'unique_{}.pdf'.format(nodeidstr), 'output',
    #               'label_{}.pdf'.format(nodeidstr))

    #       pdf2svg('label_{}.pdf'.format(nodeidstr), 'label_{}.svg'.format(nodeidstr))

        lbl = sg.fromfile('output/label_{}.svg'.format(nodeidstr))
        lblr = lbl.getroot()
        pos = get_coordinates()
        lblr.moveto(pos[0], pos[1], 1) # position correctly (hand tweaked)

        if pos[2]:
            labels.append(lblr)

    label_sheet.append(labels)
    label_sheet.save('output/all_labels_{}.svg'.format(page_num))
    sh.rsvg_convert('-f', 'pdf', '-d', '72', '-p', '72', '-o',
            'output/all_labels_{}.pdf'.format(page_num),
            'output/all_labels_{}.svg'.format(page_num))

    # cleanup after yourself
    x = POSITION_START_X
    y = POSITION_START_Y
    for fl in glob.glob('output/label_*'):
        os.remove(fl)


if __name__ == '__main__':
    main()
