import FreeCAD as App

def get_fc_version():
    """returns tuple like (0,18,4,16154) for 0.18.4 release, and (0,19,0,18234) for pre builds"""
    # ['0', '18', '4 (GitTag)', 'git://github.com/FreeCAD/FreeCAD.git releases/FreeCAD-0-18', '2019/10/22 16:53:35', 'releases/FreeCAD-0-18', '980bf9060e28555fecd9e3462f68ca74007b70f8']
    # ['0', '19', '18234 (Git)', 'git://github.com/FreeCAD/FreeCAD.git master', '2019/09/15 20:43:17', 'master', '3af5d97e9b2a60823815f662aba25422c4bc45bb']
    strmaj, strmi, strrev = App.Version()[0:3]
    maj, mi = int(strmaj), int(strmi)
    submi, rev = 0, 0
    if '(GitTag)' in strrev:
        submi = int(strrev.split(" ")[0])
    elif '(Git)' in strrev:
        try:
            rev = int(strrev.split(" ")[0])
        except Exception as err:
            App.Console.PrintWarning(u"Lattice2 failed to detect FC version number.\n"
                                     "    {err}\n".format(err= str(err)))
            rev = 19207 #assume fairly modern
    if rev < 100:
        if mi == 17:
            rev = 13544
        elif mi == 18:
            rev = 16154
        else:
            rev = 19207 #assume fairly modern
            App.Console.PrintWarning(u"Lattice2 failed to detect FC version number: revision is zero / too low, minor version is unexpected.")
    return (maj, mi, submi, rev)


try:
    rev_number = get_fc_version()[3]
except Exception as err:
    App.Console.PrintError(str(err))
    rev_number = 10000000

attach_extension_era = rev_number >= 9177

del App