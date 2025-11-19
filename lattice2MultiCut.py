#***************************************************************************
#*                                                                         *
#*   Copyright (c) 2025 - Victor Titov (DeepSOIC)                          *
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
import FreeCAD as App
if App.GuiUp:
    import FreeCADGui as Gui

__title__="MultiCut feature of Lattice2"
__author__ = "DeepSOIC"

HELP_MESSAGE = \
"""Lattice2 MultiCut feature. Subtracts an array of (possibly) intersecting shape from a base shape. 
To use, select Base, then Tool, and invole MultiCut.

This tool subtracts each element of an array from the base shape, one by one. \
This can sometimes be more reliable and faster than fusing the array together first, \
as it doesn't have to search for all intersections between array items, \
only for those that are actually imprinted into the shape being cut.

Only the top level compound is iterated over. \
Nested compounds are assumed to have no intersections within. \
If that is not the case, use 'Downgrade to Leaves' command do flatten the compound structure.\
"""

def makeMultiCut(name):
    '''makeMultiCut(name): makes a MultiCut feature.'''
    obj = App.ActiveDocument.addObject("Part::FeaturePython",name)
    MultiCut(obj)
    if App.GuiUp:
        ViewProviderMultiCut(obj.ViewObject)
    return obj

class MultiCut:
    "The MultiCut object"
    def __init__(self,host):
        self.Type = "MultiCut"
        host.addProperty('App::PropertyLink','Base',"MultiCut","Base solid to remove material from")
        host.addProperty('App::PropertyLink','Tool',"MultiCut","Compound of solids to subtract from Base, may intersect each other")
        host.addProperty('App::PropertyLength','Tolerance',"MultiCut","Textra tolerance to use when searching for intersections, in addition to shape tolerance")
        
        host.Proxy = self

    def execute(self,host):
        import Part
        baseshape = host.Base.Shape
        toolshape = host.Tool.Shape
        if toolshape.ShapeType == 'Compound':
            toolshapes = toolshape.childShapes()
        else:
            toolshapes = [toolshape]

        for i in range(len(toolshapes)):
            try:
                baseshape = baseshape.cut(toolshapes[i], host.Tolerance.Value)
            except Exception as err:
                App.Console.PrintError(f"{host.Label}: cut failed on toolshape[{i}]\n")
                raise
        
        host.Shape = baseshape
        
        
class ViewProviderMultiCut:
    "A View Provider for the MultiCut feature"

    def __init__(self,vobj):
        vobj.Proxy = self
       
    def getIcon(self):
        return getIconPath("Lattice2_MultiCut.svg")

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
        return [self.Object.Base, self.Object.Tool]
        
    def onDelete(self, feature, subelements): # subelements is a tuple of strings
        try:
            (self.Object.Base).ViewObject.show()
        except Exception as err:
            App.Console.PrintError("Error in onDelete: " + str(err))
        return True

# -------------------------- /document object --------------------------------------------------

# -------------------------- Gui command --------------------------------------------------

def CreateMultiCut(name):
    App.ActiveDocument.openTransaction("Create MultiCut")
    Gui.addModule('lattice2MultiCut')
    Gui.addModule('lattice2Executer')
    Gui.doCommand(f'f = lattice2MultiCut.makeMultiCut(name = {repr(name)})')
    Gui.doCommand('f.Base = Gui.Selection.getSelection()[0]')
    Gui.doCommand('f.Tool = Gui.Selection.getSelection()[1]')
    Gui.doCommand('lattice2Executer.executeFeature(f)')
    Gui.doCommand('f.Base.ViewObject.hide()')
    Gui.doCommand('f.Tool.ViewObject.hide()')
    Gui.doCommandGui('Gui.Selection.clearSelection()')
    Gui.doCommandGui('Gui.Selection.addSelection(f, "")')
    App.ActiveDocument.commitTransaction()

class CommandMultiCut:
    "Command to create MultiCut feature"
    def GetResources(self):
        return {'Pixmap'  : getIconPath("Lattice2_MultiCut.svg"),
                'MenuText': "Multi cut",
                'Accel': "",
                'ToolTip': "Subtract an array of (possibly intersecting) shapes from a shape. Select Base, then Tool, first."}
        
    def Activated(self):
        if len(Gui.Selection.getSelection()) == 2 :
            CreateMultiCut(name = "MultiCut")
        else:
            infoMessage("Lattice2 MultiCut", HELP_MESSAGE)
            
    def IsActive(self):
        if App.ActiveDocument is None:
            return False
        if activeBody() is not None:
            return False
        return len(Gui.Selection.getSelection()) in [0, 2]
            
if App.GuiUp:
    Gui.addCommand('Lattice2_MultiCut', CommandMultiCut())

exportedCommands = ['Lattice2_MultiCut']

# -------------------------- /Gui command --------------------------------------------------
