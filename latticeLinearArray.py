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

from latticeCommon import *
import latticeBaseFeature
import latticeExecuter
import latticeGeomUtils

def makeLinearArray(name):
    '''makeLinearArray(name): makes a LinearArray object.'''
    return latticeBaseFeature.makeLatticeFeature(name, LinearArray, ViewProviderLinearArray)

class LinearArray(latticeBaseFeature.LatticeFeature):
    "The Lattice LinearArray object"
    def derivedInit(self,obj):
        self.Type = "LatticeLinearArray"
        obj.addProperty("App::PropertyEnumeration","Mode","Lattice Array","")
        obj.Mode = ['SpanN','StepN','SpanStep','Spreadsheet']
        obj.Mode = 'StepN'
        
        obj.addProperty("App::PropertyLength","SpanStart","Lattice Array","starting position value.")  
        obj.addProperty("App::PropertyLength","SpanEnd","Lattice Array","ending position value")  
        
        obj.addProperty("App::PropertyBool","EndInclusive","Lattice Array","Determines if the last occurence is placed exactly at the ending position of the span, or the ending position is that of super-last item.")  
        obj.EndInclusive = True
        
        obj.addProperty("App::PropertyLength","Step","Lattice Array","Distance between occurences")
        obj.Step = 3.0
        
        obj.addProperty("App::PropertyInteger","NumberLinear","Lattice Array","Number of occurences")  
        obj.NumberLinear = 5
        
        obj.addProperty("App::PropertyFloat","Offset","Lattice Array","Offset of the first item (in fractions of step).")  
                        
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
        obj.DrivenProperty = 'Step'

        obj.addProperty("App::PropertyLink","SpreadSheet","SpreadSheet mode","Link to spreadsheet")
        obj.addProperty("App::PropertyString","CellStart","SpreadSheet mode","Starting cell of list of positions")
        obj.CellStart = 'A1'
        
        obj.addProperty("App::PropertyEnumeration","OrientMode","Lattice Array","Orientation of elements")
        obj.OrientMode = ['None','Along axis']
        obj.OrientMode = 'Along axis'
        
    def updateReadOnlyness(self, obj):
        m = obj.Mode
        obj.setEditorMode("Step", 1 if m == "SpanN" or m == "Spreadsheet" else 0)
        obj.setEditorMode("SpanEnd", 1 if m == "StepN" or m == "Spreadsheet" else 0)
        obj.setEditorMode("NumberLinear", 1 if m == "SpanStep" or m == "Spreadsheet" else 0)
        obj.setEditorMode("Dir", 1 if (obj.Link and obj.DirIsDriven) else 0)
        obj.setEditorMode("Point", 1 if (obj.Link and not obj.PointIsDriven) else 0)
        obj.setEditorMode("DirIsDriven", 0 if obj.Link else 1)
        obj.setEditorMode("PointIsDriven", 0 if obj.Link else 1)
        obj.setEditorMode("DrivenProperty", 0 if obj.Link else 1)
        obj.setEditorMode("SpreadSheet", 0 if m == "Spreadsheet" else 1)
        obj.setEditorMode("CellStart", 0 if m == "Spreadsheet" else 1)
        

    def derivedExecute(self,obj):
        self.updateReadOnlyness(obj)

        # Apply links
        if obj.Link:
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
                    obj.SpanEnd = obj.SpanStart + dir.Length
                else:
                    setattr(obj, obj.DrivenProperty, dir.Length)

        # Fill in (update read-only) properties that are driven by the mode.
        if obj.Mode == 'SpanN':
            n = obj.NumberLinear
            if obj.EndInclusive:
                n -= 1
            if n == 0:
                n = 1
            obj.Step = (obj.SpanEnd - obj.SpanStart)/n
            if obj.DrivenProperty == 'Step' and obj.Link:
                latticeExecuter.warning(obj,"Step property is being driven by both the link and the selected mode. Mode has priority.")
        elif obj.Mode == 'StepN':
            n = obj.NumberLinear
            if obj.EndInclusive:
                n -= 1
            obj.SpanEnd = obj.SpanStart + obj.Step*n
            if 'Span' in obj.DrivenProperty and obj.Link:
                latticeExecuter.warning(obj,"SpanEnd property is being driven by both the link and the selected mode. Mode has priority.")
        elif obj.Mode == 'SpanStep':
            nfloat = float((obj.SpanEnd - obj.SpanStart) / obj.Step)
            n = math.trunc(nfloat - ParaConfusion) + 1
            if obj.EndInclusive and abs(nfloat-round(nfloat)) <= ParaConfusion:
                n = n + 1
            obj.NumberLinear = n
            
        
        # Generate the actual array. We can use Step and N directly to 
        # completely avoid mode logic, since we had updated them
        
        # cache properties into variables
        step = float(obj.Step)
        start = float(obj.SpanStart) + step*float(obj.Offset)
        n = int(obj.NumberLinear)
        
        #Apply reversal
        if obj.Reverse:
            obj.Dir = obj.Dir*(-1.0)
            if not(obj.DirIsDriven and obj.Link):
                obj.Reverse = False

        # precompute orientation
        if obj.OrientMode == 'Along axis':
            ori = latticeGeomUtils.makeOrientationFromLocalAxes(ZAx= obj.Dir).multiply(
                    latticeGeomUtils.makeOrientationFromLocalAxes(ZAx= App.Vector(1,0,0), XAx= App.Vector(0,0,1)) )
        else:
            ori = App.Rotation()
        
        dir = obj.Dir
        dir.normalize()
        
        # Make the array
        output = [] # list of placements
        if obj.Mode != "Spreadsheet":
            for i in range(0, n):
                position = start + step*i
                output.append( App.Placement(obj.Point + obj.Dir*position, ori) )
        else:
            #parse address
            addr = obj.CellStart
            #assuming only two letter column
            if addr[1].isalpha():
                col = addr[0:2]
                row = addr[2:]
            else:
                col = addr[0:1]
                row = addr[1:]
            row = int(row)
            
            #loop until the value can't be read out
            while True:
                try:
                    position = obj.SpreadSheet.get(col+str(row))
                except ValueError:
                    break
                position = float(position)
                output.append( App.Placement(obj.Point + obj.Dir*position, ori) )
                row += 1
            
        return output

