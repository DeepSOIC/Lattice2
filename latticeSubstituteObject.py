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

__title__="Lattice SubstituteObject command module"
__author__ = "DeepSOIC"

import FreeCAD as App

from replaceobj import replaceobj #from OpenSCAD wb, the code that drives replaceChild
from latticeCommon import *

def substituteobj(oldobj, newobj):
    'Replaces all links to oldobj in the document with links to newobj'
    for dep in oldobj.InList:
        replaceobj(dep, oldobj, newobj)
    return len(oldobj.OutList)
        
class CommandSubstituteObject:
    "Command to substitute object"
    def GetResources(self):
        return {'Pixmap'  : getIconPath("Lattice_SubstituteObject.svg"),
                'MenuText': QtCore.QT_TRANSLATE_NOOP("Lattice_SubstituteObject","Substitute object"),
                'Accel': "",
                'ToolTip': QtCore.QT_TRANSLATE_NOOP("Lattice_SubstituteObject","Substitute Object: find all links to one of the selected objects, and rediret them all to another object")}
        
    def Activated(self):
        sel = FreeCADGui.Selection.getSelectionEx()
        if len(sel) == 2 :
            App.ActiveDocument.openTransaction("Substitute "+sel[0].ObjectName+" with "+sel[1].ObjectName)
            try:
                #do it
                if len(sel[0].Object.InList) == 0:
                    raise ValueError("First selected object isn't referenced by anything; nothing to do.")
                substituteobj(sel[0].Object, sel[1].Object)
                App.ActiveDocument.commitTransaction()
                
                #verify results: oldobject should not be referenced by anything anymore.
                if len(sel[0].Object.InList) != 0:
                    mb = QtGui.QMessageBox()
                    mb.setIcon(mb.Icon.Warning)
                    msg = translate("Lattice_SubstituteObject", "Some of the links coudn't be redirected, because they are not supported by the tool. Objects still linking to the object that was replaced are: \n%1\nTo redirect these links, the objects have to be edited manually. Sorry!", None)
                    rem_links = [lnk.Label for lnk in sel[0].Object.InList]
                    mb.setText(msg.replace(u"%1", u"\n".join(rem_links)))
                    mb.setWindowTitle(translate("Lattice_SubstituteObject","Error", None))
                    mb.exec_()
                    
            except Exception as err:
                mb = QtGui.QMessageBox()
                mb.setIcon(mb.Icon.Warning)
                mb.setText(translate("Lattice_SubstituteObject", "An error occured while substituting object:", None)+ u"\n"
                               + unicode(err.message))
                mb.setWindowTitle(translate("Lattice_SubstituteObject","Error", None))
                mb.exec_()
                App.ActiveDocument.abortTransaction()
                return
            
            #hide/unhide
            try:
                old_was_visible = sel[0].Object.ViewObject.Visibility
                new_was_visible = sel[1].Object.ViewObject.Visibility
                sel[0].Object.ViewObject.Visibility = True
                sel[1].Object.ViewObject.Visibility = old_was_visible
            except Exception as err:
                App.Console.PrintError("SubstituteFeature: error when changing visibilities: "+err.message+"\n")
        else:
            mb = QtGui.QMessageBox()
            mb.setIcon(mb.Icon.Warning)
            mb.setText(translate("Lattice_SubstituteObject", "Select two objects, first! The first one is the one to be substituted, and the second one is the object to redirect all links to.", None))
            mb.setWindowTitle(translate("Lattice_SubstituteObject","Bad selection", None))
            mb.exec_()
            
    def IsActive(self):
        if FreeCAD.ActiveDocument:
            return True
        else:
            return False
            
FreeCADGui.addCommand('Lattice_SubstituteObject', CommandSubstituteObject())

exportedCommands = ['Lattice_SubstituteObject']
