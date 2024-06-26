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

from lattice2Common import *
import lattice2Markers as markers
import lattice2CompoundExplorer as LCE

import math

__title__="latticeDowngrade module for FreeCAD"
__author__ = "DeepSOIC"
__url__ = ""

def getAllSeams(shape):
    '''getAllSeams(shape): extract all seam edges of a shape. Returns list of edges.'''
    # this is a hack.
    # Seam edges were found to be in wires that contain the seam edge twice.
    # See http://forum.freecadweb.org/viewtopic.php?f=3&t=15470#p122993 (post #7 in topic "Extra Line in Models")
    import itertools
    seams = []
    for w in shape.Wires:
        for (e1,e2) in itertools.combinations(w.childShapes(),2):
            if e1.isSame(e2):
                seams.append(e1)
    return seams


# -------------------------- common stuff --------------------------------------------------

def makeLatticeDowngrade(name):
    '''makeLatticeDowngrade(name): makes a latticeDowngrade object.'''
    obj = FreeCAD.ActiveDocument.addObject("Part::FeaturePython",name)
    _latticeDowngrade(obj)
    if FreeCAD.GuiUp:        
        _ViewProviderLatticeDowngrade(obj.ViewObject)
    return obj



class _latticeDowngrade:
    "The latticeDowngrade object"
    
    _DowngradeModeList = ['Leaves','CompSolids','Solids','Shells','OpenWires','Faces','Wires','Edges','Seam edges','Non-seam edges','Vertices']
    
    def __init__(self,obj):
        self.Type = "latticeDowngrade"
        obj.addProperty("App::PropertyLink","Base","latticeDowngrade","Object to downgrade")
        
        obj.addProperty("App::PropertyEnumeration","Mode","latticeDowngrade","Type of elements to output.")
        obj.Mode = ['bypass'] + self._DowngradeModeList
        obj.Mode = 'bypass'
        
        obj.Proxy = self
        

    def execute(self,obj):
        rst = [] #variable to receive the final list of shapes
        shp = screen(obj.Base).Shape
        if obj.Mode == 'bypass':
            rst = [shp]
        elif obj.Mode == 'Leaves':
            rst = LCE.AllLeaves(shp)
        elif obj.Mode == 'CompSolids':
            rst = shp.CompSolids
        elif obj.Mode == 'Solids':
            rst = shp.Solids
        elif obj.Mode == 'Shells':
            rst = shp.Shells
        elif obj.Mode == 'OpenWires':
            openWires = []
            shells = shp.Shells
            for shell in shells:
                openEdges = shell.getFreeEdges().childShapes()
                if len(openEdges) > 1: # edges need to be fused into wires
                    clusters = Part.getSortedClusters(openEdges)
                    wires = [Part.Wire(cluster) for cluster in clusters]
                else: 
                    wires = openEdges
                openWires.extend(wires)
            rst = openWires
        elif obj.Mode == 'Faces':
            rst = shp.Faces
        elif obj.Mode == 'Wires':
            rst = shp.Wires
        elif obj.Mode == 'Edges':
            rst = shp.Edges
        elif obj.Mode == 'Seam edges':
            rst = getAllSeams(shp)
        elif obj.Mode == 'Non-seam edges':
            seams = getAllSeams(shp)
            edges = shp.Edges
            rst = []
            for e in edges:
                bIsSeam = False
                for s in seams:
                    if e.isSame(s):
                        bIsSeam = True
                        break
                if not bIsSeam:
                    rst.append(e)
        elif obj.Mode == 'Vertices':
            rst = shp.Vertexes
        else:
            raise ValueError('Downgrade mode not implemented:'+obj.Mode)
        
        if len(rst) == 0:
            scale = 1.0
            if not screen(obj.Base).Shape.isNull():
                scale = screen(obj.Base).Shape.BoundBox.DiagonalLength/math.sqrt(3)
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
        return getIconPath("Lattice2_Downgrade.svg")

    def attach(self, vobj):
        self.ViewObject = vobj
        self.Object = vobj.Object

  
    def __getstate__(self):
        return None

    def __setstate__(self,state):
        return None

    def dumps(self):
        return None

    def loads(self,state):
        return None

    def claimChildren(self):
        weakparenting = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/Lattice2").GetBool("WeakParenting", True)
        if weakparenting:
            return []
        return [screen(self.Object.Base)]

    def onDelete(self, feature, subelements): # subelements is a tuple of strings
        try:
            screen(self.Object.Base).ViewObject.show()
        except Exception as err:
            FreeCAD.Console.PrintError("Error in onDelete: " + str(err))
        return True


