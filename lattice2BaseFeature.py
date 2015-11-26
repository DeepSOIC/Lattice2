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

__title__="Base feature module for lattice object of lattice workbench for FreeCAD"
__author__ = "DeepSOIC"
__url__ = ""

import FreeCAD as App
import Part

from lattice2Common import *
import lattice2CompoundExplorer as LCE
import lattice2Markers
import lattice2Executer

def getDefLatticeFaceColor():
    return (1.0, 0.7019608020782471, 0.0, 0.0) #orange
def getDefShapeColor():
    clr = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/View").GetUnsigned("DefaultShapeColor")
    #convert color in int to color in tuple of 4 floats.
    #This is probably implemented already somewhere, but I couldn't find, so I rolled my own --DeepSOIC
    # clr in hex looks like this: 0xRRGGBBOO (r,g,b,o = red, green, blue, opacity)
    o = clr & 0x000000FFL
    b = (clr >> 8) & 0x000000FFL
    g = (clr >> 16) & 0x000000FFL
    r = (clr >> 24) & 0x000000FFL
    return (r/255.0, g/255.0, b/255.0, (255-o)/255.0)
    

def makeLatticeFeature(name, AppClass, ViewClass):
    '''makeLatticeFeature(name, AppClass, ViewClass = None): makes a document object for a LatticeFeature-derived object.'''
    obj = FreeCAD.ActiveDocument.addObject("Part::FeaturePython",name)
    AppClass(obj)
    if ViewClass:
        vp = ViewClass(obj.ViewObject)
    else:
        vp = ViewProviderLatticeFeature(obj.ViewObject)
        
    return obj
    
    
def isObjectLattice(documentObject):
    '''isObjectLattice(documentObject): When operating on the object, it is to be treated as a lattice object. If False, treat as a regular shape.'''
    ret = False
    if hasattr(documentObject,"isLattice"):
        if 'On' in documentObject.isLattice:
            ret = True
    return ret
    
def getMarkerSizeEstimate(ListOfPlacements):
    '''getMarkerSizeEstimate(ListOfPlacements): computes the default marker size for the array of placements'''
    if len(ListOfPlacements) == 0:
        return 1.0
    pathLength = 0
    for i in range(1, len(ListOfPlacements)):
        pathLength += (ListOfPlacements[i].Base - ListOfPlacements[i-1].Base).Length
    sz = pathLength/len(ListOfPlacements)/2.0
    #FIXME: make hierarchy-aware
    if sz < DistConfusion*10:
        sz = 1.0
    return sz

    


