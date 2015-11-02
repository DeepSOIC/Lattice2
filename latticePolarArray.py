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

__title__="Polar array feature module for lattice workbench for FreeCAD"
__author__ = "DeepSOIC"
__url__ = ""

import math

import FreeCAD as App
import Part

from latticeCommon import *
import latticeBaseFeature
import latticeExecuter
import latticeGeomUtils

def makePolarArray(name):
    '''makePolarArray(name): makes a PolarArray object.'''
    return latticeBaseFeature.makeLatticeFeature(name, PolarArray, ViewProviderPolarArray)

class PolarArray(latticeBaseFeature.LatticeFeature):
    "The Lattice PolarArray object"
    def derivedInit(self,obj):
        self.Type = "LatticePolarArray"
        obj.addProperty("App::PropertyEnumeration","Mode","Lattice Array","")
        obj.Mode = ['SpanN','StepN','SpanStep','Spreadsheet']
        obj.Mode = 'SpanN'
        
        obj.addProperty("App::PropertyFloat","AngleSpanStart","Lattice Array","starting angle for angular span")  
        obj.AngleSpanStart = 0
        obj.addProperty("App::PropertyFloat","AngleSpanEnd","Lattice Array","ending angle for angular span")  
        obj.AngleSpanEnd = 360
        obj.addProperty("App::PropertyBool","EndInclusive","Lattice Array","Determines if the last occurence is placed exactly at the ending angle of the span, or the ending angle is super-last.")  
        obj.EndInclusive = False
        
        obj.addProperty("App::PropertyFloat","AngleStep","Lattice Array","")  
        
        obj.addProperty("App::PropertyInteger","NumberPolar","Lattice Array","Number of occurences.")  
        obj.NumberPolar = 5
        
        obj.addProperty("App::PropertyFloat","Offset","Lattice Array","Offset of the first item, expressed as a fraction of angular step.")  
        
        
        obj.addProperty("App::PropertyLength","Radius","Lattice Array","Radius of the array (set to zero for just rotation).")  
        obj.Radius = 3 #temporary, to see the array (because marker display mode is not implemented yet)
        
        obj.addProperty("App::PropertyVector","AxisDir","Lattice Array","Vector that defines axis direction")  
        obj.AxisDir = App.Vector(0,0,1)
        
        obj.addProperty("App::PropertyVector","AxisPoint","Lattice Array","Center of rotation")  
        
        obj.addProperty("App::PropertyLink","AxisLink","Lattice Array","Link to the axis (Edge1 is used for the axis).")  
        
        obj.addProperty("App::PropertyBool","AxisDirIsDriven","Lattice Array","If True, AxisDir is not updated based on the link.")
        obj.addProperty("App::PropertyBool","AxisPointIsDriven","Lattice Array","If True, AxisPoint is not updated based on the link.")
        obj.AxisDirIsDriven = True
        obj.AxisPointIsDriven = True
        
        obj.addProperty("App::PropertyLink","SpreadSheet","SpreadSheet mode","Link to spreadsheet")
        obj.addProperty("App::PropertyString","CellStart","SpreadSheet mode","Starting cell of list of angles")
        obj.CellStart = 'A1'
        
        obj.addProperty("App::PropertyEnumeration","OrientMode","Lattice Array","Orientation of elements")
        obj.OrientMode = ['None','Against axis']
        obj.OrientMode = ['Against axis']

        
    def updateReadOnlyness(self, obj):
        m = obj.Mode
        obj.setEditorMode("AngleStep", 1 if m == "SpanN" or m == "Spreadsheet" else 0)
        obj.setEditorMode("AngleSpanEnd", 1 if m == "StepN" or m == "Spreadsheet" else 0)
        obj.setEditorMode("NumberPolar", 1 if m == "SpanStep" or m == "Spreadsheet" else 0)
        obj.setEditorMode("AxisDir", 1 if (obj.AxisLink and obj.AxisDirIsDriven) else 0)
        obj.setEditorMode("AxisPoint", 1 if (obj.AxisLink and obj.AxisPointIsDriven) else 0)
        obj.setEditorMode("AxisDirIsDriven", 0 if obj.AxisLink else 1)
        obj.setEditorMode("AxisPointIsDriven", 0 if obj.AxisLink else 1)
        obj.setEditorMode("SpreadSheet", 0 if m == "Spreadsheet" else 1)
        obj.setEditorMode("CellStart", 0 if m == "Spreadsheet" else 1)
        

    def derivedExecute(self,obj):
        # Fill in (update read-only) properties that are driven by the mode.
        self.updateReadOnlyness(obj)
        if obj.Mode == 'SpanN':
            n = obj.NumberPolar
            if obj.EndInclusive:
                n -= 1
            if n == 0:
                n = 1
            obj.AngleStep = (obj.AngleSpanEnd - obj.AngleSpanStart)/n
        elif obj.Mode == 'StepN':
            n = obj.NumberPolar
            if obj.EndInclusive:
                n -= 1
            obj.AngleSpanEnd = obj.AngleSpanStart + obj.AngleStep*n
        elif obj.Mode == 'SpanStep':
            nfloat = float((obj.AngleSpanEnd - obj.AngleSpanStart) / obj.AngleStep)
            n = math.trunc(nfloat - ParaConfusion) + 1
            if obj.EndInclusive and abs(nfloat-round(nfloat)) <= ParaConfusion:
                n = n + 1
            obj.NumberPolar = n
            
        # Apply links
        if obj.AxisLink:
            axShape = obj.AxisLink
            edges = axShape.Shape.Edges
            if len(edges) < 1:
                raise ValueError('There are no edges in axis link shape!')
            elif len(edges) > 1:
                latticeExecuter.warning(obj,'There is more than one edge in shape linked as an axis. The first edge will be used, but the shape link was probably added mistakenly.')
            edge = edges[0]
            
            #prepare
            dir = App.Vector()
            point = App.Vector()
            if isinstance(edge.Curve, Part.Line):
                dir = edge.Curve.EndPoint - edge.Curve.StartPoint
                point = edge.Curve.StartPoint
            elif isinstance(edge.Curve, Part.Circle):
                obj.AxisDir = edge.Curve.Axis
                obj.AxisPoint = edge.Curve.Center
            else:
                raise ValueError("Edge " + repr(edge) + " can't be used to derive an axis. It must be either a line or a circle/arc.")
            
            #apply
            if obj.AxisDirIsDriven:
                obj.AxisDir = dir
            if obj.AxisPointIsDriven:
                obj.AxisPoint = point
        
        # Generate the actual array. We can use Step and N directly to 
        # completely avoid mode logic, since we had updated them
        
        # cache properties into variables
        step = float(obj.AngleStep)
        startAng = float(obj.AngleSpanStart) + step*float(obj.Offset)
        n = int(obj.NumberPolar)
        radius = float(obj.Radius)
        
        # compute initial vector. It is to be perpendicular to Axis
        rot_ini = latticeGeomUtils.makeOrientationFromLocalAxes(ZAx= obj.AxisDir)
        overallPlacement = App.Placement(obj.AxisPoint, rot_ini)
        
        # Make the array
        output = [] # list of placements
        if obj.Mode != "Spreadsheet":
            for i in range(0, n):
                ang = startAng + step*i
                p = Part.Vertex()
                localrot = App.Rotation(App.Vector(0,0,1), ang)
                localtransl = localrot.multVec(App.Vector(radius,0,0))
                localplm = App.Placement(localtransl, localrot)
                resultplm = overallPlacement.multiply(localplm)
                if obj.OrientMode == 'None':
                    resultplm.Rotation = App.Rotation()
                output.append(resultplm)
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
            
            #loop until the value an't be read out
            while True:
                try:
                    ang = obj.SpreadSheet.get(col+str(row))
                except ValueError:
                    break
                ang = float(ang)
                p = Part.Vertex()
                localrot = App.Rotation(App.Vector(0,0,1), ang)
                localtransl = localrot.multVec(App.Vector(radius,0,0))
                localplm = App.Placement(localtransl, localrot)
                output.append( overallPlacement.multiply(localplm) )
                row += 1
            
        return output

