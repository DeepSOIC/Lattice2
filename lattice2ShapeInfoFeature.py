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

__title__= "Lattice ShapeInfo feature for FreeCAD"
__author__ = "DeepSOIC"
__doc__ = "Shape info feature is for getting info on a shape and exposing it in form of properties, that are useable from expressions."

from lattice2Common import *
import lattice2BaseFeature as LBF
import lattice2CompoundExplorer as LCE
import FreeCAD as App

# -------------------------- feature --------------------------------------------------

def makeShapeInfoFeature(name):
    '''makeShapeInfoFeature(name): makes a ShapeInfoFeature object.'''
    obj = App.ActiveDocument.addObject("App::FeaturePython",name)
    ShapeInfoFeature(obj)
    ViewProviderShapeInfo(obj.ViewObject)
    return obj
    

class ShapeInfoFeature:
    "The Lattice ShapeInfo object"
    def __init__(self,obj):
        self.Type = "ShapeInfoFeature"
        obj.addProperty("App::PropertyLink","Object","Lattice ShapeInfo","Object to be analyzed")
        
        obj.Proxy = self
        

    def execute(self,selfobj):
        
        self.updatedProperties = set()
        try:
            if LBF.isObjectLattice(selfobj.Object):
                plms = LBF.getPlacementsList(selfobj.Object)
                self.assignProp(selfobj,"App::PropertyInteger","NumberOfPlacements",len(plms))
                for i in range(    min(  len(plms), 10  )    ):
                    self.assignProp(selfobj,"App::PropertyPlacement","Placement"+str(i),plms[i])
            else:
                sh = selfobj.Object.Shape
                
                self.assignProp(selfobj,"App::PropertyString","ShapeType", sh.ShapeType)
                
                if sh.ShapeType == "Compound" or sh.ShapeType == "CompSolid" or sh.ShapeType == "Shell" or sh.ShapeType == "Wire":
                    self.assignProp(selfobj,"App::PropertyInteger",sh.ShapeType+"NumChildren",len(sh.childShapes(False,False)))
                if sh.ShapeType == "Compound":
                    max_depth = 0
                    num_leaves = 0
                    last_leaf = None
                    for (child, msg, it) in LCE.CompoundExplorer(sh):
                        if it.curDepth() > max_depth:
                            max_depth = it.curDepth()
                        if msg == LCE.CompoundExplorer.MSG_LEAF:
                            last_leaf = child
                            num_leaves += 1
                    self.assignProp(selfobj,"App::PropertyInteger","CompoundNestingDepth", max_depth)
                    self.assignProp(selfobj,"App::PropertyInteger","CompoundNumLeaves", num_leaves)
                    if num_leaves == 1:
                        self.assignProp(selfobj,"App::PropertyString","ShapeType", sh.ShapeType + "(" + last_leaf.ShapeType + ")")
                        sh = last_leaf

                self.transplant_all_attributes(selfobj,sh,"Shape", withdraw_set= set(["ShapeType", "Content", "Module", "TypeId"]))
                        
                if sh.ShapeType == "Face":
                    self.assignProp(selfobj,"App::PropertyFloat","Area",sh.Area)

                    typelist = ["BSplineSurface",
                                "BezierSurface",
                                "Cone",
                                "Cylinder",
                                "OffsetSurface",
                                "Plane",
                                "PlateSurface",
                                "RectangularTrimmedSurface",
                                "Sphere",
                                "SurfaceOfExtrusion",
                                "SurfaceOfRevolution",
                                "Toroid",
                                ]
                    surf = sh.Surface
                    for typename in typelist:
                        if type(surf) is getattr(Part, typename):
                            break
                        typename = None
                    self.assignProp(selfobj,"App::PropertyString","FaceType",typename)
                    
                    self.transplant_all_attributes(selfobj,surf,"Face")
                elif sh.ShapeType == "Edge":
                    self.assignProp(selfobj,"App::PropertyFloat","Length",sh.Length)

                    typelist = ["Arc",
                                "ArcOfCircle",
                                "ArcOfEllipse",
                                "ArcOfHyperbola",
                                "ArcOfParabola",
                                "BSplineCurve",
                                "BezierCurve",
                                "Circle",
                                "Ellipse",
                                "Hyperbola",
                                "Line",
                                "OffsetCurve",
                                "Parabola",
                                ]
                    crv = sh.Curve
                    for typename in typelist:
                        if type(crv) is getattr(Part, typename):
                            break
                        typename = None
                    self.assignProp(selfobj,"App::PropertyString","EdgeType",typename)
                    
                    self.transplant_all_attributes(selfobj,crv,"Edge")
                        
                elif sh.ShapeType == "Vertex":
                    self.assignProp(selfobj,"App::PropertyVector","VertexPosition",sh.Point)
        finally:
            #remove properties that haven't been updated
            for propname in selfobj.PropertiesList:
                if selfobj.getGroupOfProperty(propname) == "info":
                    if not (propname in self.updatedProperties):
                        selfobj.removeProperty(propname)
        
    def assignProp(self, selfobj, proptype, propname, propvalue):
        if not hasattr(selfobj,propname):
            selfobj.addProperty(proptype, propname,"info")
            selfobj.setEditorMode(propname,1) #set read-only
        setattr(selfobj,propname,propvalue)
        self.updatedProperties.add(propname)
        
    def transplant_all_attributes(self, selfobj, source, prefix, withdraw_set = set()):
        for attrname in dir(source):
            if attrname in withdraw_set: continue
            if attrname[0]=="_": continue
            try:
                attr = getattr(source,attrname)
            except Exception:
                continue
            if callable(attr): continue
            propname = prefix+attrname[0].upper()+attrname[1:]
            if type(attr) is int:
                self.assignProp(selfobj,"App::PropertyInteger",propname,attr)
            if type(attr) is float:
                self.assignProp(selfobj,"App::PropertyFloat",propname,attr) 
            if type(attr) is str:
                self.assignProp(selfobj,"App::PropertyString",propname,attr)
            if type(attr) is App.Vector:
                self.assignProp(selfobj,"App::PropertyVector",propname,attr)
            if type(attr) is App.Placement:
                self.assignProp(selfobj,"App::PropertyPlacement",propname,attr)
            if type(attr) is list:
                self.assignProp(selfobj,"App::PropertyInteger",propname+"Count",len(attr))

    def __getstate__(self):
        return None

    def __setstate__(self,state):
        return None

