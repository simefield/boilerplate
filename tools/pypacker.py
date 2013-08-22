#----------------------------------------------------
#- pypacker: written by Joe Wezorek.
#            CSS extensions by Josh Barr | Springload
#- license:  WTFPL
#- If you use this code and/or have suggestions, etc.,
#- email me at jwezorek@gmail.com

import os
import os.path
import copy
import re
from PIL import Image  # ImageDraw
from optparse import OptionParser
from math import log, ceil
from decimal import *


def sort_images_by_size(image_files):
    #sort by area (secondary key)
    sorted_images = sorted(
        image_files,
        key=lambda img_pair: img_pair.img.size[0] * img_pair.img.size[1]
    )
        #sort by max dimension (primary key)
    sorted_images = sorted(
        sorted_images,
        key=lambda img_pair: max(img_pair.img.size[0], img_pair.img.size[1])
    )
    return sorted_images


#----------------------------------------------------------------------

class img_pair:
    def __init__(self, name, img):
        self.name = name
        self.img = img

#----------------------------------------------------------------------


class rectangle:
    def __init__(self, x=0, y=0, wd=0, hgt=0):
        self.x = x
        self.y = y
        self.wd = wd
        self.hgt = hgt

    def split_vert(self, y):
        top = rectangle(self.x, self.y, self.wd, y)
        bottom = rectangle(self.x, self.y+y, self.wd, self.hgt-y)
        return (top, bottom)

    def split_horz(self, x):
        left = rectangle(self.x, self.y, x, self.hgt)
        right = rectangle(self.x+x, self.y, self.wd-x, self.hgt)
        return (left, right)

    def area(self):
        return self.wd * self.hgt

    def max_side(self):
        return max(self.wd, self.hgt)

    def can_contain(self, wd, hgt):
        return self.wd >= wd and self.hgt >= hgt

    def is_congruent_with(self, wd, hgt):
        return self.wd == wd and self.hgt == hgt

    def to_string(self):
        return "<(%d, %d) - (%d, %d)>" % (self.x, self.y, self.wd, self.hgt)

    def should_split_vertically(self, wd, hgt):
        if (self.wd == wd):
            return True
        elif (self.hgt == hgt):
            return False
        #TODO: come up with a better heuristic
        vert_rects = self.split_vert(hgt)
        horz_rects = self.split_horz(wd)
        return vert_rects[1].area() > horz_rects[1].area()

    def should_grow_vertically(self, wd, hgt):
        can_grow_vert = self.wd >= wd
        can_grow_horz = self.hgt >= hgt
        if (not can_grow_vert and not can_grow_horz):
            raise Exception("Unable to grow!")
        if (can_grow_vert and not can_grow_horz):
            return True
        if (can_grow_horz and not can_grow_vert):
            return False
        return (self.hgt + hgt < self.wd + wd)