def CreateLatticeDowngrade(name, mode = "Wires"):
    FreeCAD.ActiveDocument.openTransaction("Create latticeDowngrade")
    FreeCADGui.addModule("lattice2Downgrade")
    FreeCADGui.addModule("lattice2Executer")
    FreeCADGui.doCommand("f = lattice2Downgrade.makeLatticeDowngrade(name = '"+name+"')")
    FreeCADGui.doCommand("f.Base = FreeCADGui.Selection.getSelection()[0]")
    FreeCADGui.doCommand("f.Mode = '"+mode+"'")    
    FreeCADGui.doCommand("f.Label = f.Mode + ' of ' + f.Base.Label")    
    if mode != 'OpenWires':
        FreeCADGui.doCommand("f.Base.ViewObject.hide()")
    else:
        FreeCADGui.doCommand("f.ViewObject.LineWidth = 6.0")
    FreeCADGui.doCommand("lattice2Executer.executeFeature(f)")
    FreeCADGui.doCommand("f = None")
    FreeCAD.ActiveDocument.commitTransaction()


# -------------------------- /common stuff --------------------------------------------------

# -------------------------- Gui command --------------------------------------------------

class _CommandLatticeDowngrade:
    "Command to create latticeDowngrade feature"
    
    mode = ''
    
    def __init__(self, mode = 'wires'):
        self.mode = mode
    
    def GetResources(self):
        return {'Pixmap'  : getIconPath("Lattice2_Downgrade.svg"),
                'MenuText': QtCore.QT_TRANSLATE_NOOP("Lattice2_Downgrade","Downgrade to ") + self.mode, # FIXME: not translation-friendly!
                'Accel': "",
                'ToolTip': QtCore.QT_TRANSLATE_NOOP("Lattice2_Downgrade","Parametric Downgrade: downgrade and put results into a compound.")}
        
    def Activated(self):
        if len(FreeCADGui.Selection.getSelection()) == 1 :
            CreateLatticeDowngrade(name= "Downgrade", mode= self.mode)
        else:
            mb = QtGui.QMessageBox()
            mb.setIcon(mb.Icon.Warning)
            mb.setText(translate("Lattice2_Downgrade", "Select a shape to downgrade, first!", None))
            mb.setWindowTitle(translate("Lattice2_Downgrade","Bad selection", None))
            mb.exec_()
            
    def IsActive(self):
        if FreeCAD.ActiveDocument:
            return True
        else:
            return False

_listOfSubCommands = []
for mode in _latticeDowngrade._DowngradeModeList: 
    cmdName = 'Lattice2_Downgrade' + mode
    if FreeCAD.GuiUp:
        FreeCADGui.addCommand(cmdName, _CommandLatticeDowngrade(mode))
    _listOfSubCommands.append(cmdName)
    

class GroupCommandLatticeDowngrade:
    def GetCommands(self):
        global _listOfSubCommands
        return tuple(_listOfSubCommands) # a tuple of command names that you want to group

    def GetDefaultCommand(self): # return the index of the tuple of the default command. This method is optional and when not implemented '0' is used  
        return 5

    def GetResources(self):
        return { 'MenuText': 'Parametric Downgrade', 'ToolTip': 'Parametric Downgrade: downgrade and pack results into a compound.'}
        
    def IsActive(self): # optional
        return activeBody() is None
        
if FreeCAD.GuiUp:
    FreeCADGui.addCommand('Lattice2_Downgrade_GroupCommand',GroupCommandLatticeDowngrade())




exportedCommands = ['Lattice2_Downgrade_GroupCommand']

# -------------------------- /Gui command --------------------------------------------------