class ViewProviderShapeInfo:
    "A View Provider for the ShapeInfo object"

    def __init__(self,vobj):
        vobj.Proxy = self
        
    def getIcon(self):
        return getIconPath("Lattice2_ShapeInfoFeature.svg")
        
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
        
def CreateShapeInfo(object):
    FreeCADGui.addModule("lattice2ShapeInfoFeature")
    FreeCADGui.addModule("lattice2Executer")
    name = object.Name+"_Info"
    FreeCADGui.doCommand("f = lattice2ShapeInfoFeature.makeShapeInfoFeature(name= "+repr(name)+")")
    label = u"Shape info (" + object.Label +")"
    FreeCADGui.doCommand("f.Label = "+repr(label))    
    FreeCADGui.doCommand("f.Object = App.ActiveDocument."+object.Name)
    FreeCADGui.doCommand("lattice2Executer.executeFeature(f)")
    FreeCADGui.doCommand("Gui.Selection.addSelection(f)")    
    return App.ActiveDocument.ActiveObject

def cmdShapeInfoFeature():
    sel = FreeCADGui.Selection.getSelectionEx()
    if len(sel) == 0:
        raise SelectionError("Bad selection", "Please select some subelements from one object, first.")
    App.ActiveDocument.openTransaction("Create ShapeInfo Feature")
    for sel_item in sel:
        CreateShapeInfo(sel_item.Object)
    deselect(sel)
    App.ActiveDocument.commitTransaction()

# -------------------------- /common stuff --------------------------------------------------

# -------------------------- Gui command --------------------------------------------------

class _CommandShapeInfoFeature:
    "Command to create ShapeInfo feature"
    def GetResources(self):
        return {'Pixmap'  : getIconPath("Lattice2_ShapeInfoFeature.svg"),
                'MenuText': QtCore.QT_TRANSLATE_NOOP("Lattice2_ShapeInfoFeature","Shape info (feature)"),
                'Accel': "",
                'ToolTip': QtCore.QT_TRANSLATE_NOOP("Lattice2_ShapeInfoFeature","Shape info (feature): extract metrics from shape and expose them as properties.")}
        
    def Activated(self):
        try:
            if len(FreeCADGui.Selection.getSelection())==0:
                infoMessage("Shape info (feature)",
                    "'Shape info (feature)' command. extract metrics from shape and expose them as properties. Useful for referencing in expressions.\n\n"+
                    "Please select an object, then invoke the command.")
                return
            cmdShapeInfoFeature()
        except Exception as err:
            msgError(err)
            
    def IsActive(self):
        if App.ActiveDocument:
            return True
        else:
            return False
            
FreeCADGui.addCommand('Lattice2_ShapeInfoFeature', _CommandShapeInfoFeature())

exportedCommands = ['Lattice2_ShapeInfoFeature']

# -------------------------- /Gui command --------------------------------------------------