#----------------------------------------------------------------------
class rect_node:
    def __init__(self, img_pair, rect=(), children=()):
        self.rect = rect
        if (img_pair):
            self.img_name = img_pair.name
            self.img = img_pair.img
        else:
            self.img_name = ()
            self.img = ()
        self.children = children

    def clone(self):
        if (self.is_leaf()):
            return rect_node(img_pair(self.img_name, self.img), copy.copy(self.rect))
        else:
            return rect_node(img_pair(self.img_name, self.img), copy.copy(self.rect),
                            (self.children[0].clone(), self.children[1].clone()))

    def is_leaf(self):
        return not self.children

    def is_empty_leaf(self):
        return (self.is_leaf() and not self.img)

    def split_node(self, img_pair):
        if (not self.is_leaf):
            raise Exception("Attempted to split non-leaf")

        (img_wd, img_hgt) = img_pair.img.size
        if (not self.rect.can_contain(img_wd, img_hgt)):
            raise Exception("Attempted to place an img in a node it doesn't fit")

        #if it fits exactly then we are done...
        if (self.rect.is_congruent_with(img_wd, img_hgt)):
            self.img_name = img_pair.name
            self.img = img_pair.img
        else:
            if (self.rect.should_split_vertically(img_wd, img_hgt)):
                vert_rects = self.rect.split_vert(img_hgt)
                top_child = rect_node((), vert_rects[0])
                bottom_child = rect_node((), vert_rects[1])
                self.children = (top_child, bottom_child)
            else:
                horz_rects = self.rect.split_horz(img_wd)
                left_child = rect_node((), horz_rects[0])
                right_child = rect_node((), horz_rects[1])
                self.children = (left_child, right_child)
            self.children[0].split_node(img_pair)


    def divisible_by_two(self, value):
        if (not value % 2 == 0 and not value == 0):
            return 0
        return 1


    def grow_node(self, img_pair):
        if (self.is_empty_leaf()):
            raise Exception("Attempted to grow an empty leaf")
        (img_wd, img_hgt) = img_pair.img.size
        new_child = self.clone()
        self.img = ()
        self.img_name = ()

        # def our variables for growing...
        startX = self.rect.x
        startY = self.rect.y

        # check the width and height are grow-able by two :)
        if (not self.divisible_by_two(startX)):
            startX = startX+1
        if (not self.divisible_by_two(startY)):
            startY = startY+1

        newY = startY+self.rect.hgt
        newX = startX+self.rect.wd

        if (not self.divisible_by_two(newY)):
            newY = self.rect.y+self.rect.hgt+1
        if (not self.divisible_by_two(newX)):
            newX = self.rect.x+self.rect.wd+1

        #print "<%d, %d, %d, %d, %d, %d>" % (newY, newX, startX, startY, img_wd, img_hgt)

        if self.rect.should_grow_vertically(img_wd, img_hgt):
            self.children = (
                new_child,
                rect_node((), rectangle(startX, newY, self.rect.wd, img_hgt))
            )
            self.rect.hgt += img_hgt
        else:
            self.children = (
                new_child,
                rect_node((), rectangle(newX, startY, img_wd, self.rect.hgt))
            )
            self.rect.wd += img_wd
        self.children[1].split_node(img_pair)

    def to_string(self):
        if (self.is_leaf()):
            return "[ %s: %s ]" % (self.img_name, self.rect.to_string())
        else:
            return "[ %s: %s | %s %s]" % \
                (self.img_name, self.rect.to_string(), self.children[0].to_string(), self.children[1].to_string())

    def render(self, img):
        if (self.is_leaf()):
            if (self.img):
                img.paste(self.img, (self.rect.x, self.rect.y))
        else:
            self.children[0].render(img)
            self.children[1].render(img)

    def to_xml(self):
        xml = "<key>%s</key>\n" % (self.img_name)
        xml += "<dict>\n"
        xml += "    <key>frame</key>\n"
        xml += "    <string>{{%d,%d},{%d,%d}}</string>\n" % (self.rect.x, self.rect.y, self.rect.wd, self.rect.hgt)
        xml += "    <key>offset</key>\n"\
               "    <string>{0,0}</string>\n"\
               "    <key>rotated</key>\n"\
               "    <false/>\n"\
               "    <key>sourceColorRect</key>\n"
        xml += "    <string>{{0,0},{%d,%d}}</string>\n" % (self.rect.wd, self.rect.hgt)
        xml += "    <key>sourceSize</key>\n"
        xml += "    <string>{%d,%d}</string>\n" % (self.rect.wd, self.rect.hgt)
        xml += "</dict>\n"
        return xml

    def to_css(self):
        space = ""

        x = self.rect.x
        y = self.rect.y
        w = self.rect.wd
        h = self.rect.hgt

        if (self.pixel_ratio != 1):
            space = "    "
            scale = (1 / self.pixel_ratio)

            if (self.pixel_ratio == 2.00):
                if (self.rect.x == 0):
                    x = self.rect.x
                else:
                    if (self.rect.x % 2 == 0):
                        x = self.rect.x / 2
                    else:
                        print "Warning: `%s` x co-ordinate not divisible by two (%d)" % (self.img_name, self.rect.x)
                        x = int(self.rect.x * scale)
                if (self.rect.y == 0):
                    y = self.rect.y
                else:
                    if (self.rect.y % 2 == 0):
                        y = self.rect.y / 2
                    else:
                        print "Warning: `%s` y co-ordinate not divisible by two (%d)" % (self.img_name, self.rect.y)
                        y = int(self.rect.y * scale)
            else:
                x = int(self.rect.x * scale)
                y = int(self.rect.y * scale)

            # w = int(self.rect.wd * scale)
            # h = int(self.rect.hgt * scale)
            #
        squeaky_clean_name = re.sub('[^a-zA-Z0-9]', '_', (self.img_name.rsplit(".", 1)[0]))

        xml = "%s.s_%s_%s{\n" % (space, self.css_namespace, squeaky_clean_name)  # get the icon name for the classname

        xml += "%s    background-position: -%dpx -%dpx;\n" % (space, x, y)

        if (self.pixel_ratio == 1):
            xml += "%s    width: %dpx;\n" % (space, w)
            xml += "%s    height: %dpx;\n" % (space, h)

        xml += "%s}\n" % space
        return xml


