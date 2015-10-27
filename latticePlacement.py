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

__title__="Placement feature module for lattice workbench for FreeCAD"
__author__ = "DeepSOIC"
__url__ = ""

import math

import FreeCAD as App
import Part

from latticeCommon import *
import latticeBaseFeature

def makeLatticePlacement(name):
    '''makePlacement(name): makes a Placement object.'''
    return latticeBaseFeature.makeLatticeFeature(name, LatticePlacement,'Lattice_Placement.svg')

class LatticePlacement(latticeBaseFeature.LatticeFeature):
    "The Lattice Placement object"
    
    _PlacementChoiceList = ['Custom','XY plane', 'XZ plane', 'YZ plane']
    
    def derivedInit(self,obj):
        self.Type = "LatticePlacement"
        
        obj.addProperty("App::PropertyEnumeration","PlacementChoice","Lattice Placement","Choose one of standard placements here.")
        obj.PlacementChoice = self._PlacementChoiceList
        
        obj.addProperty("App::PropertyLength","Offset","Lattice Placement","Offset from oigin for XY/XZ/YZ plane modes")
        
        obj.addProperty("App::PropertyBool","FlipZ","Lattice Placement","Set to true to flip Z axis (also flips Y)")
        
        obj.addProperty("App::PropertyBool","Invert","Lattice Placement","Invert the placement")
        
    def updateReadOnlyness(self, obj):
        m = obj.PlacementChoice
        obj.setEditorMode("Placement", 0 if m == "Custom" else 1)        
        obj.setEditorMode("Offset", 1 if m == "Custom" else 0)        

    def derivedExecute(self,obj):
        # Fill in (update read-only) properties that are driven by the mode.
        self.updateReadOnlyness(obj)
        
        
        if obj.PlacementChoice == 'Custom':
            pass
        else:
            rot = App.Rotation()
            if obj.PlacementChoice == 'XY plane':
                pass
            elif obj.PlacementChoice == 'XZ plane':
                rot.Q = (-1.0, 0.0, 0.0, -1.0) #will get normalized by FC automatically
            elif obj.PlacementChoice == 'YZ plane':
                rot.Q = (0.5, 0.5, 0.5, 0.5) #will get normalized by FC automatically
            else:
                raise ValueError("latticePlacement: unsupported placement: "+obj.PlacementChoice)
            obj.Placement = App.Placement(rot.multVec(App.Vector(0,0,obj.Offset)), rot)
        if obj.FlipZ:
            obj.Placement = obj.Placement.multiply(App.Placement(App.Vector(),App.Rotation(App.Vector(1,0,0),180)))
            if obj.PlacementChoice == 'Custom':
                obj.FlipZ = False
        if obj.Invert:
            obj.Placement = obj.Placement.inverse()
            if obj.PlacementChoice == 'Custom':
                obj.Invert = False
        
        return [App.Placement()] #always return default placement, because Placement property is automatically applied on top of it.

# -------------------------- /common stuff --------------------------------------------------

# -------------------------- Gui command --------------------------------------------------

def CreateLatticePlacement(name,mode = 'Custom'):
    sel = FreeCADGui.Selection.getSelectionEx()
    FreeCAD.ActiveDocument.openTransaction("Create Lattice Placement")
    FreeCADGui.addModule("latticePlacement")
    FreeCADGui.doCommand("f = latticePlacement.makeLatticePlacement(name='"+name+"')")    
    FreeCADGui.doCommand("f.PlacementChoice = '"+mode+"'")
    FreeCADGui.doCommand("f.Proxy.execute(f)")
    FreeCADGui.doCommand("f.purgeTouched()")
    FreeCADGui.doCommand("f = None")
    FreeCAD.ActiveDocument.commitTransaction()


class _CommandPlacement:
    "Command to create Lattice Placement feature"
        
    def __init__(self, mode = 'Custom'):
        self.mode = mode
    
    def GetResources(self):
        return {'Pixmap'  : getIconPath("Lattice_Placement.svg"),
                'MenuText': QtCore.QT_TRANSLATE_NOOP("Lattice_Placement","Single Placement: ") + self.mode, # FIXME: not translation-friendly!
                'Accel': "",
                'ToolTip': QtCore.QT_TRANSLATE_NOOP("Lattice_Placement","Lattice Placement: Create lattice object with single item")}
        
    def Activated(self):
        CreateLatticePlacement(name= "Placement", mode= self.mode)
            
    def IsActive(self):
        if FreeCAD.ActiveDocument:
            return True
        else:
            return False

_listOfSubCommands = []
for mode in LatticePlacement._PlacementChoiceList: 
    cmdName = 'Lattice_Placement' + mode
    FreeCADGui.addCommand(cmdName, _CommandPlacement(mode))
    _listOfSubCommands.append(cmdName)
    

class GroupCommandPlacement:
    def GetCommands(self):
        global _listOfSubCommands
        return tuple(_listOfSubCommands) # a tuple of command names that you want to group

    def GetDefaultCommand(self): # return the index of the tuple of the default command. This method is optional and when not implemented '0' is used  
        return 0

    def GetResources(self):
        return { 'MenuText': 'Lattice Placement', 'ToolTip': 'Lattice Placement: Create lattice object with single item'}
        
    def IsActive(self): # optional
        return True
        
FreeCADGui.addCommand('Lattice_Placement_GroupCommand',GroupCommandPlacement())




exportedCommands = ['Lattice_Placement_GroupCommand']

# -------------------------- /Gui command --------------------------------------------------
