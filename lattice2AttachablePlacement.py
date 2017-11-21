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
import lattice2Subsequencer as Subsequencer

def makeAttachablePlacement(name):
    '''makeAttachablePlacement(name): makes an attachable Placement object.'''
    rev_number = int(App.Version()[2].split(" ")[0])
    if rev_number < 9177:
        #obsolete!
        obj = FreeCAD.ActiveDocument.addObject("Part::AttachableObjectPython",name)
    else:
        obj = FreeCAD.ActiveDocument.addObject("Part::FeaturePython",name)
        obj.addExtension("Part::AttachExtensionPython", None)
    AttachablePlacement(obj)
    ViewProviderAttachablePlacement(obj.ViewObject)        
    return obj

class AttachablePlacement(lattice2BaseFeature.LatticeFeature):
    "Attachable Lattice Placement object"
    
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
        import FreeCADGui as Gui
        PartGui.AttachmentEditor.editAttachment(self.Object, 
                                                callback_OK= lambda: Gui.ActiveDocument.resetEdit(),
                                                callback_Cancel= lambda: Gui.ActiveDocument.resetEdit())
        return True
    
    def unsetEdit(self,vobj,mode):
        import FreeCADGui as Gui
        Gui.Control.closeDialog()
        return True


def makeLatticeAttachedPlacementSubsequence(name):
    '''makeLatticeAttachedPlacementSubsequence(name): makes a AttachedPlacementSubsequence object.'''
    return lattice2BaseFeature.makeLatticeFeature(name, AttachedPlacementSubsequence, ViewProviderAttachedPlacementSubsequence)

class AttachedPlacementSubsequence(lattice2BaseFeature.LatticeFeature):
    "Array Maker from Attachable Lattice Placement"
    
    def derivedInit(self,obj):
        self.Type = "AttachablePlacementSubsequence"
        
        obj.ExposePlacement = False
        obj.setEditorMode("ExposePlacement", 1) #read-only
        
        obj.addProperty("App::PropertyLink", "Base", "Lattice Attached Placement Subsequence", "Link to Lattice Attached Placement, which is to be subsequenced.")
        obj.addProperty("App::PropertyString", "RefIndexFilter","Lattice Attached Placement Subsequence","Sets which references of attachment to cycle through children. '0000' = no cycle, '1000' = cycle only ref1. '' = cycle all if possible")
        obj.addProperty("App::PropertyEnumeration", "CycleMode","Lattice Attached Placement Subsequence", "How to cycle through chidren. Open = advance each link till one reaches the end of array. Periodic = if array end reached, continue from begin if any children left.")
        obj.CycleMode = ['Open','Periodic']
        
    def derivedExecute(self,obj):
        attacher = Part.AttachEngine(screen(obj.Base).AttacherType)
        attacher.readParametersFromFeature(screen(obj.Base))
        i_filt_str = obj.RefIndexFilter
        ifilt = None if i_filt_str == "" else [i for i in range(len(i_filt_str)) if int(i_filt_str[i]) != 0]
        sublinks = Subsequencer.Subsequence_auto(attacher.References, 
                                                 loop= ('Till end' if obj.CycleMode == 'Open' else 'All around'), 
                                                 index_filter= ifilt)
        plms = []
        for lnkval in sublinks:
            attacher.References = lnkval
            plms.append(attacher.calculateAttachedPlacement(screen(obj.Base).Placement))
        return plms

class ViewProviderAttachedPlacementSubsequence(lattice2BaseFeature.ViewProviderLatticeFeature):
    def getIcon(self):
        return getIconPath('Lattice2_AttachedPlacementSubsequence.svg')

    def claimChildren(self):
        return [screen(self.Object.Base)]

# -------------------------- /document object --------------------------------------------------

# -------------------------- Gui command --------------------------------------------------

