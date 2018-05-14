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

from lattice2Common import *
import lattice2BaseFeature

def makeLatticePlacement(name):
    '''makePlacement(name): makes a Placement object.'''
    return lattice2BaseFeature.makeLatticeFeature(name, LatticePlacement, ViewProviderLatticePlacement)

class LatticePlacement(lattice2BaseFeature.LatticeFeature):
    "The Lattice Placement object"
    
    _PlacementChoiceList = ['Custom','XY plane', 'XZ plane', 'YZ plane']
    
    def derivedInit(self,obj):
        self.Type = "LatticePlacement"
        
        obj.addProperty("App::PropertyEnumeration","PlacementChoice","Lattice Placement","Choose one of standard placements here.")
        obj.PlacementChoice = self._PlacementChoiceList
        
        obj.addProperty("App::PropertyLength","Offset","Lattice Placement","Offset from oigin for XY/XZ/YZ plane modes")
        
        obj.addProperty("App::PropertyBool","FlipZ","Lattice Placement","Set to true to flip Z axis (also flips Y)")
        
        obj.addProperty("App::PropertyBool","Invert","Lattice Placement","Invert the placement")
        
        obj.ExposePlacement = True
        
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
                raise ValueError("lattice2Placement: unsupported placement: "+obj.PlacementChoice)
            obj.Placement = App.Placement(rot.multVec(App.Vector(0,0,obj.Offset)), rot)
        if obj.FlipZ:
            obj.Placement = obj.Placement.multiply(App.Placement(App.Vector(),App.Rotation(App.Vector(1,0,0),180)))
            if obj.PlacementChoice == 'Custom':
                obj.FlipZ = False
        if obj.Invert:
            obj.Placement = obj.Placement.inverse()
            if obj.PlacementChoice == 'Custom':
                obj.Invert = False
        
        return [obj.Placement]

def makeLatticePlacementAx(name):
    '''makePlacement(name): makes a Placement object.'''
    return lattice2BaseFeature.makeLatticeFeature(name, LatticePlacementAx, ViewProviderLatticePlacement)

class LatticePlacementAx(lattice2BaseFeature.LatticeFeature):
    "The Lattice Placement object, defined by axes directions"
        
    def derivedInit(self,obj):
        self.Type = "LatticePlacementAx"
        
        obj.addProperty("App::PropertyEnumeration","Priority","Lattice Placement","Example: ZXY = ZDir followed strictly, XDir is a hint, YDir is ignored and computed from others.")
        obj.Priority = ["XYZ", "XZY", "YXZ", "YZX", "ZXY", "ZYX"]
        
        obj.addProperty("App::PropertyVector","XDir_wanted","Lattice Placement","Align X axis of placement with this direction.")
        obj.addProperty("App::PropertyVector","YDir_wanted","Lattice Placement","Align Y axis of placement with this direction.")
        obj.addProperty("App::PropertyVector","ZDir_wanted","Lattice Placement","Align Z axis of placement with this direction.")

        obj.addProperty("App::PropertyVector","XDir_actual","Lattice Placement","Actual resulting direction of X axis of the placement.")
        obj.addProperty("App::PropertyVector","YDir_actual","Lattice Placement","Actual resulting direction of Y axis of the placement.")
        obj.addProperty("App::PropertyVector","ZDir_actual","Lattice Placement","Actual resulting direction of Z axis of the placement.")

        obj.setEditorMode("XDir_actual", 1) #read-only
        obj.setEditorMode("YDir_actual", 1) #read-only
        obj.setEditorMode("ZDir_actual", 1) #read-only
        
        obj.ExposePlacement = True
        
    def derivedExecute(self,obj):
        old_pos = App.Vector()
        try:
            old_pos = lattice2BaseFeature.getPlacementsList(obj, suppressWarning= True)[0].Base
        except Exception:
            pass #retrieving position may fail if the object is recomputed for the very first time
        
        import lattice2GeomUtils
        
        ori = lattice2GeomUtils.makeOrientationFromLocalAxesUni(obj.Priority, obj.XDir_wanted * 1.0, obj.YDir_wanted * 1.0, obj.ZDir_wanted * 1.0) # multiply vectors by 1.0 to copy them, to block mutation
        
        plm =  App.Placement(old_pos, ori)
        
        obj.XDir_actual = ori.multVec(App.Vector(1,0,0))
        obj.YDir_actual = ori.multVec(App.Vector(0,1,0))
        obj.ZDir_actual = ori.multVec(App.Vector(0,0,1))
        
        return [plm]

