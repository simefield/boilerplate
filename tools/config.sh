#!/bin/bash

# ---------------------------------------------
# Front-end utilities
# ---------------------------------------------
# 
# Contents:
#       1. General config
#       2. SpriteBlaster 2000™
#       3. Compass/SaSS
#       4. JS Uglifier
#   
# 
# ---------------------------------------------
# 1. General config
# ---------------------------------------------
# 
# We've hacked the config.rb file so it reads these
# by default. That way, everything is configured in 
# one place. If it can't find config.sh, it'll 
# use the defaults in config.rb
# 
# ---------------------------------------------

    ENV="production"        # `production` or `development`
    OS="mac_osx"              # `mac_osx` or `linux`

# ---------------------------------------------

    ROOT_PATH="../"         # relative to the tools directory
    HTTP_PATH="/";          # relative to the web root in production
    ASSETS_DIR="www/" # relative to root_path
    IMG_DIR="images";       # relative to assets
    # SASS_DIR="sass"         # relative to assets
    SASS_DIR="css"         # relative to assets
    CSS_DIR="css"           # relative to assets
    FONTS_DIR="fonts"       # relative to assets
    SCRIPTS_DIR="js"        # relative to assets

    # Set this default to save us some repetitive
    # typing further on in the file
    ASSETS=$ROOT_PATH$ASSETS_DIR;

# ---------------------------------------------
# 2. SpriteBlaster
# ---------------------------------------------
# 
# Sprites expects a single flat folder containing
# all the sprite source images. Eg:
#
# [sprite_input_dir]
#       => sprite_dir
#       => sprite_dir_1.33x
#       => sprite_dir_1.5x
#       => sprite_dir_2x
#       => some_other_sprite_dir
#       => some_other_sprite_dir_2x
#       
# ---------------------------------------------

    # The image input directory
    sprite_input_dir=$ASSETS/$IMG_DIR/"sprites";

    # Where images are output
    sprite_output_dir=$ASSETS/$IMG_DIR;

    # Where CSS is served from. This is used to work out the background-url
    # relative to the CSS_DIR.
    sprite_css_output_dir=$ASSETS/$CSS_DIR;

    # Where SaSS expects to find the sprite CSS
    sprite_sass_output_dir=$ASSETS/$SASS_DIR/"sprites";

    # What the concatenated sprite css file is called
    sprite_sass_file="_sprites.scss"

    # a test page to review all the sprites in one handy place
    sprite_test_page_dir=$ASSETS

    # actual name of sprite test page.
    sprite_test_page=$sprite_test_page_dir/"sprite_test_page.html"
