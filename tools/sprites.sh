#!/bin/bash
#------------------------------------------------------------------------------
cd "$(dirname "${BASH_SOURCE[0]}")"
CONFIG="./config.sh"
#------------------------------------------------------------------------------

# Make sure python is 2.6 or later
PYTHON_OK=`python -c 'import sys
print (sys.version_info >= (2, 6) and "1" or "0")'`

if [ "$PYTHON_OK" = '0' ]; then
    echo ""
    echo "Oops. Sprites requires python 2.6 or higher."
    echo "http://www.python.org/getit/"
    echo ""
    exit
fi

echo "---------------------------------------------------------"
echo "Building Sprites..."
echo "---------------------------------------------------------"

if [ -f $CONFIG ]; then
    source $CONFIG
else
    echo "Error: Couldn't find [project]/config/config.sh"
    exit;
fi

# Vars
SASS_FILE=$sprite_sass_output_dir/${sprite_sass_file}
SASS_FILE_TEMP=$sprite_sass_output_dir/_temp_${sprite_sass_file}
TEMP_CSS_FILES=$sprite_sass_output_dir/*.css


# If we pass in clean as the param, nuke all the generated sprites
if [ "$1" == "clean" ]
then
    # Generate an array of all the filenames in the scss file.
    # echo "cleaned all sprites"
    if [ -f $SASS_FILE ]
      then
            files=$(sed 's/url\((.*?)\)//' $SASS_FILE | grep -oi '[A-Z0-9@-\.]*\.png')
            arr=($files)

            # read into array and check if file exists before calling rm
            if [ -z "$arr" ]
                then
                    # do nothing
                    echo "No sprite image files to delete"
                else
                    for i in "${arr[@]}"
                    do
                        temp_rm_path=$sprite_output_dir/$i
                        echo "Removed" $temp_rm_path;
                        if [ -f "$temp_rm_path" ]
                            then
                            rm $temp_rm_path
                        fi
                    done
            fi

            echo "Removed" $SASS_FILE
            rm -f $SASS_FILE
        else
            echo "No files to remove. Squeaky clean."
    fi
    exit
fi

subdircount=$(find $sprite_input_dir -maxdepth 1 -type d | wc -l)

if [ $subdircount -ge 2 ]; then
    echo ""
else
    echo "Oops. You'll need to drop your sprite images in a sub-folder for each pixel aspect ratio."
    printf "\nEg: sprites/\n"
    echo "          base/           (the 1x has no prefix)"
    echo "          base-0.75x/     (smaller than 1x for poxy androids)"
    echo "          base-1.5x/      (android pseudo-retina)"
    echo "          base-2x/        (true retina)"
    echo ""
    exit
fi

for _ief in $sprite_input_dir/*; do
    if [ -e "$_ief" ]; then
        echo "Found sprite dir: " $_ief

        files=(`find $_ief -maxdepth 1 -name "*.png"`)

        if [ ${#files[@]} -gt 0 ]; 
            then 
                python pypacker.py -i $_ief -c $sprite_css_output_dir -a $sprite_sass_output_dir -s $sprite_output_dir  -m grow --test
            else
                echo ""
                echo "Skipping $_ief because it's empty."
                echo "Put some .png images in the directory to make a sprite."
                echo ""
        fi
    else
        echo "You need images to make a sprite, fool."
    fi
done


if hash pngcrush 2>/dev/null; then
    fat_sprites=($sprite_output_dir/sprite_*.png)

    echo "Info: We have PNG Crush. Crush him!"
    echo "---------------------------------------------------------"
    for _sprite in ${fat_sprites[@]}; do
        pngcrush -rem alla -reduce $_sprite $_sprite".tmp"
        mv -f $_sprite".tmp" $_sprite
    done
else
    echo ""
fi



temp_css_files=$(ls $TEMP_CSS_FILES 2> /dev/null | wc -l)

if [  **"$temp_css_files" != "0"** ]
    then        
        # Concat the CSS into a single file
        rm -f $SASS_FILE
        printf "/**\n * ----------------------------------------\n * Sprites\n * ----------------------------------------\n */\n\n" > $SASS_FILE

        if [ "$OS" == "mac_osx" ]; then
            (ls -d $TEMP_CSS_FILES | sort -n -t _ -k 2 | xargs cat) >> $SASS_FILE   # for Linux, use sort -V, for OSX use sort -n
        fi;

        if [ "$OS" == "linux" ]; then
            (ls -d $TEMP_CSS_FILES | sort -V -t _ -k 2 | xargs cat) >> $SASS_FILE   # for Linux, use sort -V, for OSX use sort -n
        fi;

        
        # Clean up after that damn cat
        rm -f $TEMP_CSS_FILES

    else
        echo "Sorry, couldn't find any output CSS. Exiting."
        exit
fi

# -----------------------------------------------------------------------------

if [[ -n $sprite_test_page ]]
    then
    temp=$SASS_FILE".temp"
    temp2=$SASS_FILE".temp2"
    
    rm -f $temp2 $sprite_test_page
    
    relative_path=${sprite_output_dir#$sprite_test_page_dir/}

    echo "Finished making sprites."
    echo "---------------------------------------------------------"
    echo "Test page: $sprite_test_page"
    echo ""

    # strip the CSS images paths out, and replace them with a path relative
    # to the location of the sprites_test_page.html
    # 
    styles=$(cat $SASS_FILE | sed -e 's,\.\.\/'$IMG_DIR','$relative_path',g')

    # Make an HTML test page.
    html="<!doctype html>
<html>
    <head>
        <title>Sprite test sheet</title>
        <style type='text/css'>
            body{
                font-family:sans-serif;
                color: #333;
                background-image: url(data:image/png;base64,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);
            }
            .sprite_list{
                list-style:none;
            }
            .sprite_list li {
                margin-bottom: 1em;
                padding-bottom: 1em;
                border-bottom: solid 1px #eee;
            }
            .sprite_list li > p {
                font-size: .875em;
            }
            .test_sprite{
                display:block;
            }
            
            $styles

        </style>
    </head>
    <body>
        <!-- sprites -->
        <ul class='sprite_list'>
"

    # parse the lines out into a file via a Glob.
    while read line
    do
        if [[ "$line" = .* ]]
            then

            # print all the children of the sprite
            if [[ $line =~ _[^_]*_ ]]
                then
                echo "${line//[\.\{\,]/}" >> $temp;
            # else            
                # This is the actual icon name which only has one underscore, so don't print it.
            fi 

            
        fi    
    done < "$SASS_FILE"

    # Sort the lines
    awk '!x[$0]++' $temp > $temp2

    # read the lines back in and make a div for each of the selectors.
    while read line
    do

        html+="        <li>
                <p>.$line</p>
                <div class='test_sprite $line'></div>
            </li>
    "
    done < $temp2

    rm -f $temp $temp2

    html+="     </ul><!-- end sprites -->
    </body>
</html>"

    # Save the test page
    echo "$html" > $sprite_test_page
fi

# -----------------------------------------------------------------------------

