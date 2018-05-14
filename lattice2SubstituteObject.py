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
from lattice2Common import *

def getAllDependencies(feat):
    '''getAllDependencies(feat): gets all features feat depends on, directly or indirectly. Returns a list, with deepest dependencies last.'''
    list_traversing_now = [feat]
    set_of_deps = set()
    list_of_deps = []
    
    while len(list_traversing_now) > 0:
        list_to_be_traversed_next = []
        for feat in list_traversing_now:
            for dep in feat.OutList:
                if not (dep in set_of_deps):
                    set_of_deps.add(dep)
                    list_of_deps.append(dep)
                    list_to_be_traversed_next.append(dep)
        
        list_traversing_now = list_to_be_traversed_next
    
    return list_of_deps
    

def substituteobj(oldobj, newobj):
    '''Replaces all links to oldobj in the document with links to newobj.
    Returns a tuple (list_replaced, list_not_replaced)'''
    deps_of_new = getAllDependencies(newobj) + [newobj]
    list_not_replaced = []
    list_replaced = []
    for dep in oldobj.InList:
        if dep in deps_of_new:
            #we are about to make an object newobj depends on, to depend on newobj. 
            #This will create a circular graph, so we must skip this.
            print ("not replacing "+oldobj.Name+" with " + newobj.Name +" in " + dep.Name)
            list_not_replaced.append(dep)
        else:
            print ("replacing "+oldobj.Name+" with " + newobj.Name +" in " + dep.Name)
            list_replaced.append(dep)
            replaceobj(dep, oldobj, newobj)
    return (list_replaced, list_not_replaced)
        
class CommandSubstituteObject:
    "Command to substitute object"
    def GetResources(self):
        return {'Pixmap'  : getIconPath("Lattice2_SubstituteObject.svg"),
                'MenuText': QtCore.QT_TRANSLATE_NOOP("Lattice2_SubstituteObject","Substitute object"),
                'Accel': "",
                'ToolTip': QtCore.QT_TRANSLATE_NOOP("Lattice2_SubstituteObject","Substitute Object: find all links to one of the selected objects, and rediret them all to another object")}
        
    def Activated(self):
        sel = FreeCADGui.Selection.getSelectionEx()
        if len(sel) == 2 :
            App.ActiveDocument.openTransaction("Substitute "+sel[0].ObjectName+" with "+sel[1].ObjectName)
            try:
                #do it
                if len(sel[0].Object.InList) == 0:
                    raise ValueError("First selected object isn't referenced by anything; nothing to do.")
                dummy, list_not_replaced = substituteobj(sel[0].Object, sel[1].Object)
                App.ActiveDocument.commitTransaction()
                
                #verify results: oldobject should not be referenced by anything anymore.
                if len(sel[0].Object.InList) != 0:
                    set_failed = set(sel[0].Object.InList).difference(set(list_not_replaced))
                    mb = QtGui.QMessageBox()
                    if len(set_failed) > 0:
                        mb.setIcon(mb.Icon.Warning)
                        msg = translate("Lattice2_SubstituteObject", "Some of the links couldn't be redirected, because they are not supported by the tool. Link redirection failed for: \n%1\nTo redirect these links, the objects have to be edited manually. Sorry!", None)
                        rem_links = [lnk.Label for lnk in set_failed]
                    else:
                        mb.setIcon(mb.Icon.Information)
                        msg = translate("Lattice2_SubstituteObject", "The following objects still link to old object: \n%1\nReplacing those links would have caused loops in dependency graph, so they were skipped.", None)
                        rem_links = [lnk.Label for lnk in sel[0].Object.InList]
                    mb.setText(msg.replace(u"%1", u"\n".join(rem_links)))
                    mb.setWindowTitle(translate("Lattice2_SubstituteObject","Error", None))
                    mb.exec_()
                    
            except Exception as err:
                mb = QtGui.QMessageBox()
                mb.setIcon(mb.Icon.Warning)
                mb.setText(translate("Lattice2_SubstituteObject", "An error occured while substituting object:", None)+ u"\n"
                               + str(err))
                mb.setWindowTitle(translate("Lattice2_SubstituteObject","Error", None))
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
                App.Console.PrintError("SubstituteFeature: error when changing visibilities: "+str(err)+"\n")
        else:
            mb = QtGui.QMessageBox()
            mb.setIcon(mb.Icon.Warning)
            mb.setText(translate("Lattice2_SubstituteObject", "Select two objects, first! The first one is the one to be substituted, and the second one is the object to redirect all links to.", None))
            mb.setWindowTitle(translate("Lattice2_SubstituteObject","Bad selection", None))
            mb.exec_()
            
    def IsActive(self):
        if FreeCAD.ActiveDocument:
            return True
        else:
            return False
            
if FreeCAD.GuiUp:
    FreeCADGui.addCommand('Lattice2_SubstituteObject', CommandSubstituteObject())

exportedCommands = ['Lattice2_SubstituteObject']