#----------------------------------------------------------------------

def find_empty_leaf(node, img):
    (img_wd, img_hgt) = img.size
    if (node.is_empty_leaf()):
        return node if node.rect.can_contain(img_wd, img_hgt) else ()
    else:
        if (node.is_leaf()):
            return ()
        leaf = find_empty_leaf(node.children[0], img)
        if (leaf):
            return leaf
        else:
            return find_empty_leaf(node.children[1], img)


def pack_images(named_images, grow_mode, max_dim):
    root = ()
    while named_images:
        named_image = named_images.pop()
        if not root:
            if (grow_mode):
                root = rect_node((), rectangle(0, 0, named_image.img.size[0], named_image.img.size[1]))
            else:
                root = rect_node((), rectangle(0, 0, max_dim[0], max_dim[1]))
            root.split_node(named_image)
            continue
        leaf = find_empty_leaf(root, named_image.img)
        if (leaf):
            leaf.split_node(named_image)
        else:
            if (grow_mode):
                root.grow_node(named_image)
            else:
                raise Exception("Can't pack images into a %d by %d rectangle." % max_dim)
    return root


def nearest_power_of_two(n):
    #there's probably some cleverer way to do this... but take the log base-2,
    #and raise 2 to the power of the next integer...
    log_2 = log(n) / log(2)
    return int(2**(ceil(log_2)))


def flatten_nodes(node):
    if (node.is_leaf()):
        if (node.img):
            return [node]
        else:
            return ()
    else:
        left = flatten_nodes(node.children[0])
        right = flatten_nodes(node.children[1])
        if (left and not right):
            return left
        if (right and not left):
            return right
        if (left and right):
            return left + right
        else:
            return ()


def generate_sprite_sheet_img(packing, image_filename, should_pad):
    sz = ()
    if (not should_pad):
        sz = (packing.rect.wd, packing.rect.hgt)
    else:
        padded_dim = nearest_power_of_two(max(packing.rect.wd, packing.rect.hgt))
        sz = (padded_dim, padded_dim)

    sprite_sheet = Image.new('RGBA', sz)
    packing.render(sprite_sheet)
    sprite_sheet.save(image_filename, 'PNG', optimize=True)
    return sprite_sheet


def write_css_head(f, filename, nodes, css_namespace, path_to_sprite_from_css, pixel_ratio, sz):

    base_dpi = 96  # This is the standard DPI of screen devices. Bit of an assumption.
    space = ""

    comment_name = "@%ddpi | 1.00x" % base_dpi

    if(pixel_ratio != 1):
        comment_name = "@ %ddpi | %.2fx" % (base_dpi * pixel_ratio, pixel_ratio)

    f.write("/**\n * %s %s\n * ----------------------------------------\n" % (css_namespace, comment_name))

    #f.write(" * Size: %dpx, %dpx \n" % sz)
    f.write(" */\n")
    img_width = sz[0]
    img_height = sz[1]

    # If the ratio isn't 1, print a media query
    if(pixel_ratio != 1):
        dpi = "%ddpi" % (base_dpi * pixel_ratio)
        img_width = round(img_width * 1 / pixel_ratio, 0)
        img_height = round(img_height * 1 / pixel_ratio, 0)

        media_query = "@media "
        media_query += "only screen and (-webkit-min-device-pixel-ratio: %.2f), " % pixel_ratio
        media_query += "only screen and (min--moz-device-pixel-ratio: %.2f), " % pixel_ratio
        media_query += "only screen and (-o-min-device-pixel-ratio: %.2f/1), " % pixel_ratio
        media_query += "only screen and (min-device-pixel-ratio: %.2f), " % pixel_ratio
        media_query += "only screen and (min-resolution: %s), " % dpi
        media_query += "only screen and (min-resolution: 2dppx) {\n"

        f.write(media_query)
        space = "    "

    for node in nodes:
        squeaky_clean_name = re.sub('[^a-zA-Z0-9]', '_', (node.img_name.rsplit(".", 1)[0]))
        f.write("%s.s_%s_%s,\n" % (space, css_namespace, squeaky_clean_name))  # get the icon name for the classname
    
    f.write('%s.s_%s{\n' % (space, css_namespace))
    f.write('%s   background-repeat: no-repeat;\n' % space)
    f.write('%s   background-image: url(\'%s\');\n' % (space, path_to_sprite_from_css))

    if(pixel_ratio != 1):
        # print background_size
        f.write('%s   background-size: %dpx %dpx;\n' % (space, img_width, img_height))

    f.write('%s}\n' % space)