class LatticeFeature():
    "Base object for lattice objects (arrays of placements)"
    
    def __init__(self,obj):
        # please, don't override. Override derivedInit instead.
        self.Type = "latticeFeature"

        prop = "NumElements"
        obj.addProperty("App::PropertyInteger",prop,"Lattice","Info: number of placements in the array")
        obj.setEditorMode(prop, 1) # set read-only
        
        obj.addProperty("App::PropertyLength","MarkerSize","Lattice","Size of placement markers (set to zero for automatic).")
        
        obj.addProperty("App::PropertyEnumeration","MarkerShape","Lattice","Choose the preferred shape of placement markers.")
        obj.MarkerShape = ["tetra-orimarker","paperplane-orimarker"]
        obj.MarkerShape = "paperplane-orimarker" #TODO: setting for choosing the default

        obj.addProperty("App::PropertyEnumeration","isLattice","Lattice","Sets whether this object should be treated as a lattice by further operations")
        obj.isLattice = ['Auto-Off','Auto-On','Force-Off','Force-On']
        # Auto-On an Auto-Off can be modified when recomputing. Force values are going to stay.
        
        #Hidden properties affecting some standard behaviours
        prop = "SingleByDesign"
        obj.addProperty("App::PropertyBool",prop,"Lattice","Makes the element be populated into object's Placement property")
        obj.setEditorMode(prop, 2) # set hidden

        self.derivedInit(obj)
        
        obj.Proxy = self

        
    def derivedInit(self, obj):
        '''for overriding by derived classes'''
        pass
        
    def execute(self,obj):
        # please, don't override. Override derivedExecute instead.

        plms = self.derivedExecute(obj)

        if plms is not None:
            obj.NumElements = len(plms)
            shapes = []
            markerSize = obj.MarkerSize
            if markerSize < DistConfusion:
                markerSize = getMarkerSizeEstimate(plms)
            marker = lattice2Markers.getPlacementMarker(scale= markerSize, markerID= obj.MarkerShape)
            #FIXME: make hierarchy-aware
            if obj.SingleByDesign:
                if len(plms) != 1:
                    lattice2Executer.warning(obj,"Multiple placements are being fed, but object is single by design. Only fisrt placement will be used...")
                obj.Shape = marker.copy()
                obj.Placement = plms[0]
            else:
                for plm in plms:
                    sh = marker.copy()
                    sh.Placement = plm
                    shapes.append(sh)
                    
                if len(shapes) == 0:
                    obj.Shape = lattice2Markers.getNullShapeShape(markerSize)
                    raise ValueError('Lattice object is null') #Feeding empty compounds to FreeCAD seems to cause rendering issues, otherwise it would have been a good idea to output nothing.
                
                sh = Part.makeCompound(shapes)
                obj.Shape = sh

            if obj.isLattice == 'Auto-Off':
                obj.isLattice = 'Auto-On'
            
        else:
            # DerivedExecute didn't return anything. Thus we assume it 
            # has assigned the shape, and thus we don't do anything.
            # Moreover, we assume that it is no longer a lattice object, so:
            if obj.isLattice == 'Auto-On':
                obj.isLattice = 'Auto-Off'
            obj.NumElements = len(obj.Shape.childShapes(False,False))
        
        return
    
    def derivedExecute(self,obj):
        '''For overriding by derived class. If this returns a list of placements,
            it's going to be used to build the shape. If returns None, it is assumed that 
            derivedExecute has already assigned the shape, and no further actions are needed. 
            Moreover, None is a signal that the object is not a lattice array, and it will 
            morph into a non-lattice if isLattice is set to auto'''
        return []
                
    def verifyIntegrity(self):
        if self.__init__.__func__ is not LatticeFeature.__init__.__func__:
            FreeCAD.Console.PrintError("__init__() of lattice object is overridden. Please don't! Fix it!\n")
        if self.execute.__func__ is not LatticeFeature.execute.__func__:
            FreeCAD.Console.PrintError("execute() of lattice object is overridden. Please don't! Fix it!\n")
    
    def onChanged(self, obj, prop): #prop is a string - name of the property
        if prop == 'isLattice':
            if obj.ViewObject is not None:
                try:
                    if isObjectLattice(obj):
                        #obj.ViewObject.DisplayMode = 'Shaded'
                        obj.ViewObject.ShapeColor = getDefLatticeFaceColor()
                        obj.ViewObject.Lighting = 'One side'
                    else:
                        #obj.ViewObject.DisplayMode = 'Flat Lines'
                        obj.ViewObject.ShapeColor = getDefShapeColor()
                except App.Base.FreeCADError as err:
                    #these errors pop up while loading project file, apparently because
                    # viewprovider is up already, but the shape vis mesh wasn't yet
                    # created. It is safe to ignore them, as DisplayMode is eventually
                    # restored to the correct values. 
                    #Proper way of dealing with it would have been by testing for 
                    # isRestoring(??), but I failed to find the way to do it.
                    #--DeepSOIC
                    pass 
                    
    
class ViewProviderLatticeFeature:
    "A View Provider for base lattice object"

    def __init__(self,vobj):
        '''Don't override. Override derivedInit, please!'''
        vobj.Proxy = self
        
        prop = "DontUnhideOnDelete"
        vobj.addProperty("App::PropertyBool",prop,"Lattice","Makes the element be populated into object's Placement property")
        vobj.setEditorMode(prop, 2) # set hidden
        
        self.derivedInit(vobj)

    def derivedInit(self,vobj):
        pass
       
    def verifyIntegrity(self):
        if self.__init__.__func__ is not ViewProviderLatticeFeature.__init__.__func__:
            FreeCAD.Console.PrintError("__init__() of lattice object view provider is overridden. Please don't! Fix it!\n")

    def getIcon(self):
        return getIconPath("Lattice.svg")

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
        self.Object.Proxy.verifyIntegrity()
        self.verifyIntegrity()
        return []

    def onDelete(self, feature, subelements): # subelements is a tuple of strings
        try:
            if hasattr(self.ViewObject,"DontUnhideOnDelete") and self.ViewObject.DontUnhideOnDelete:
                pass
            else:
                children = self.claimChildren()
                if children and len(children) > 0:
                    marker = lattice2Markers
                    for child in children:
                        child.ViewObject.show()
        except Exception as err:
            # catch all exceptions, because we don't want to prevent deletion if something goes wrong
            FreeCAD.Console.PrintError("Error in onDelete: " + err.message)
        return True

    