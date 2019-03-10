"""
ImportC2D, an Inkscape input extension by Nathaniel Klumb

This extension adds support for Carbide Create C2D files to the File/Import...
dialog in Inkscape.  It loads the C2D file passed to it by Inkscape as a
command-line parameter and writes the resulting SVG to stdout (which is how
Inkscape input plugins work).

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.
"""
import inkex
from StringIO import StringIO
from math import sin,cos,pi
import json

class ImportC2D:
    """ Import a Carbide Create C2D file and process it into an SVG."""
    svg = None
    current_id = 0
    STYLE = ('opacity:1;vector-effect:none;fill:none;fill-opacity:1;'
             'stroke:#000000;stroke-width:0.1px;stroke-opacity:1;'
             'stroke-linecap:round;stroke-linejoin:round;stroke-miterlimit:4;'
             'stroke-dasharray:none;stroke-dashoffset:0')
    def __init__(self,c2d_file,as_paths):
        """ Load a C2D file and process it into an SVG. """
        self.as_paths = as_paths
        self.SubElement = inkex.etree.SubElement

        with open(c2d_file,'r') as f:
            c2d = json.load(f)
        
        width = c2d['DOCUMENT_VALUES']['WIDTH']
        height = c2d['DOCUMENT_VALUES']['HEIGHT']
        self.svg = inkex.etree.parse(StringIO(
            '<svg xmlns="http://www.w3.org/2000/svg" width="{0}mm" '
            'height="{1}mm" viewBox="0 0 {0} {1}"/>'.format(width,height)))
        
        self.add_stock(height,width)
        self.add_groups(self.get_groups(c2d))
        self.add_circles(c2d)
        self.add_curves(c2d)
        self.add_rects(c2d)
        self.add_polys(c2d)
        self.add_texts(c2d)
        
    def add_stock(self,height,width):
        """ Add the stock size rectangle to the SVG. """
        style = ('opacity:1;vector-effect:none;fill:#24c389;fill-opacity:0.05;'
                 'stroke:none;stroke-width:0.1px;stroke-linecap:round;'
                 'stroke-linejoin:round;stroke-miterlimit:4;stroke-dasharray:none;'
                 'stroke-dashoffset:0;stroke-opacity:1')
        self.SubElement(self.svg.getroot(),'rect',{'x':'0', 'y':'0',
                                                   'width':'{}'.format(width),
                                                   'height':'{}'.format(height),
                                                   'id':'frame', 'style':style,
                                                   'transform':'scale(1,-1)'})

    def get_groups(self,c2d):
        """ Get the group information from the C2D. """
        all_groups = {False: []}
        seen_groups = {}
        for key in c2d.keys():
            for thing in c2d[key]:
                try:
                    groups = thing['group_id']
                except (KeyError,TypeError):
                    groups = []
                parent = False
                for g in range(len(groups)-1,-1,-1):
                    group = groups[g]
                    if group not in seen_groups:
                        all_groups[parent] += [group]
                        all_groups[group] = []
                    parent = group
                    seen_groups[group] = True
        return all_groups
        
    def add_groups(self,all_groups,subgroups_of=None):
        """ Add nested groups to the SVG. """
        if subgroups_of is None:
            attrs = {'id':'C2Dfile','transform':'scale(1,-1)'}
            self.group_elements = {False:self.SubElement(self.svg.getroot(),
                                                         'g',attrs)}
            subgroups_of = False
        for group in all_groups[subgroups_of]:
            self.group_elements[group] = \
                self.SubElement(self.group_elements[subgroups_of],
                                'g',{'id':str(group)})
            self.add_groups(all_groups,group)
    
    def add_circles(self,c2d):
        """ Add the C2D's CIRCLE_OBJECTS to the SVG. """
        try:
            circles = c2d['CIRCLE_OBJECTS']
        except KeyError:
            circles = []
        for c in circles:
            x,y = c['position']
            radius = c['radius']
            tag,attrs = self.c2d_circle(x,y,radius)
            try:
                parent = c['group_id'][0]
            except IndexError:
                parent = ''
            self.SubElement(self.group_elements[parent],tag,attrs)

    def add_curves(self,c2d):
        """ Add the C2D's CURVE_OBJECTS to the SVG. """
        try:
            curves = c2d['CURVE_OBJECTS']
        except KeyError:
            curves = []
        for c in curves:
            x,y = c['position']
            points = c['points']
            point_types = c['point_type']
            handles_1 = c['control_point_1']
            handles_2 = c['control_point_2']
            tag,attrs = self.c2d_curve(x,y,point_types,points,
                                       handles_1,handles_2)
            try:
                parent = c['group_id'][0]
            except IndexError:
                parent = ''
            self.SubElement(self.group_elements[parent],tag,attrs)

    def add_rects(self,c2d):
        """ Add the C2D's RECT_OBJECTS to the SVG. """
        try:
            rects = c2d['RECT_OBJECTS']
        except KeyError:
            rects = []
        for r in rects:
            x,y = r['position']
            height = r['height']
            width = r['width']
            radius = r['radius']
            corners = r['corner_type']
            rotation = r['rotation']
            tag,attrs = self.c2d_rect(x,y,height,width,radius,corners,rotation)
            try:
                parent = r['group_id'][0]
            except IndexError:
                parent = ''
            self.SubElement(self.group_elements[parent],tag,attrs)

    def add_polys(self,c2d):
        """ Add the C2D's REGULAR_POLYGON_OBJECTS to the SVG. """
        try:
            polys = c2d['REGULAR_POLYGON_OBJECTS']
        except KeyError:
            polys = []
        for p in polys:
            x,y = p['position']
            radius = p['radius']
            sides = p['num_sides']
            rotation = p['rotation']
            tag,attrs = self.c2d_poly(x,y,radius,sides,rotation)
            try:
                parent = p['group_id'][0]
            except IndexError:
                parent = ''
            self.SubElement(self.group_elements[parent],tag,attrs)

    def add_texts(self,c2d):
        """ Add the C2D's rendered TEXT_OBJECTS to the SVG. """
        warning_shown = False
        try:
            texts = c2d['TEXT_OBJECTS']
        except KeyError:
            texts = []
        for t in texts:
            try:
                tag,attrs = self.c2d_text(t['rendered'])
            except KeyError:
                if not warning_shown:
                    inkex.errormsg('Non-rendered text ignored:  '
                                   'To import the text, simply '
                                   'open the file in Carbide Create '
                                   'version 316 or later and save.')
                warning_shown = True
                continue
            try:
                parent = t['group_id'][0]
            except IndexError:
                parent = ''
            self.SubElement(self.group_elements[parent],tag,attrs)

    def next_id(self):
        """ Get the next serially-incremented ID. """
        self.current_id += 1
        return self.current_id
        
    def rect(self,x,y,width,height,radius=None,transform=None):
        """ Make a rectangle to add to the SVG. """
        attrs = {'x':str(x), 'y':str(y),
                 'width':str(width), 'height':str(height),
                 'id':'rect{}'.format(self.next_id()), 'style':self.STYLE}
        if radius is not None:
            attrs['rx'] = str(radius)
            attrs['ry'] = str(radius)
        if transform is not None:
            attrs['transform'] = transform
            attrs['style'] = self.STYLE
        return ('rect', attrs)

    def circle(self,x,y,radius):
        """ Make a circle to add to the SVG. """
        return ('circle', {'cx':str(x), 'cy':str(y), 'r':str(radius),
                           'id':'circle{}'.format(self.next_id()),
                           'style':self.STYLE})

    def path(self,path_data,transform=None):
        """ Make a path to add to the SVG. """
        attrs = {'d': path_data,
                 'id':'path{}'.format(self.next_id()),
                 'style':self.STYLE}
        if transform is not None:
            attrs['transform'] = transform
        return ('path', attrs)
            
    def c2d_rect(self,x,y,height,width,radius,corners,rotation):
        """ Turn a C2D rect into SVG element data. """
        if rotation:
            transform = 'rotate({},{},{})'.format(rotation,x,y)
        else:
            transform = None
        hheight = height / 2.0
        hwidth = width / 2.0
        
        # Carbide Create limits the radius to sane values... although
        # for "Tee" corners, it really ought to limit it to half that.
        if radius > hheight:
            radius = hheight
        if radius > hwidth:
            radius = hwidth

        # Plain rectange. ("Square")
        if ((corners == 0) or (radius == 0)):
            if self.as_paths:
                return self.path('M {},{} '.format(x + hwidth, y + hheight) +
                                 'L {},{} '.format(x + hwidth, y - hheight) +
                                 'L {},{} '.format(x - hwidth, y - hheight) +
                                 'L {},{} '.format(x - hwidth, y + hheight) +
                                 'Z', transform)
            else:
                return self.rect(x-hwidth,y-hheight,width,height,None,transform)
        # Rounded rectange.    ("Fillet")
        elif (corners == 1):
            if self.as_paths:
                return self.path('M {},{} '.format(x + hwidth - radius,
                                                   y + hheight) +
                                 'A {} {} 0 0 0 {},{} '.format(radius, radius,
                                                               x + hwidth,
                                                               y + hheight
                                                               - radius) +
                                 'L {},{} '.format(x + hwidth,
                                               y - hheight + radius) +
                                 'A {} {} 0 0 0 {},{} '.format(radius, radius,
                                                               x + hwidth
                                                               - radius,
                                                               y - hheight) +
                                 'L {},{} '.format(x - hwidth + radius,
                                               y - hheight) +
                                 'A {} {} 0 0 0 {},{} '.format(radius, radius,
                                                               x - hwidth,
                                                               y - hheight
                                                               + radius) +
                                 'L {},{} '.format(x - hwidth,
                                               y + hheight - radius) +
                                 'A {} {} 0 0 0 {},{} '.format(radius, radius,
                                                               x - hwidth
                                                               + radius,
                                                               y + hheight) +
                                 'Z', transform)
            else:
                return self.rect(x-hwidth,y-hheight,width,height,radius,transform)
        # Chamfered corners. ("Chamfered")
        elif (corners == 2):
            return self.path('M {},{} '.format(x + hwidth - radius,
                                               y + hheight) +
                             'L {},{} '.format(x + hwidth,
                                               y + hheight - radius) +
                             'L {},{} '.format(x + hwidth,
                                               y - hheight + radius) +
                             'L {},{} '.format(x + hwidth - radius,
                                               y - hheight) +
                             'L {},{} '.format(x - hwidth + radius,
                                               y - hheight) +
                             'L {},{} '.format(x - hwidth,
                                               y - hheight + radius) +
                             'L {},{} '.format(x - hwidth,
                                               y + hheight - radius) +
                             'L {},{} '.format(x - hwidth + radius,
                                               y + hheight) +
                             'Z', transform)
        # Inverted rounded corners. ("Flipped Fillet")
        elif (corners == 3):
            return self.path('M {},{} '.format(x + hwidth - radius,
                                               y + hheight) +
                             'A {} {} 0 0 1 {},{} '.format(radius, radius,
                                                           x + hwidth,
                                                           y + hheight
                                                           - radius) +
                             'L {},{} '.format(x + hwidth,
                                               y - hheight + radius) +
                             'A {} {} 0 0 1 {},{} '.format(radius, radius,
                                                           x + hwidth - radius,
                                                           y - hheight) +
                             'L {},{} '.format(x - hwidth + radius,
                                               y - hheight) +
                             'A {} {} 0 0 1 {},{} '.format(radius, radius,
                                                           x - hwidth,
                                                           y - hheight
                                                           + radius) +
                             'L {},{} '.format(x - hwidth,
                                               y + hheight - radius) +
                             'A {} {} 0 0 1 {},{} '.format(radius, radius,
                                                           x - hwidth + radius,
                                                           y + hheight) +
                             'Z', transform)
        # Dogboned corners. ("Dogbone")                                
        elif (corners == 4):
            return self.path('M {},{} '.format(x + hwidth - radius,
                                               y + hheight) +
                             'A {} {} 0 1 0 {},{} '.format(radius, radius,
                                                           x + hwidth,
                                                           y + hheight
                                                           - radius) +
                             'L {},{} '.format(x + hwidth,
                                               y - hheight + radius) +
                             'A {} {} 0 1 0 {},{} '.format(radius, radius,
                                                           x + hwidth - radius,
                                                           y - hheight) +
                             'L {},{} '.format(x - hwidth + radius,
                                               y - hheight) +
                             'A {} {} 0 1 0 {},{} '.format(radius, radius,
                                                           x - hwidth,
                                                           y - hheight
                                                           + radius) +
                             'L {},{} '.format(x - hwidth,
                                               y + hheight - radius) +
                             'A {} {} 0 1 0 {},{} '.format(radius, radius,
                                                           x - hwidth + radius,
                                                           y + hheight) +
                             'Z', transform)
        # "Tee" corners. ("Tee")
        elif (corners == 5):
            return self.path('M {},{} '.format(x + hwidth - radius*2,
                                               y + hheight) +
                             'A {} {} 0 1 0 {},{} '.format(radius, radius,
                                                           x + hwidth,
                                                           y + hheight) +
                             'L {},{} '.format(x + hwidth,
                                               y - hheight) +
                             'A {} {} 0 1 0 {},{} '.format(radius, radius,
                                                           x + hwidth
                                                           - radius*2,
                                                           y - hheight) +
                             'L {},{} '.format(x - hwidth + radius*2,
                                               y - hheight) +
                             'A {} {} 0 1 0 {},{} '.format(radius, radius,
                                                           x - hwidth,
                                                           y - hheight) +
                             'L {},{} '.format(x - hwidth, y + hheight) +
                             'A {} {} 0 1 0 {},{} '.format(radius, radius,
                                                           x - hwidth
                                                           + radius*2,
                                                           y + hheight) +
                             'Z', transform)
        inkex.errormsg(str((x,y,height,width,radius,corners,rotation)))

    def c2d_poly(self,x,y,radius,sides,rotation):
        """ Turn a C2D regular polygon into SVG element data. """
        if rotation:
            transform = 'rotate({},{},{})'.format(rotation,x,y)
        else:
            transform = None
        path_data = ''
        command = 'M'
        for i in range(0,sides):
            point_x = x + radius * cos(2.0 * pi * i / sides)
            point_y = y + radius * sin(2.0 * pi * i / sides)
            path_data += '{} {},{} '.format(command,point_x,point_y)
            command = 'L'
        path_data += ' Z'
        return self.path(path_data, transform)

    def c2d_circle(self,x,y,radius):
        """ Turn a C2D circle into SVG element data. """
        if self.as_paths:
            return self.path('M {},{} '.format(x + radius, y) +
                             'A {} {} 0 1 1 {},{} '.format(radius, radius,
                                                           x - radius, y) +
                             'A {} {} 0 1 1 {},{} '.format(radius, radius,
                                                           x + radius, y) +
                             'Z')
        else:
            return self.circle(x,y,radius)

    def c2d_text(self,rendered):
        """ Turn C2D rendered text into SVG element data. """
        path_data = ''
        for subpath in rendered:
            command = 'M'
            for point in subpath:
                path_data += '{} {},{} '.format(command,point[0],point[1])
                command = 'L'
        path_data += 'Z'
        return self.path(path_data)

    def c2d_curve(self,x,y,point_types,points,handles_1,handles_2):
        """ Turn a C2D curve into SVG element data. 
        
        point_type == 1: Straight line segments.
        point_type == 3: Cubic bezier curve.
        point_type == 4: Close the curve.
        
        The last "point" is basically just there as a flag for
        whether the curve is open or closed.
        """
        path_data = 'M {},{} '.format(points[0][0]+x,points[0][1]+y)
        if point_types[-1] == 4:
            num_points = len(point_types) - 1
        else:
            num_points = len(point_types)
        for i in range(1,num_points):
            if (point_types[i-1] == 3):
                path_data += 'C {},{} {},{} {},{} '.format(handles_2[i-1][0]+x,
                                                           handles_2[i-1][1]+y,
                                                           handles_1[i][0]+x,
                                                           handles_1[i][1]+y,
                                                           points[i][0]+x,
                                                           points[i][1]+y)
            elif (point_types[i-1] == 1):
                path_data += 'L {},{} '.format(points[i][0]+x,points[i][1]+y)
        if (point_types[-1] == 4):
            if (point_types[0] == 3):
                # For closed bezier curves, Carbide Create makes a connecting
                # bezier curve segment using the incoming handle from the
                # starting point.  Add that curve before closing the path.
                path_data += 'C {},{} {},{} {},{} '.format(handles_2[-2][0]+x,
                                                           handles_2[-2][1]+y,
                                                           handles_1[0][0]+x,
                                                           handles_1[0][1]+y,
                                                           points[0][0]+x,
                                                           points[0][1]+y)
            path_data += 'Z'    
        return self.path(path_data)
        
if __name__ == '__main__':
    parser = inkex.optparse.OptionParser(usage="usage: %prog [-p] C2Dfile",
                                         option_class=inkex.InkOption)
    parser.add_option('-p', '--as_paths', action='store',
                      help='Import all objects as paths.', default=False)
    # These <param> elements in "c2d_input.inx" apparently get passed to
    # the extension.  We don't use them, but we let OptionParser store them
    # so it won't complain.
    parser.add_option('--tab', action='store')
    parser.add_option('--inputhelp', action='store')
    parser.add_option('--textwarning', action='store')
    parser.add_option('--helptext', action='store')
    (options, args) = parser.parse_args(inkex.sys.argv[1:])
    
    # The File/Import... dialog only allows importing a single file at a time,
    # and the fully-qualified filename is passed as the first positional
    # argument when the extension is called.
    c2d = ImportC2D(args[0], (options.as_paths == 'true'))
    
    # An Inkscape input extension does whatever it needs to do with the input
    # file and then writes an SVG to stdout.  Inkscape takes this as input and
    # creates a new layer out of the contents of the SVG.
    c2d.svg.write(inkex.sys.stdout)
