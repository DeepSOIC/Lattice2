#***************************************************************************
#*                                                                         *
#*   Copyright (c) 2016 - Victor Titov (DeepSOIC)                          *
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

__title__="Attachable placement feature module for lattice workbench for FreeCAD"
__author__ = "DeepSOIC"
__url__ = ""

import math

import FreeCAD as App
import Part

from lattice2Common import *
import lattice2BaseFeature

def makeAttachablePlacement(name):
    '''makePlacement(name): makes a Placement object.'''
    obj = FreeCAD.ActiveDocument.addObject("Part::AttachableObjectPython",name)
    AttachablePlacement(obj)
    ViewProviderAttachablePlacement(obj.ViewObject)        
    return obj

class AttachablePlacement(lattice2BaseFeature.LatticeFeature):
    "The Lattice Placement object"
    
    def derivedInit(self,obj):
        self.Type = "AttachablePlacement"
        
        obj.ExposePlacement = True
        obj.setEditorMode("ExposePlacement", 1) #read-only
        
    def derivedExecute(self,obj):
        obj.positionBySupport()
        
        return [obj.Placement]


class ViewProviderAttachablePlacement(lattice2BaseFeature.ViewProviderLatticeFeature):
        
    def getIcon(self):
        return getIconPath('Lattice2_AttachablePlacement.svg')

    def setEdit(self,vobj,mode):
        import PartGui
        PartGui.AttachmentEditor.editAttachment(self.Object)
        return True
    
    def unsetEdit(self,vobj,mode):
        import FreeCADGui as Gui
        Gui.Control.closeDialog()
        return True

# -------------------------- /document object --------------------------------------------------

# -------------------------- Gui command --------------------------------------------------

def CreateAttachablePlacement(name):
    sel = FreeCADGui.Selection.getSelectionEx()
    FreeCAD.ActiveDocument.openTransaction("Create Attachable Placement")
    FreeCADGui.addModule("lattice2AttachablePlacement")
    FreeCADGui.addModule("lattice2Executer")
    FreeCADGui.doCommand("f = lattice2AttachablePlacement.makeAttachablePlacement(name='"+name+"')")    
    FreeCADGui.doCommand("lattice2Executer.executeFeature(f)")    
    FreeCADGui.doCommand("PartGui.AttachmentEditor.editAttachment(f, take_selection= True,"
                                                                  "create_transaction= False,"
                                                                  "callback_OK= lambda: App.ActiveDocument.commitTransaction(),"
                                                                  "callback_Cancel= lambda: App.ActiveDocument.abortTransaction())")
    FreeCAD.ActiveDocument.commitTransaction()

class CommandAttachablePlacement:
    "Command to create Lattice Placement feature"
        
    def __init__(self):
        pass
    
    def GetResources(self):
        return {'Pixmap'  : getIconPath("Lattice2_AttachablePlacement.svg"),
                'MenuText': QtCore.QT_TRANSLATE_NOOP("Lattice2_Placement","Attached Placement") , 
                'Accel': "",
                'ToolTip': QtCore.QT_TRANSLATE_NOOP("Lattice2_Placement","Attached Placement: create Lattice Placement attached to geometry")}
        
    def Activated(self):
        try:
            CreateAttachablePlacement(name= "Placment")
        except Exception as err:
            msgError(err)
            
    def IsActive(self):
        if FreeCAD.ActiveDocument:
            return True
        else:
            return False

FreeCADGui.addCommand("Lattice2_AttachedPlacement", CommandAttachablePlacement())
exportedCommands = ["Lattice2_AttachedPlacement"]
# -------------------------- /Gui command --------------------------------------------------