class ViewProviderPolarArray(latticeBaseFeature.ViewProviderLatticeFeature):
        
    def getIcon(self):
        return getIconPath('Lattice_PolarArray.svg')
        
# -------------------------- /document object --------------------------------------------------

# -------------------------- Gui command --------------------------------------------------

def CreatePolarArray(name):
    sel = FreeCADGui.Selection.getSelectionEx()
    FreeCAD.ActiveDocument.openTransaction("Create PolarArray")
    FreeCADGui.addModule("latticePolarArray")
    FreeCADGui.addModule("latticeExecuter")
    FreeCADGui.doCommand("f = latticePolarArray.makePolarArray(name='"+name+"')")
    if len(sel) == 1:
        FreeCADGui.doCommand("f.AxisLink = App.ActiveDocument."+sel[0].ObjectName)
    FreeCADGui.doCommand("latticeExecuter.executeFeature(f)")
    FreeCADGui.doCommand("f = None")
    FreeCAD.ActiveDocument.commitTransaction()


class _CommandPolarArray:
    "Command to create PolarArray feature"
    def GetResources(self):
        return {'Pixmap'  : getIconPath("Lattice_PolarArray.svg"),
                'MenuText': QtCore.QT_TRANSLATE_NOOP("Lattice_PolarArray","Generate polar array"),
                'Accel': "",
                'ToolTip': QtCore.QT_TRANSLATE_NOOP("Lattice_PolarArray","Make a polar array lattice object (array of placements)")}
        
    def Activated(self):
        if len(FreeCADGui.Selection.getSelection()) < 2 :
            CreatePolarArray(name = "PolarArray")
        else:
            mb = QtGui.QMessageBox()
            mb.setIcon(mb.Icon.Warning)
            mb.setText(translate("Lattice_PolarArray", "Either don't select anything, or select an object to serve an axis. More than one object was selected, not supported.", None))
            mb.setWindowTitle(translate("Lattice_PolarArray","Bad selection", None))
            mb.exec_()
            
    def IsActive(self):
        if FreeCAD.ActiveDocument:
            return True
        else:
            return False
            
FreeCADGui.addCommand('Lattice_PolarArray', _CommandPolarArray())

exportedCommands = ['Lattice_PolarArray']

# -------------------------- /Gui command --------------------------------------------------