def write_css_tail(f, pixel_ratio):
    if(pixel_ratio != 1):
        f.write("}\n\n")


def generate_sprite_sheet_css(packing, filename, sz, css_namespace, path_to_sprite_from_css, pixel_ratio, test_page):
    nodes = flatten_nodes(packing)

    f = open(filename, 'w')
    write_css_head(f, filename, nodes, css_namespace, path_to_sprite_from_css, pixel_ratio, sz)
    for node in nodes:
        node.css_namespace = css_namespace
        node.pixel_ratio = pixel_ratio
        f.write(node.to_css())
    write_css_tail(f, pixel_ratio)
    f.close()


def generate_sprite_sheet(packing, output_sprite_file, output_css_file, css_namespace, should_pad, path_to_sprite_from_css, pixel_ratio, test_page):
    img = generate_sprite_sheet_img(packing, output_sprite_file, should_pad)
    generate_sprite_sheet_css(packing, output_css_file, img.size, css_namespace, path_to_sprite_from_css, pixel_ratio, test_page)


def get_images(image_dir):
    images = []
    for file in os.listdir(image_dir):
        img = ()
        try:
            img = Image.open(image_dir + os.sep + file)
            img.basename = file
        except:
            continue
        if (not images):
            images = [img_pair(file, img)]
        else:
            images.append(img_pair(file, img))
    return images


def ensure_path_exists(path):
    isDir = os.path.isdir(path)

    if(isDir==False):
        try:
            print "Creating: " + path
            os.makedirs(path)
        except:
            print "Oops, couldn't make directory " + path



