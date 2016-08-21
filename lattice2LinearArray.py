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

__title__="Linear array feature module for lattice workbench for FreeCAD"
__author__ = "DeepSOIC"
__url__ = ""

import math

import FreeCAD as App
import Part

from lattice2Common import *
import lattice2BaseFeature
import lattice2Executer
import lattice2GeomUtils
from lattice2ValueSeriesGenerator import ValueSeriesGenerator

def makeLinearArray(name):
    '''makeLinearArray(name): makes a LinearArray object.'''
    return lattice2BaseFeature.makeLatticeFeature(name, LinearArray, ViewProviderLinearArray)

class LinearArray(lattice2BaseFeature.LatticeFeature):
    "The Lattice LinearArray object"
    def derivedInit(self,obj):
        self.Type = "LatticeLinearArray"

        obj.addProperty("App::PropertyVector","Dir","Lattice Array","Vector that defines axis direction")  
        obj.Dir = App.Vector(1,0,0)
        
        obj.addProperty("App::PropertyVector","Point","Lattice Array","Position of base (the point through which the axis passes, and from which positions of elements are measured)")  
        
        obj.addProperty("App::PropertyLink","Link","Lattice Array","Link to the axis (Edge1 is used for the axis).")  
        obj.addProperty("App::PropertyString","LinkSubelement","Lattice Array","subelement to take from axis link shape")

        obj.addProperty("App::PropertyBool","Reverse","Lattice Array","Set to true to reverse direction")

        obj.addProperty("App::PropertyBool","DirIsDriven","Lattice Array","If True, Dir property is driven by link.")
        obj.DirIsDriven = True

        obj.addProperty("App::PropertyBool","PointIsDriven","Lattice Array","If True, AxisPoint is not updated based on the link.")
        obj.PointIsDriven = True

        obj.addProperty("App::PropertyEnumeration","DrivenProperty","Lattice Array","Select, which property is to be driven by length of axis link.")
        obj.DrivenProperty = ['None','Span','SpanStart','SpanEnd','Step']
        obj.DrivenProperty = 'Span'
                        
        obj.addProperty("App::PropertyEnumeration","OrientMode","Lattice Array","Orientation of elements")
        obj.OrientMode = ['None','Along axis']
        obj.OrientMode = 'Along axis'
        
        self.assureGenerator(obj)
        obj.ValuesSource = "Generator"
        obj.GeneratorMode = "StepN"
        obj.EndInclusive = True
        obj.SpanStart = 0.0
        obj.SpanEnd = 12.0
        obj.Step = 3.0
        obj.Count = 5.0

    def updateReadonlyness(self, obj):
        obj.setEditorMode("Dir", 1 if (obj.Link and obj.DirIsDriven) else 0)
        obj.setEditorMode("Point", 1 if (obj.Link and obj.PointIsDriven) else 0)
        obj.setEditorMode("DirIsDriven", 0 if obj.Link else 1)
        obj.setEditorMode("PointIsDriven", 0 if obj.Link else 1)
        obj.setEditorMode("DrivenProperty", 0 if obj.Link else 1)
        
        self.generator.updateReadonlyness()

    def assureGenerator(self, obj):
        '''Adds an instance of value series generator, if one doesn't exist yet.'''
        if hasattr(self,"generator"):
            return
        self.generator = ValueSeriesGenerator(obj)
        self.generator.addProperties(groupname= "Lattice Array", 
                                     groupname_gen= "Lattice Series Generator", 
                                     valuesdoc= "List of distances. Distance is measured from Point, along Dir, in millimeters.",
                                     valuestype= "App::PropertyDistance")
        self.updateReadonlyness(obj)
        
        

    def derivedExecute(self,obj):
        self.assureGenerator(obj)
        self.updateReadonlyness(obj)

        # Apply links
        if obj.Link:
            if lattice2BaseFeature.isObjectLattice(obj.Link):
                lattice2Executer.warning(obj,"For polar array, axis link is expected to be a regular shape. Lattice objct was supplied instead, it's going to be treated as a generic shape.")
            
            #resolve the link
            if len(obj.LinkSubelement) > 0:
                linkedShape = obj.Link.Shape.getElement(obj.LinkSubelement)
            else:
                linkedShape = obj.Link.Shape
            
            #Type check
            if linkedShape.ShapeType != 'Edge':
                raise ValueError('Axis link must be an edge; it is '+linkedShape.ShapeType+' instead.')
            if type(linkedShape.Curve) is not Part.Line:
                raise ValueError('Axis link must be a line; it is '+type(linkedShape.Curve)+' instead.')
            
            #obtain
            dir = linkedShape.Curve.EndPoint - linkedShape.Curve.StartPoint
            point = linkedShape.Curve.StartPoint if not obj.Reverse else linkedShape.Curve.EndPoint
            
            if obj.DirIsDriven:
                obj.Dir = dir
            if obj.PointIsDriven:
                obj.Point = point
            if obj.DrivenProperty != 'None':
                if obj.DrivenProperty == 'Span':
                    propname = "SpanEnd"
                    obj.SpanEnd = obj.SpanStart + App.Units.Quantity('mm')*dir.Length
                else:
                    propname = obj.DrivenProperty
                    setattr(obj, propname, dir.Length)
                if self.generator.isPropertyControlledByGenerator(propname):
                    lattice2Executer.warning(obj, "Property "+propname+" is driven by both generator and link. Generator has priority.")

        
        # Generate series of values
        self.generator.execute()
        values = [float(strv) for strv in obj.Values]
        
        #Apply reversal
        if obj.Reverse:
            obj.Dir = obj.Dir*(-1.0)
            if not(obj.DirIsDriven and obj.Link):
                obj.Reverse = False

        # precompute orientation
        if obj.OrientMode == 'Along axis':
            ori = lattice2GeomUtils.makeOrientationFromLocalAxes(ZAx= obj.Dir).multiply(
                    lattice2GeomUtils.makeOrientationFromLocalAxes(ZAx= App.Vector(1,0,0), XAx= App.Vector(0,0,1)) )
        else:
            ori = App.Rotation()
        
        dir = obj.Dir
        dir.normalize()
        
        # Make the array
        output = [] # list of placements
        for v in values:
            output.append( App.Placement(obj.Point + obj.Dir*v, ori) )
            
        return output

