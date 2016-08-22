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

__title__= "Lattice SubLink feature for FreeCAD"
__author__ = "DeepSOIC"
__doc__ = "Lattice SubLink is like Draft Facebinder, but for edges and vertices too."

from lattice2Common import *
from lattice2BaseFeature import isObjectLattice
import lattice2Markers as markers
import FreeCAD as App
import lattice2ShapeCopy as ShapeCopy

# -------------------------- feature --------------------------------------------------

def makeSubLink(name):
    '''makeSubLink(name): makes a SubLink object.'''
    obj = App.ActiveDocument.addObject("Part::FeaturePython",name)
    LatticeSubLink(obj)
    ViewProviderSubLink(obj.ViewObject)
    return obj
    

class LatticeSubLink:
    "The Lattice SubLink object"
    def __init__(self,obj):
        self.Type = "SubLink"
        obj.addProperty("App::PropertyLink","Object","Lattice SubLink","Object to extract an element from")
        
        obj.addProperty("App::PropertyStringList","SubNames","Lattice SubLink", "List of elements to extract. Example: Edge5,Edge8")
        
        obj.Proxy = self
        

    def execute(self,selfobj):
        #validity check
        if isObjectLattice(selfobj.Object):
            import lattice2Executer
            lattice2Executer.warning(selfobj,"A generic shape is expected, but a placement/array was supplied. It will be treated as a generic shape.")

        rst = [] #variable to receive the final list of shapes
        lnkobj = selfobj.Object
        for subname in selfobj.SubNames:
            subname = subname.strip()
            if len(subname)==0:
                raise ValueError("Empty subname! Not allowed.")
            if 'Face' in subname:
                index = int(subname.replace('Face',''))-1
                rst.append(lnkobj.Shape.Faces[index])
            elif 'Edge' in subname:
                index = int(subname.replace('Edge',''))-1
                rst.append(lnkobj.Shape.Edges[index])
            elif 'Vertex' in subname:
                index = int(subname.replace('Vertex',''))-1
                rst.append(lnkobj.Shape.Vertexes[index])
            else:
                lattice2Executer.warning(selfobj,"Unexpected subelement name: "+subname+". Trying to extract it with .Shape.getElement()...")
                rst.append(linkobj.Shape.getElement(subname))
        if len(rst) == 0:
            scale = 1.0
            try:
                if selfobj.Object:
                    scale = selfobj.Object[0].Shape.BoundBox.DiagonalLength/math.sqrt(3)
            except Exception as err:
                App.Console.PrintError(selfobj.Name+": Failed to estimate size of marker shape")
            if scale < DistConfusion * 100:
                scale = 1.0
            selfobj.Shape = markers.getNullShapeShape(scale)
            raise ValueError('Nothing is linked, apparently!') #Feeding empty compounds to FreeCAD seems to cause rendering issues, otherwise it would have been a good idea to output nothing.
        
        if len(rst) > 1:
            selfobj.Shape = Part.makeCompound(rst)
        else: # don't make compound of one shape, output it directly
            sh = rst[0]
            # absorb placement of original shape
            sh = ShapeCopy.transformCopy(sh)
            # apply Placement that is filled into feature's Placement property (not necessary)
            sh.Placement = selfobj.Placement
            selfobj.Shape = sh
        
    def __getstate__(self):
        return None

    def __setstate__(self,state):
        return None

class ViewProviderSubLink:
    "A View Provider for the SubLink object"

    def __init__(self,vobj):
        vobj.Proxy = self
        
    def getIcon(self):
        if len(self.Object.SubNames) == 1:
            subname = self.Object.SubNames[0]
            if 'Face' in subname:
                return getIconPath("Lattice2_SubLink_Face.svg")
            elif 'Edge' in subname:
                return getIconPath("Lattice2_SubLink_Edge.svg")
            elif 'Vertex' in subname:
                return getIconPath("Lattice2_SubLink_Vertex.svg")            
        return getIconPath("Lattice2_SubLink.svg")

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
        return []
        