def main():

    parser = OptionParser(usage="usage: %prog [options]",
                          version="%prog 1.0")

    parser.add_option("-o", "--output_filename",
                      action="store",
                      default="",
                      help="filename (minus extensions) of the two output files")

    parser.add_option("-i", "--input_dir",
                      action="store",
                      default="",
                      help="input directory")

    parser.add_option("-m", "--mode",
                      action="store",
                      default="grow",
                      help="packingmode. Can be 'grow' or numeric")

    parser.add_option("-p", "--pad",
                      action="store_true",
                      default=False,
                      help="pad to nearest power of two")

    parser.add_option("-n", "--css_namespace",
                      action="store",
                      default="",
                      help="CSS namespace for the sprites. Defaults to the folder-name")

    parser.add_option("-c", "--css_dir",
                      action="store",
                      default=".",
                      help="CSS output directory")

    parser.add_option("-a", "--sass_dir",
                      action="store",
                      default="",
                      help="SaSS output directory")

    parser.add_option("-s", "--sprite_dir",
                      action="store",
                      default=".",
                      help="Sprite output directory")

    parser.add_option("-r", "--pixel_ratio",
                      action="store",
                      default="1",
                      help="Sprite pixel ratio (defaults to 1)")

    parser.add_option("-f", "--filename_prefix",
                      action="store",
                      default="sprite_",
                      help="Sprite pixel ratio (defaults to 1)")

    parser.add_option("-t", "--test_page",
                      action="store_true",
                      default=False,
                      help="Render an HTML test page in the CSS directory.")

    try:
        (options, args) = parser.parse_args()

        # A nice little banner in the terminal output

        css_extension = "css"
        img_extension = "png"

        # Clean directory paths so we don't get // nastiness.
        # ---------------------------------------------------------------------
        options.input_dir = os.path.normpath(options.input_dir)

        # Get the basename of the input directory so we can regex it
        basename = os.path.basename(options.input_dir)

        print "\n---------------------------------------------------------\nPyPacker\t\"" + basename + "\"\n---------------------------------------------------------\n"

        # Where the CSS gets saved to. Also the relative path for image urls
        # is calculated from here. Defaults to current dir.
        if(options.css_dir):
            options.css_dir = os.path.normpath(options.css_dir)
            ensure_path_exists(options.css_dir)

        # Where the SaSS files gets saved to (if used)
        if(options.sass_dir != ""):
            options.sass_dir = os.path.normpath(options.sass_dir)
            ensure_path_exists(options.sass_dir)

        # Where the sprites get saved to
        if(options.sprite_dir):
            options.sprite_dir = os.path.normpath(options.sprite_dir)
            ensure_path_exists(options.sprite_dir)

        if(options.output_filename == ""):
            options.output_filename = re.sub("-", "_", basename)

        if(options.css_namespace == ""):
            options.css_namespace = options.output_filename

        #
        # Sets the pixel aspect ratio
        # ---------------------------------------------------------------------
        pixel_ratio = Decimal(options.pixel_ratio)

        #
        # Try and infer the pixel_ratio from the directory name
        # ---------------------------------------------------------------------
        matchObj = re.search(r"([\d\.]+)", basename)
        if matchObj:
            pixel_ratio = float(matchObj.group(0))  # cast the retina ratio to a number.

        print "Pixel ratio: \t%.2f (determined by directory name)" % (pixel_ratio)

        # If we're making a different image ratio, we don't want the 1.5x or
        # 2x or 0.5x in the filename
        # ---------------------------------------------------------------------
        if(pixel_ratio != 1):
            options.css_namespace = re.sub("-", "_", re.sub(r"(-[\d\.]+x)", "", basename))

        #
        # Enumerate some filenames
        # ---------------------------------------------------------------------
        css_file = options.filename_prefix + options.output_filename + "." + css_extension
        img_file = options.filename_prefix + options.output_filename + "." + img_extension
        test_file = options.filename_prefix + options.output_filename + ".html"

        #
        # Set the relative path to the sprite from the generated CSS file
        # ---------------------------------------------------------------------
        path_to_sprite_from_css = os.path.relpath(options.sprite_dir, options.css_dir) + "/" + img_file


        if(options.test_page==True):
            options.test_page = options.css_dir + "/" + test_file

        # If we're using SaSS, point the url to the sass project output dir
        # ---------------------------------------------------------------------
        if(options.sass_dir != ""):
            print "\nInfo: You're using SaSS. Image URL is relative to final css_dir"
           # print "Image URL:\t" + path_to_sprite_from_css
            options.css_dir = options.sass_dir


        # Once the sass/css voodoo is done, set the real file output locations
        # ---------------------------------------------------------------------
        output_sprite_file = options.sprite_dir + "/" + img_file
        output_css_file = options.css_dir + "/" + css_file

        # Get some images
        # ---------------------------------------------------------------------
        images = get_images(options.input_dir)
        sorted_images = sort_images_by_size(images)

        # Max dimensions
        max_dim = ()

        # Set the packing mode
        # ---------------------------------------------------------------------
        if (options.mode != "grow"):
            dim_strings = options.mode.split("x")
            if (len(dim_strings) != 2):
                raise Exception("Invalid packing mode")
            try:
                max_dim = (int(dim_strings[0]), int(dim_strings[1]))
            except ValueError:
                raise Exception("Invalid packing mode")

        # Pack the images
        # ---------------------------------------------------------------------
        image_packing = pack_images(sorted_images, not max_dim, max_dim)

        # Generate a sprite sheet
        # ---------------------------------------------------------------------
        generate_sprite_sheet(image_packing, output_sprite_file, output_css_file, options.css_namespace, options.pad, path_to_sprite_from_css, pixel_ratio, options.test_page)

    # Return on errors
    except Exception as e:
        print "\nError: %s" % e
        return

    # Print a report of our activites to the console
    print "\nPacked: \t%s\nGenerated:\t%s\n\t\t%s\n" % \
        (options.input_dir, output_sprite_file, output_css_file)
    # Go!
    # ---------------------------------------------------------------------

if __name__ == '__main__':
    main()