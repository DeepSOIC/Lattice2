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

def translate(context, text, disambig):
    #Lattice2 is not translatable, sorry...
    return text


def getParamRefine():
    return FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/Part/Boolean").GetBool("RefineModel")

def getIconPath(icon_dot_svg):
    return ":/icons/" + icon_dot_svg

class SelectionError(FreeCAD.Base.FreeCADError):
    '''Error that isused inside Gui command code'''
    def __init__(self, title, message):
        self.message = message
        self.args = (message,)
        self.title = title
        
def msgError(err):
    #if type(err) is CancelError: return   # doesn't work! Why!
    if hasattr(err, "isCancelError") and err.isCancelError: return   #workaround
    mb = QtGui.QMessageBox()
    mb.setIcon(mb.Icon.Warning)
    mb.setText(str(err))
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
        
# OCC's Precision::Confusion; should have taken this from FreeCAD but haven't found; unlikely to ever change.
DistConfusion = 1e-7
ParaConfusion = 1e-8

if FreeCAD.GuiUp:
    import lattice2_rc

def screen(feature):
    """screen(feature): protects link properties from being overwritten. 
    This is to be used as workaround for a bug where modifying an object accessed through 
    a link property of another object results in the latter being touched.
    
    returns: feature"""
    if not hasattr(feature,"isDerivedFrom"):
        return feature
    if not feature.isDerivedFrom("App::DocumentObject"):
        return feature
    if feature.Document is None:
        return feature
    feature = getattr(feature.Document, feature.Name)
    return feature

def activeBody():
    return FreeCADGui.ActiveDocument.ActiveView.getActiveObject("pdbody")
