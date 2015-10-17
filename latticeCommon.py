import FreeCAD, Part
if FreeCAD.GuiUp:
    import FreeCADGui
    from PySide import QtCore, QtGui

#-------------------------- translation-related code ----------------------------------------
#Thanks, yorik! (see forum thread "A new Part tool is being born... JoinFeatures!"
#http://forum.freecadweb.org/viewtopic.php?f=22&t=11112&start=30#p90239 )
try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s
try:
    _encoding = QtGui.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)
#--------------------------/translation-related code ----------------------------------------


def getParamRefine():
    return FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/Part/Boolean").GetBool("RefineModel")

def getIconPath(icon_dot_svg):
    return ":/icons/" + icon_dot_svg


# OCC's Precision::Confusion; should have taken this from FreeCAD but haven't found; unlikely to ever change.
DistConfusion = 1e-7

import lattice_rc