class ViewProviderLinearArray(latticeBaseFeature.ViewProviderLatticeFeature):
        
    def getIcon(self):
        return getIconPath('Lattice_LinearArray.svg')
        
# -------------------------- /document object --------------------------------------------------

# -------------------------- Gui command --------------------------------------------------

def CreateLinearArray(name):
    sel = FreeCADGui.Selection.getSelectionEx()
    FreeCAD.ActiveDocument.openTransaction("Create LinearArray")
    FreeCADGui.addModule("latticeLinearArray")
    FreeCADGui.addModule("latticeExecuter")
    FreeCADGui.doCommand("f = latticeLinearArray.makeLinearArray(name='"+name+"')")
    if len(sel) == 1:
        FreeCADGui.doCommand("f.Link = App.ActiveDocument."+sel[0].ObjectName)
        if sel[0].HasSubObjects:
            FreeCADGui.doCommand("f.LinkSubelement = '"+sel[0].SubElementNames[0]+"'")
    FreeCADGui.doCommand("latticeExecuter.executeFeature(f)")
    FreeCADGui.doCommand("f = None")
    FreeCAD.ActiveDocument.commitTransaction()


class _CommandLinearArray:
    "Command to create LinearArray feature"
    def GetResources(self):
        return {'Pixmap'  : getIconPath("Lattice_LinearArray.svg"),
                'MenuText': QtCore.QT_TRANSLATE_NOOP("Lattice_LinearArray","Generate linear array"),
                'Accel': "",
                'ToolTip': QtCore.QT_TRANSLATE_NOOP("Lattice_LinearArray","Make a linear array lattice object (array of placements)")}
        
    def Activated(self):
        if len(FreeCADGui.Selection.getSelection()) < 2 :
            CreateLinearArray(name = "LinearArray")
        else:
            mb = QtGui.QMessageBox()
            mb.setIcon(mb.Icon.Warning)
            mb.setText(translate("Lattice_LinearArray", "Either don't select anything, or select a linear edge to serve an axis. More than one object was selected, not supported.", None))
            mb.setWindowTitle(translate("Lattice_LinearArray","Bad selection", None))
            mb.exec_()
            
    def IsActive(self):
        if FreeCAD.ActiveDocument:
            return True
        else:
            return False
            
FreeCADGui.addCommand('Lattice_LinearArray', _CommandLinearArray())

exportedCommands = ['Lattice_LinearArray']

# -------------------------- /Gui command --------------------------------------------------