def makeLatticePlacementEuler(name):
    '''makePlacement(name): makes a Placement object.'''
    return lattice2BaseFeature.makeLatticeFeature(name, LatticePlacementEuler, ViewProviderLatticePlacement)

class LatticePlacementEuler(lattice2BaseFeature.LatticeFeature):
    "The Lattice Placement object, defined by axes directions"
        
    def derivedInit(self,obj):
        self.Type = "LatticePlacementEuler"
                
        obj.addProperty("App::PropertyAngle","Yaw","Lattice Placement","Rotation around Z axis")
        obj.addProperty("App::PropertyAngle","Pitch","Lattice Placement","Rotation around Y axis")
        obj.addProperty("App::PropertyAngle","Roll","Lattice Placement","Rotation around X axis")

        obj.ExposePlacement = True
        
    def derivedExecute(self,obj):
        old_pos = App.Vector()
        try:
            old_pos = lattice2BaseFeature.getPlacementsList(obj, suppressWarning= True)[0].Base
        except Exception:
            pass #retrieving position may fail if the object is recomputed for the very first time
        
        ori = App.Rotation(obj.Yaw, obj.Pitch, obj.Roll)
        
        plm =  App.Placement(old_pos, ori)
        
        return [plm]

class ViewProviderLatticePlacement(lattice2BaseFeature.ViewProviderLatticeFeature):
        
    def getIcon(self):
        return getIconPath('Lattice2_Placement.svg')

# -------------------------- /document object --------------------------------------------------

# -------------------------- Gui command --------------------------------------------------

def CreateLatticePlacement(name,mode = 'Custom'):
    sel = FreeCADGui.Selection.getSelectionEx()
    FreeCAD.ActiveDocument.openTransaction("Create Lattice Placement")
    FreeCADGui.addModule("lattice2Placement")
    FreeCADGui.addModule("lattice2Executer")
    FreeCADGui.doCommand("f = lattice2Placement.makeLatticePlacement(name='"+name+"')")    
    FreeCADGui.doCommand("f.PlacementChoice = '"+mode+"'")
    FreeCADGui.doCommand("f.Label = '"+mode+"'")
    FreeCADGui.doCommand("lattice2Executer.executeFeature(f)")
    FreeCADGui.doCommand("Gui.Selection.addSelection(f)")
    FreeCADGui.doCommand("f = None")
    FreeCAD.ActiveDocument.commitTransaction()

def CreateLatticePlacementAx(label, priority, XDir, YDir, ZDir):
    sel = FreeCADGui.Selection.getSelectionEx()
    FreeCAD.ActiveDocument.openTransaction("Create Lattice Placement")
    FreeCADGui.addModule("lattice2Placement")
    FreeCADGui.addModule("lattice2Executer")
    name = "PlacementAx"
    FreeCADGui.doCommand("f = lattice2Placement.makeLatticePlacementAx(name='"+name+"')")    
    FreeCADGui.doCommand("f.Priority = "+repr(priority))
    if XDir is not None and XDir.Length > DistConfusion:
        FreeCADGui.doCommand("f.XDir_wanted = App.Vector"+repr(tuple(XDir)))
    if YDir is not None and YDir.Length > DistConfusion:
        FreeCADGui.doCommand("f.YDir_wanted = App.Vector"+repr(tuple(YDir)))
    if ZDir is not None and ZDir.Length > DistConfusion:
        FreeCADGui.doCommand("f.ZDir_wanted = App.Vector"+repr(tuple(ZDir)))
    FreeCADGui.doCommand("f.Label = "+repr(label))        
    FreeCADGui.doCommand("lattice2Executer.executeFeature(f)")
    FreeCADGui.doCommand("Gui.Selection.addSelection(f)")
    FreeCADGui.doCommand("f = None")
    FreeCAD.ActiveDocument.commitTransaction()

def CreateLatticePlacementEuler(name):
    sel = FreeCADGui.Selection.getSelectionEx()
    FreeCAD.ActiveDocument.openTransaction("Create Lattice Placement")
    FreeCADGui.addModule("lattice2Placement")
    FreeCADGui.addModule("lattice2Executer")
    FreeCADGui.doCommand("f = lattice2Placement.makeLatticePlacementEuler(name='"+name+"')")    
    FreeCADGui.doCommand("lattice2Executer.executeFeature(f)")
    FreeCADGui.doCommand("Gui.Selection.addSelection(f)")
    FreeCADGui.doCommand("f = None")
    FreeCAD.ActiveDocument.commitTransaction()


