#***************************************************************************
#*                                                                         *
#*   Copyright (c) 2015 - Victor Titov (DeepSOIC)                          *
#*                                               <vv.titov@gmail.com>      *  
#*                                                                         *
#*   This program is free software; you can redistribute it and/or modify  *
#*   it under the terms of the GNU Lesser General Public License (LGPL)    *
#*   as published by the Free Software Foundation; either version 2 of     *
#*   the License, or (at your option) any later version.                   *
#*   for detail see the LICENCE text file.                                 *
#*                                                                         *
#*   This program is distributed in the hope that it will be useful,       *
#*   but WITHOUT ANY WARRANTY; without even the implied warranty of        *
#*   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
#*   GNU Library General Public License for more details.                  *
#*                                                                         *
#*   You should have received a copy of the GNU Library General Public     *
#*   License along with this program; if not, write to the Free Software   *
#*   Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  *
#*   USA                                                                   *
#*                                                                         *
#***************************************************************************

import FreeCAD, Part
from lattice2Executer import CancelError
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
    def translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)
#--------------------------/translation-related code ----------------------------------------


def getParamRefine():
    return FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/Part/Boolean").GetBool("RefineModel")

def getIconPath(icon_dot_svg):
    return ":/icons/" + icon_dot_svg

class SelectionError(FreeCAD.Base.FreeCADError):
    '''Error that isused inside Gui command code'''
    def __init__(self, title, message):
        self.message = message
        self.title = title
        
def msgError(err):
    #if type(err) is CancelError: return   # doesn't work! Why!
    if hasattr(err, "isCancelError") and err.isCancelError: return   #workaround
    mb = QtGui.QMessageBox()
    mb.setIcon(mb.Icon.Warning)
    mb.setText(err.message)
    if type(err) is SelectionError:
        mb.setWindowTitle(err.title)
    else:
        mb.setWindowTitle("Error")
    mb.exec_()

def infoMessage(title, message):
    mb = QtGui.QMessageBox()
    mb.setIcon(mb.Icon.Information)
    mb.setText(message)
    mb.setWindowTitle(title)
    mb.exec_()

def deselect(sel):
    '''deselect(sel): remove objects in sel from selection'''
    for selobj in sel:
        FreeCADGui.Selection.removeSelection(selobj.Object)
        
def shallow_copy(shape):
    copiers = {
      "Vertex": lambda(sh): sh.Vertexes[0],
      "Edge": lambda(sh): sh.Edges[0],
      "Wire": lambda(sh): sh.Wires[0],
      "Face": lambda(sh): sh.Faces[0],
      "Shell": lambda(sh): sh.Shells[0],
      "Solid": lambda(sh): sh.Solids[0],
      "CompSolid": lambda(sh): sh.CompSolids[0],
      "Compound": lambda(sh): sh.Compounds[0],
      }
    copier = copiers.get(shape.ShapeType)
    if copier is None:
        copier = lambda(sh): sh.copy()
        FreeCAD.Console.PrintWarning("Lattice2: shallow_copy: unexpected shape type '{typ}'. Using deep copy instead.\n".format(typ= shape.ShapeType))
    return copier(shape)

# OCC's Precision::Confusion; should have taken this from FreeCAD but haven't found; unlikely to ever change.
DistConfusion = 1e-7
ParaConfusion = 1e-8

import lattice2_rc