class ViewProviderLinearArray(lattice2BaseFeature.ViewProviderLatticeFeature):
        
    def getIcon(self):
        return getIconPath('Lattice2_LinearArray.svg')
        
# -------------------------- /document object --------------------------------------------------

# -------------------------- Gui command --------------------------------------------------

def CreateLinearArray(name, mode):
    sel = FreeCADGui.Selection.getSelectionEx()
    FreeCAD.ActiveDocument.openTransaction("Create LinearArray")
    FreeCADGui.addModule("lattice2LinearArray")
    FreeCADGui.addModule("lattice2Executer")
    FreeCADGui.doCommand("f = lattice2LinearArray.makeLinearArray(name='"+name+"')")
    if len(sel) == 1:
        FreeCADGui.doCommand("f.Link = App.ActiveDocument."+sel[0].ObjectName)
        if sel[0].HasSubObjects:
            FreeCADGui.doCommand("f.LinkSubelement = '"+sel[0].SubElementNames[0]+"'")
    FreeCADGui.doCommand("f.GeneratorMode = {mode}".format(mode= repr(mode)))
    FreeCADGui.doCommand("lattice2Executer.executeFeature(f)")
    FreeCAD.ActiveDocument.commitTransaction()
    
    FreeCADGui.doCommand("Gui.Selection.clearSelection()")
    FreeCADGui.doCommand("Gui.Selection.addSelection(f)")

class CommandLinearArray:
    "Command to create LinearArray feature"
    def __init__(self, mode):
        self.mode = mode
    
    def GetResources(self):
        mode_tooltips = {
            'SpanN': "fit N placements into Span",
            'StepN': "make N placements spaced by Step",
            'SpanStep': "fill Span with placements spaced by Step",
            'Random': "put N placements into Span randomly",
        }
        return {'Pixmap'  : getIconPath("Lattice2_LinearArray_New.svg"),
                'MenuText': QtCore.QT_TRANSLATE_NOOP("Lattice2_LinearArray","Linear array: {mode}")
                              .format(mode= ValueSeriesGenerator.mode_userfriendly_names[self.mode]),
                'Accel': "",
                'ToolTip': QtCore.QT_TRANSLATE_NOOP("Lattice2_LinearArray","Make a linear array of placements ({mode_tooltip})")
                              .format(mode_tooltip= mode_tooltips[self.mode])}
        
    def Activated(self):
        if len(FreeCADGui.Selection.getSelection()) < 2 :
            try:
                CreateLinearArray(name= "LinearArray", mode= self.mode)
            except Exception as err:
                msgError(err)
        else:
            infoMessage(translate("Lattice2_LinearArray","Bad selection", None),
                        translate("Lattice2_LinearArray", "Either don't select anything, or select a linear edge to serve an axis. More than one object was selected, not supported.", None))

    def IsActive(self):
        if FreeCAD.ActiveDocument:
            return True
        else:
            return False

_listOfSubCommands = []
for m in ValueSeriesGenerator.gen_modes:
    cmd_name = 'Lattice2_LinearArray_'+m
    _listOfSubCommands.append(cmd_name)
    FreeCADGui.addCommand(cmd_name, CommandLinearArray(m))

class GroupCommandLinearArray:
    def GetCommands(self):
        global _listOfSubCommands
        return tuple(_listOfSubCommands) # a tuple of command names that you want to group

    def GetDefaultCommand(self): # return the index of the tuple of the default command. This method is optional and when not implemented '0' is used  
        return 0

    def GetResources(self):
        return { 'MenuText': 'Linear Array', 'ToolTip': 'Linear Array: array of placements on a line.'}
        
    def IsActive(self): # optional
        return FreeCAD.ActiveDocument is not None

FreeCADGui.addCommand('Lattice2_LinearArray_GroupCommand',GroupCommandLinearArray())
exportedCommands = ['Lattice2_LinearArray_GroupCommand']

# -------------------------- /Gui command --------------------------------------------------