def CreateAttachablePlacement(name):
    sel = FreeCADGui.Selection.getSelectionEx()
    FreeCAD.ActiveDocument.openTransaction("Create Attachable Placement")
    FreeCADGui.addModule("lattice2AttachablePlacement")
    FreeCADGui.addModule("lattice2Executer")
    FreeCADGui.addModule("PartGui")
    FreeCADGui.doCommand("f = lattice2AttachablePlacement.makeAttachablePlacement(name='"+name+"')")    
    FreeCADGui.doCommand("lattice2Executer.executeFeature(f)")    
    FreeCADGui.doCommand("PartGui.AttachmentEditor.editAttachment(f, take_selection= True,"
                                                                  "create_transaction= False,"
                                                                  "callback_OK= lambda: App.ActiveDocument.commitTransaction(),"
                                                                  "callback_Cancel= lambda: App.ActiveDocument.abortTransaction())")
    FreeCAD.ActiveDocument.commitTransaction()

def cmdCreateAttachedPlacementSubsequence(name):
    sel = FreeCADGui.Selection.getSelectionEx()
    FreeCAD.ActiveDocument.openTransaction("Array an attached placement")
    FreeCADGui.addModule("lattice2AttachablePlacement")
    FreeCADGui.addModule("lattice2Executer")
    FreeCADGui.doCommand("f = lattice2AttachablePlacement.makeLatticeAttachedPlacementSubsequence(name='"+name+"')")    
    FreeCADGui.doCommand("f.Base = App.ActiveDocument."+sel[0].Object.Name)
    FreeCADGui.doCommand("f.Base.ViewObject.hide()")
    FreeCADGui.doCommand("lattice2Executer.executeFeature(f)")    
    FreeCAD.ActiveDocument.commitTransaction()
    FreeCADGui.doCommand("Gui.Selection.addSelection(f)")
    deselect(sel)

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

class CommandAttachedPlacementSubsequence:
    "Command to convert a attached placement into an array"
        
    def __init__(self):
        pass
    
    def GetResources(self):
        return {'Pixmap'  : getIconPath("Lattice2_AttachedPlacementSubsequence.svg"),
                'MenuText': QtCore.QT_TRANSLATE_NOOP("Lattice2_Placement","Array an attached placement") , 
                'Accel': "",
                'ToolTip': QtCore.QT_TRANSLATE_NOOP("Lattice2_Placement","Attached Placement: makes an array of placements from an attached placement by cycling attachment references...")}
        
    def Activated(self):
        try:
            sel = FreeCADGui.Selection.getSelectionEx()
            if len(sel) == 0:
                infoMessage("Attached Placement Subsequence",
                            "Attached Placement Subsequence feature: makes an array of placements from an attached placement by cycling attachment references through children of an array the placement is attached to."+
                            "\n\nPlease select an attached placement object, first. Then invoke this tool. Adjust the properties of the created object if necessary."                          )
            else:
                if len(sel)!=1:
                    raise SelectionError("PlacementSubsequence", "Please select just one object, an attached placement. You have seleced {num}.".format(num= len(sel)))
                cmdCreateAttachedPlacementSubsequence(name= "PlacementSubsequence")
        except Exception as err:
            msgError(err)
            
    def IsActive(self):
        if FreeCAD.ActiveDocument:
            return True
        else:
            return False

FreeCADGui.addCommand("Lattice2_AttachedPlacement", CommandAttachablePlacement())
FreeCADGui.addCommand("Lattice2_AttachedPlacementSubsequence", CommandAttachedPlacementSubsequence())

class CommandAttachedPlacementGroup:
    def GetCommands(self):
        return ("Lattice2_AttachedPlacement","Lattice2_AttachedPlacementSubsequence") 

    def GetDefaultCommand(self): # return the index of the tuple of the default command. 
        return 0

    def GetResources(self):
        return { 'MenuText': 'Attached Placement:', 
                 'ToolTip': 'Attached Placement (group): tools to work with attached placement objects.'}
        
    def IsActive(self): # optional
        return App.ActiveDocument is not None

FreeCADGui.addCommand("Lattice2_AttachedPlacement_Group", CommandAttachedPlacementGroup())

exportedCommands = ["Lattice2_AttachedPlacement_Group"]
# -------------------------- /Gui command --------------------------------------------------
