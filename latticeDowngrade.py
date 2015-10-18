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

from latticeCommon import *
import latticeMarkers as markers
import math

__title__="latticeDowngrade module for FreeCAD"
__author__ = "DeepSOIC"
__url__ = ""



# -------------------------- common stuff --------------------------------------------------

def makeLatticeDowngrade(name):
    '''makeLatticeDowngrade(name): makes a latticeDowngrade object.'''
    obj = FreeCAD.ActiveDocument.addObject("Part::FeaturePython",name)
    _latticeDowngrade(obj)
    _ViewProviderLatticeDowngrade(obj.ViewObject)
    return obj

class _latticeDowngrade:
    "The latticeDowngrade object"
    def __init__(self,obj):
        self.Type = "latticeDowngrade"
        obj.addProperty("App::PropertyLink","Base","latticeDowngrade","Object to downgrade")
        
        obj.addProperty("App::PropertyEnumeration","Mode","latticeDowngrade","Type of elements to output.")
        obj.Mode = ['bypass','Compounds','CompSolids','Solids','Shells','Faces','Wires','Edges','Vertices']
        obj.Mode = 'bypass'
        
        obj.Proxy = self
        

    def execute(self,obj):
        rst = [] #variable to receive the final list of shapes
        shp = obj.Base.Shape
        if obj.Mode == 'bypass':
            rst = [shp]
        elif obj.Mode == 'Compounds':
            rst = shp.Compounds
        elif obj.Mode == 'CompSolids':
            rst = shp.CompSolids
        elif obj.Mode == 'Solids':
            rst = shp.Solids
        elif obj.Mode == 'Shells':
            rst = shp.Shells
        elif obj.Mode == 'Faces':
            rst = shp.Faces
        elif obj.Mode == 'Wires':
            rst = shp.Wires
        elif obj.Mode == 'Edges':
            rst = shp.Edges
        elif obj.Mode == 'Vertices':
            rst = shp.Vertexes
        else:
            raise ValueError('Downgrade mode not implemented:'+obj.Mode)
        
        if len(rst) == 0:
            scale = 1.0
            if not obj.Base.Shape.isNull():
                scale = obj.Base.Shape.BoundBox.DiagonalLength/math.sqrt(3)
            if scale < DistConfusion * 100:
                scale = 1.0
            obj.Shape = markers.getNullShapeShape(scale)
            raise ValueError('Downgrade output is null') #Feeding empty compounds to FreeCAD seems to cause rendering issues, otherwise it would have been a good idea to output nothing.
        
        obj.Shape = Part.makeCompound(rst)
        return
        
        
class _ViewProviderLatticeDowngrade:
    "A View Provider for the latticeDowngrade object"

    def __init__(self,vobj):
        vobj.Proxy = self
       
    def getIcon(self):
        return getIconPath("Lattice_Downgrade.svg")

    def attach(self, vobj):
        self.ViewObject = vobj
        self.Object = vobj.Object

  
    def setEdit(self,vobj,mode):
        return False
    
    def unsetEdit(self,vobj,mode):
        return

    def __getstate__(self):
        return None

    def __setstate__(self,state):
        return None

    def claimChildren(self):
        return [self.Object.Base]

    def onDelete(self, feature, subelements): # subelements is a tuple of strings
        try:
            self.Object.Base.ViewObject.show()
        except Exception as err:
            FreeCAD.Console.PrintError("Error in onDelete: " + err.message)
        return True


def CreateLatticeDowngrade(name, mode = "Wires"):
    FreeCAD.ActiveDocument.openTransaction("Create latticeDowngrade")
    FreeCADGui.addModule("latticeDowngrade")
    FreeCADGui.doCommand("f = latticeDowngrade.makeLatticeDowngrade(name = '"+name+"')")
    FreeCADGui.doCommand("f.Base = FreeCADGui.Selection.getSelection()[0]")
    FreeCADGui.doCommand("f.Mode = '"+mode+"'")    
    FreeCADGui.doCommand("f.Label = f.Mode + ' of ' + f.Base.Label")    
    FreeCADGui.doCommand("f.Base.ViewObject.hide()")
    FreeCADGui.doCommand("f.Proxy.execute(f)")
    FreeCADGui.doCommand("f.purgeTouched()")
    FreeCADGui.doCommand("f = None")
    FreeCAD.ActiveDocument.commitTransaction()


# -------------------------- /common stuff --------------------------------------------------

# -------------------------- Gui command --------------------------------------------------

class _CommandLatticeDowngrade:
    "Command to create latticeDowngrade feature"
    def GetResources(self):
        return {'Pixmap'  : getIconPath("Lattice_Downgrade.svg"),
                'MenuText': QtCore.QT_TRANSLATE_NOOP("Lattice_Downgrade","Parametric Downgrade"),
                'Accel': "",
                'ToolTip': QtCore.QT_TRANSLATE_NOOP("Lattice_Downgrade","Parametric Downgrade: downgrade and put results into a compound.")}
        
    def Activated(self):
        if len(FreeCADGui.Selection.getSelection()) == 1 :
            CreateLatticeDowngrade(name = "Downgrade")
        else:
            mb = QtGui.QMessageBox()
            mb.setIcon(mb.Icon.Warning)
            mb.setText(_translate("Lattice_Downgrade", "Select a shape to downgrade, first!", None))
            mb.setWindowTitle(_translate("Lattice_Downgrade","Bad selection", None))
            mb.exec_()
            
    def IsActive(self):
        if FreeCAD.ActiveDocument:
            return True
        else:
            return False
            
FreeCADGui.addCommand('Lattice_Downgrade', _CommandLatticeDowngrade())

exportedCommands = ['Lattice_Downgrade']

# -------------------------- /Gui command --------------------------------------------------