def CreateSubLink(object, subnames):
    #stabilize links
    subnames = list(subnames) #'tuple' object does not support item assignment; SubElementNames of SelectionObject is a tuple
    try:
        cnt_faces = 0
        cnt_edges = 0
        cnt_vertexes = 0
        cnt_somethingelse = 0
        n_faces = None #vars to receive counts of respective subelements in the shape of object. Not prefilling them, for speed - filled only as needed
        n_edges = None
        n_vertexes = None
        for i in range(len(subnames)):
            subname = subnames[i].strip()
            if 'Face' in subname:
                index = int(subname.replace('Face',''))
                if n_faces is None:
                    n_faces = len(object.Shape.Faces)
                if (index-1)*2 > n_faces:
                    index = index - n_faces 
                subname = "Face"+str(index)
                cnt_faces += 1
            elif 'Edge' in subname:
                index = int(subname.replace('Edge',''))
                if n_edges is None:
                    n_edges = len(object.Shape.Edges)
                if (index-1)*2 > n_edges:
                    index = index - n_edges 
                subname = "Edge"+str(index)
                cnt_edges += 1
            elif 'Vertex' in subname:
                index = int(subname.replace('Vertex',''))
                if n_vertexes is None:
                    n_vertexes = len(object.Shape.Vertexes)
                if (index-1)*2 > n_vertexes:
                    index = index - n_vertexes 
                subname = "Vertex"+str(index)
                cnt_vertexes += 1
            else:
                cnt_somethingelse += 1
                pass #something unexpected, pass through unchanged
            subnames[i] = subname
    except Exception:
        pass
    FreeCADGui.addModule("lattice2SubLink")
    FreeCADGui.addModule("lattice2Executer")
    name = object.Name+"_"+subnames[0]   if len(subnames)==1 else   "SubLink"
    FreeCADGui.doCommand("f = lattice2SubLink.makeSubLink(name = "+repr(name)+")")
    label = unicode(subnames[0] if len(subnames)==1 else "subelements")  + u" of " + object.Label
    FreeCADGui.doCommand("f.Label = "+repr(label))    
    FreeCADGui.doCommand("f.Object = App.ActiveDocument."+object.Name)
    FreeCADGui.doCommand("f.SubNames = "+repr(subnames))
    FreeCADGui.doCommand("lattice2Executer.executeFeature(f)")
    if cnt_vertexes > 0 and cnt_faces+cnt_edges+cnt_somethingelse  == 0: #only vertices selected - make them bigger to make them visible
        FreeCADGui.doCommand("f.ViewObject.PointSize = 10")
    FreeCADGui.doCommand("f.Object.ViewObject.hide()")
    FreeCADGui.doCommand("Gui.Selection.addSelection(f)")    
    FreeCADGui.doCommand("f = None")
    return App.ActiveDocument.ActiveObject

def cmdSubLink():
    sel = FreeCADGui.Selection.getSelectionEx()
    if len(sel) == 0:
        raise SelectionError("Bad selection", "Please select some subelements from one object, first.")
    if len(sel) > 1:
        raise SelectionError("Bad selection", "You have selected subelements from more than one object. Not allowed. You can only select subelements of one object.")
    if len(sel[0].SubElementNames)==0:
        raise SelectionError("Bad selection", "Please select some subelements, not the whole object.")
    App.ActiveDocument.openTransaction("Create SubLink")
    CreateSubLink(sel[0].Object,sel[0].SubElementNames)
    deselect(sel)
    App.ActiveDocument.commitTransaction()

# -------------------------- /common stuff --------------------------------------------------

# -------------------------- Gui command --------------------------------------------------

class _CommandSubLink:
    "Command to create SubLink feature"
    def GetResources(self):
        return {'Pixmap'  : getIconPath("Lattice2_SubLink.svg"),
                'MenuText': QtCore.QT_TRANSLATE_NOOP("Lattice2_SubLink","SubLink"),
                'Accel': "",
                'ToolTip': QtCore.QT_TRANSLATE_NOOP("Lattice2_SubLink","SubLink: extract individual vertices, edges and faces from shapes")}
        
    def Activated(self):
        try:
            if len(FreeCADGui.Selection.getSelection())==0:
                infoMessage("SubLink",
                    "'SubLink' command. Extracts selected faces, edges or vertices from the object.\n\n"+
                    "Please select subelements of one object, then invoke the command.")
                return
            cmdSubLink()
        except Exception as err:
            msgError(err)
            
    def IsActive(self):
        if App.ActiveDocument:
            return True
        else:
            return False
            
FreeCADGui.addCommand('Lattice2_SubLink', _CommandSubLink())

exportedCommands = ['Lattice2_SubLink']

# -------------------------- /Gui command --------------------------------------------------
