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

from lattice2Common import *
import lattice2BaseFeature
from lattice2BaseFeature import assureProperty
import lattice2Executer
import lattice2GeomUtils
from lattice2ValueSeriesGenerator import ValueSeriesGenerator
from lattice2Utils import sublinkFromApart, syncSublinkApart

def makePolarArray(name):
    '''makePolarArray(name): makes a PolarArray object.'''
    return lattice2BaseFeature.makeLatticeFeature(name, PolarArray, ViewProviderPolarArray)

class PolarArray(lattice2BaseFeature.LatticeFeature):
    "The Lattice PolarArray object"
    def derivedInit(self,obj):
        self.Type = "LatticePolarArray"
                
        obj.addProperty("App::PropertyLength","Radius","Lattice Array","Radius of the array (set to zero for just rotation).")  
        obj.Radius = 3 
        
        obj.addProperty("App::PropertyVector","AxisDir","Lattice Array","Vector that defines axis direction")  
        obj.AxisDir = App.Vector(0,0,1)
        
        obj.addProperty("App::PropertyVector","AxisPoint","Lattice Array","Center of rotation")  
        
        obj.addProperty("App::PropertyLink","AxisLink","Lattice Array","Link to the axis (Edge1 is used for the axis).")  
        obj.addProperty("App::PropertyString","AxisLinkSubelement","Lattice Array","subelement to take from axis link shape")        
        
        obj.addProperty("App::PropertyBool","AxisDirIsDriven","Lattice Array","If True, AxisDir is not updated based on the link.")
        obj.addProperty("App::PropertyBool","AxisPointIsDriven","Lattice Array","If True, AxisPoint is not updated based on the link.")
        obj.AxisDirIsDriven = True
        obj.AxisPointIsDriven = True
        
        obj.addProperty("App::PropertyEnumeration","OrientMode","Lattice Array","Orientation of elements")
        obj.OrientMode = ['None','Against axis']
        obj.OrientMode = 'Against axis'
        
        self.assureGenerator(obj)

        obj.ValuesSource = "Generator"
        obj.SpanStart = 0
        obj.SpanEnd = 360
        obj.EndInclusive = False
        obj.Count = 5
        
        self.assureProperties(obj)

    def assureGenerator(self, obj):
        '''Adds an instance of value series generator, if one doesn't exist yet.'''
        if hasattr(self,"generator"):
            return
        self.generator = ValueSeriesGenerator(obj)
        self.generator.addProperties(groupname= "Lattice Array", 
                                     groupname_gen= "Lattice Series Generator", 
                                     valuesdoc= "List of angles, in degrees.",
                                     valuestype= "App::PropertyFloat")
        self.updateReadonlyness(obj)
        
    def updateReadonlyness(self, obj):
        obj.setEditorMode("AxisDir", 1 if (obj.AxisLink and obj.AxisDirIsDriven) else 0)
        obj.setEditorMode("AxisPoint", 1 if (obj.AxisLink and obj.AxisPointIsDriven) else 0)
        obj.setEditorMode("AxisDirIsDriven", 0 if obj.AxisLink else 1)
        obj.setEditorMode("AxisPointIsDriven", 0 if obj.AxisLink else 1)
        self.generator.updateReadonlyness()
    
    def assureProperties(self, selfobj):
        assureProperty(selfobj, "App::PropertyLinkSub", "AxisSubLink", sublinkFromApart(selfobj.AxisLink, selfobj.AxisLinkSubelement), "Lattice Array", "Mirror of Object+SubNames properties")


    def derivedExecute(self,obj):
        self.assureGenerator(obj)
        self.assureProperties(obj)
        self.updateReadonlyness(obj)
        
        # Apply links
        if obj.AxisLink:
            if lattice2BaseFeature.isObjectLattice(obj.AxisLink):
                lattice2Executer.warning(obj,"For polar array, axis link is expected to be a regular shape. Lattice objct was supplied instead, it's going to be treated as a generic shape.")
                
            #resolve the link        
            if len(obj.AxisLinkSubelement) > 0:
                linkedShape = obj.AxisLink.Shape.getElement(obj.AxisLinkSubelement)
            else:
                linkedShape = obj.AxisLink.Shape

            #Type check
            if linkedShape.ShapeType != 'Edge':
                raise ValueError('Axis link must be an edge; it is '+linkedShape.ShapeType+' instead.')
            
            #prepare
            dir = App.Vector()
            point = App.Vector()
            if isinstance(linkedShape.Curve, Part.Line):
                dir = linkedShape.Curve.EndPoint - linkedShape.Curve.StartPoint
                point = linkedShape.Curve.StartPoint
            elif isinstance(linkedShape.Curve, Part.Circle):
                dir = linkedShape.Curve.Axis
                point = linkedShape.Curve.Center
            else:
                raise ValueError("Edge " + repr(linkedShape) + " can't be used to derive an axis. It must be either a line or a circle/arc.")
            
            #apply
            if obj.AxisDirIsDriven:
                obj.AxisDir = dir
            if obj.AxisPointIsDriven:
                obj.AxisPoint = point
        
        self.generator.execute()
        
        # cache properties into variables
        radius = float(obj.Radius)
        values = [float(strv) for strv in obj.Values]
        
        # compute initial vector. It is to be perpendicular to Axis
        rot_ini = lattice2GeomUtils.makeOrientationFromLocalAxes(ZAx= obj.AxisDir)
        overallPlacement = App.Placement(obj.AxisPoint, rot_ini)
        
        # Make the array
        output = [] # list of placements
        for ang in values:
            p = Part.Vertex()
            localrot = App.Rotation(App.Vector(0,0,1), ang)
            localtransl = localrot.multVec(App.Vector(radius,0,0))
            localplm = App.Placement(localtransl, localrot)
            resultplm = overallPlacement.multiply(localplm)
            if obj.OrientMode == 'None':
                resultplm.Rotation = App.Rotation()
            output.append(resultplm)

        return output

    def onChanged(self, selfobj, prop): #prop is a string - name of the property
        # synchronize SubLink and Object+SubNames properties
        syncSublinkApart(selfobj, prop, 'AxisSubLink', 'AxisLink', 'AxisLinkSubelement')
        return lattice2BaseFeature.LatticeFeature.onChanged(self, selfobj, prop)

