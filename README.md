# ImportC2D
An Inkscape input extension to add support for Carbide Create C2D files to the File/Import... dialog.

* The stock as defined in Carbide Create is included in the import.
* All drawing objects from the C2D file are imported.
* Grouping from Carbide Create is fully preserved.
* Text is supported if the C2D file has been saved from a recent enough version of Carbide Create.
    * If the text cannot be imported, you will be notified.
    * To make the text import, just open the file with a current copy of Carbide Create (e.g. 316 or later) and save.
* No toolpath information is imported.

## Installation

1. Download the extension (ImportC2D.zip contains the two extension files, `c2d_input.inx` and `c2d_input.py`).
2. In Inkscape, go to the "Edit" menu and click "Preferences" (Shift-Ctrl-P).
3. On the left side, click "System".
4. Copy the location listed in the box labeled "Inkscape extensions:".
5. Close Inkscape.  (It only checks for extensions when it starts up.)
6. Copy the two files, `c2d_input.inx` and `c2d_input.py`, to the "Inkscape extensions:" location.
    > You may be asked for permission to copy the files there.  This is normal and is the computer just making sure you're not doing something you don't intend to do.

## Importing Carbide Create C2D Files

1. In Inkscape, go to the "File" menu and click "Import..." (Ctrl-I).
2. To see *only* Carbide Create C2D files, choose "Carbide Create file (*.c2d)" from the file type dropdown menu.
3. Choose whether to "Import all shapes as paths."
    * **Checked:** All objects in the C2D file are imported as SVG paths.
    * **Unchecked:** Circles, plain rectangles, and rectangles with simple rounded corners are imported as SVG shapes.  All other objects are imported as SVG paths.
    * If in doubt, leave it checked.  If not in doubt, probably leave it checked, too.
4. Click "OK".