class _CommandPlacement:
    "Command to create Lattice Placement feature"
        
    def __init__(self, mode = 'Custom'):
        self.mode = mode
    
    def GetResources(self):
        return {'Pixmap'  : getIconPath("Lattice2_Placement_New.svg"),
                'MenuText': QtCore.QT_TRANSLATE_NOOP("Lattice2_Placement","Single Placement: ") + self.mode, # FIXME: not translation-friendly!
                'Accel': "",
                'ToolTip': QtCore.QT_TRANSLATE_NOOP("Lattice2_Placement","Lattice Placement: Create lattice object with single item")}
        
    def Activated(self):
        FreeCADGui.Selection.clearSelection() 
        CreateLatticePlacement(name= "Placment", mode= self.mode)
        if self.mode == "Custom":
            FreeCADGui.runCommand("Std_Placement")
            
    def IsActive(self):
        if FreeCAD.ActiveDocument:
            return True
        else:
            return False

_listOfSubCommands = []
for mode in LatticePlacement._PlacementChoiceList: 
    cmdName = 'Lattice2_Placement' + mode
    if FreeCAD.GuiUp:
        FreeCADGui.addCommand(cmdName, _CommandPlacement(mode))
    _listOfSubCommands.append(cmdName)
    
class _CommandPlacementAx:
    "Command to create Lattice Placement by axes feature"
        
    def __init__(self, menu_text, tooltip, label, priority, XDir = None, YDir = None, ZDir = None):
        self.menu_text = menu_text
        self.tooltip = tooltip
        self.label = label
        self.priority = priority
        self.XDir = XDir
        self.YDir = YDir
        self.ZDir = ZDir
        
    
    def GetResources(self):
        return {'Pixmap'  : getIconPath("Lattice2_Placement_New.svg"),
                'MenuText': "Single Placement: " + self.menu_text, # FIXME: not translation-friendly!
                'Accel': "",
                'ToolTip': self.tooltip}
        
    def Activated(self):
        try:
            FreeCADGui.Selection.clearSelection() 
            CreateLatticePlacementAx(self.label, self.priority, self.XDir, self.YDir, self.ZDir)
        except Exception as err:
            msgError(err)
            
    def IsActive(self):
        if FreeCAD.ActiveDocument:
            return True
        else:
            return False

cmdName = "Lattice2_PlacementAx_AlongX"
if FreeCAD.GuiUp:
    FreeCADGui.addCommand(cmdName, _CommandPlacementAx("along X","Single Placement with local X aligned along global X","Plm along X","XZY", XDir= App.Vector(1,0,0)))
_listOfSubCommands.append(cmdName)

cmdName = "Lattice2_PlacementAx_AlongY"
if FreeCAD.GuiUp:
    FreeCADGui.addCommand(cmdName, _CommandPlacementAx("along Y","Single Placement with local X aligned along global Y","Plm along Y","XZY", XDir= App.Vector(0,1,0)))
_listOfSubCommands.append(cmdName)

cmdName = "Lattice2_PlacementAx_AlongZ"
if FreeCAD.GuiUp:
    FreeCADGui.addCommand(cmdName, _CommandPlacementAx("along Z","Single Placement with local X aligned along global Z","Plm along Z","XZY", XDir= App.Vector(0,0,1)))
_listOfSubCommands.append(cmdName)

class _CommandPlacementEuler:
    "Command to create Lattice Placement feature"
    
    def GetResources(self):
        return {'Pixmap'  : getIconPath("Lattice2_Placement_New.svg"),
                'MenuText': QtCore.QT_TRANSLATE_NOOP("Lattice2_Placement","Single Placement: Euler angles"),
                'Accel': "",
                'ToolTip': QtCore.QT_TRANSLATE_NOOP("Lattice2_Placement","Lattice Placement: driven by Euler angles (yaw, pitch, roll)")}
        
    def Activated(self):
        try:
            FreeCADGui.Selection.clearSelection() 
            CreateLatticePlacementEuler(name= "PlacementEu")
        except Exception as err:
            msgError(err)
            
    def IsActive(self):
        if FreeCAD.ActiveDocument:
            return True
        else:
            return False

cmdName = "Lattice2_PlacementEuler"
if FreeCAD.GuiUp:
    FreeCADGui.addCommand(cmdName, _CommandPlacementEuler())
_listOfSubCommands.append(cmdName)


import lattice2ArrayFromShape
_listOfSubCommands.extend(lattice2ArrayFromShape.exportedCommands_forSinglePlacement)

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
        
if FreeCAD.GuiUp:
    FreeCADGui.addCommand('Lattice2_Placement_GroupCommand',GroupCommandPlacement())




exportedCommands = ['Lattice2_Placement_GroupCommand']

# -------------------------- /Gui command --------------------------------------------------
