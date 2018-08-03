import FreeCAD as App

try:
    rev_number = int(App.Version()[2].split(" ")[0])
except Exception as err:
    rev_number = 10000000
    del err

attach_extension_era = rev_number >= 9177

del App