class ViewProviderPolarArray(lattice2BaseFeature.ViewProviderLatticeFeature):
        
    def getIcon(self):
        return getIconPath('Lattice2_PolarArray.svg')
        
# -------------------------- /document object --------------------------------------------------

# -------------------------- Gui command --------------------------------------------------

def CreatePolarArray(name):
    sel = FreeCADGui.Selection.getSelectionEx()
    FreeCAD.ActiveDocument.openTransaction("Create PolarArray")
    FreeCADGui.addModule("lattice2PolarArray")
    FreeCADGui.addModule("lattice2Executer")
    FreeCADGui.doCommand("f = lattice2PolarArray.makePolarArray(name='"+name+"')")
    if len(sel) == 1:
        FreeCADGui.doCommand("f.AxisLink = App.ActiveDocument."+sel[0].ObjectName)
        if sel[0].HasSubObjects:
            FreeCADGui.doCommand("f.AxisLinkSubelement = '"+sel[0].SubElementNames[0]+"'")
    FreeCADGui.doCommand("lattice2Executer.executeFeature(f)")
    FreeCADGui.doCommand("f = None")
    FreeCAD.ActiveDocument.commitTransaction()


class _CommandPolarArray:
    "Command to create PolarArray feature"
    def GetResources(self):
        return {'Pixmap'  : getIconPath("Lattice2_PolarArray_New.svg"),
                'MenuText': QtCore.QT_TRANSLATE_NOOP("Lattice2_PolarArray","Generate polar array"),
                'Accel': "",
                'ToolTip': QtCore.QT_TRANSLATE_NOOP("Lattice2_PolarArray","Make a polar array lattice object (array of placements)")}
        
    def Activated(self):
        if len(FreeCADGui.Selection.getSelection()) < 2 :
            CreatePolarArray(name = "PolarArray")
        else:
            mb = QtGui.QMessageBox()
            mb.setIcon(mb.Icon.Warning)
            mb.setText(translate("Lattice2_PolarArray", "Either don't select anything, or select an object to serve an axis. More than one object was selected, not supported.", None))
            mb.setWindowTitle(translate("Lattice2_PolarArray","Bad selection", None))
            mb.exec_()
            
    def IsActive(self):
        if FreeCAD.ActiveDocument:
            return True
        else:
            return False
            
FreeCADGui.addCommand('Lattice2_PolarArray', _CommandPolarArray())

exportedCommands = ['Lattice2_PolarArray']

# -------------------------- /Gui command --------------------------------------------------

