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
from lattice2ShapeCopy import shallowCopy


def getDefLatticeFaceColor():
    return (1.0, 0.7019608020782471, 0.0, 0.0) #orange
def getDefShapeColor():
    clr = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/View").GetUnsigned("DefaultShapeColor")
    #convert color in int to color in tuple of 4 floats.
    #This is probably implemented already somewhere, but I couldn't find, so I rolled my own --DeepSOIC
    # clr in hex looks like this: 0xRRGGBBOO (r,g,b,o = red, green, blue, opacity)
    o = clr & 0x000000FF
    b = (clr >> 8) & 0x000000FF
    g = (clr >> 16) & 0x000000FF
    r = (clr >> 24) & 0x000000FF
    return (r/255.0, g/255.0, b/255.0, (255-o)/255.0)
    

def makeLatticeFeature(name, AppClass, ViewClass, no_body = False, no_disable_attacher = False):
    '''makeLatticeFeature(name, AppClass, ViewClass, no_body = False): makes a document object for a LatticeFeature-derived object.
    
    no_body: if False, the Lattice object will end up in an active body, and Part2DObject will be used.
    no_disable_attacher: if True, attachment properties of Part2DObject won't be hidden'''
    
    body = activeBody()
    if body and not no_body:
        obj = body.newObject("Part::Part2DObjectPython",name) #hack: body accepts any 2dobjectpython, thinking it is a sketch. Use it to get into body. This does cause some weirdness (e.g. one can Pad a placement), but that is rather minor. 
        obj.AttacherType = 'Attacher::AttachEngine3D'
    else:
        obj = FreeCAD.ActiveDocument.addObject("Part::FeaturePython",name)
    AppClass(obj)
    
    if FreeCAD.GuiUp:
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
    if documentObject.isDerivedFrom('PartDesign::ShapeBinder'):
        if len(documentObject.Support) == 1 and documentObject.Support[0][1] == ('',):
            ret = isObjectLattice(documentObject.Support[0][0])
    if hasattr(documentObject, 'IAm') and documentObject.IAm == 'PartOMagic.Ghost':
        ret = isObjectLattice(documentObject.Base)
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

    


class LatticeFeature(object):
    "Base object for lattice objects (arrays of placements)"
    
    def __init__(self,obj):
        # please, don't override. Override derivedInit instead.
        obj.addProperty('App::PropertyString', 'Type', "Lattice", "module_name.class_name of this object, for proxy recovery", 0, True, True)
        obj.Type = self.__module__ + '.' + type(self).__name__

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
        
        prop = "ExposePlacement"
        obj.addProperty("App::PropertyBool",prop,"Lattice","Makes the placement syncronized to Placement property. This will oftem make this object unmoveable. Not applicable to arrays.")

        self.derivedInit(obj)
        
        obj.Proxy = self
        
    def assureProperty(self, selfobj, proptype, propname, defvalue, group, tooltip):
        """assureProperty(selfobj, proptype, propname, defvalue, group, tooltip): adds
        a property if one is missing, and sets its value to default. Does nothing if property 
        already exists. Returns True if property was created, or False if not."""
        
        return assureProperty(selfobj, proptype, propname, defvalue, group, tooltip)
        
    def derivedInit(self, obj):
        '''for overriding by derived classes'''
        pass
        
    def execute(self,obj):
        # please, don't override. Override derivedExecute instead.

        plms = self.derivedExecute(obj)

        if plms is not None:
            if plms == "suppress":
                return
            obj.NumElements = len(plms)
            shapes = []
            markerSize = obj.MarkerSize
            if markerSize < DistConfusion:
                markerSize = getMarkerSizeEstimate(plms)
            marker = lattice2Markers.getPlacementMarker(scale= markerSize, markerID= obj.MarkerShape)
            
            bExposing = False
            if obj.ExposePlacement:
                if len(plms) == 1:
                    bExposing = True
                else:
                    lattice2Executer.warning(obj,"Multiple placements are being fed, can't expose placements. Placement property will be forced to zero.")
                    obj.Placement = App.Placement()
            
            if bExposing:
                obj.Shape = shallowCopy(marker)
                obj.Placement = plms[0]
            else:
                for plm in plms:
                    sh = shallowCopy(marker)
                    sh.Placement = plm
                    shapes.append(sh)
                    
                if len(shapes) == 0:
                    obj.Shape = lattice2Markers.getNullShapeShape(markerSize)
                    raise ValueError('Lattice object is null') 
                
                sh = Part.makeCompound(shapes)
                sh.Placement = obj.Placement
                obj.Shape = sh

            if obj.isLattice == 'Auto-Off':
                obj.isLattice = 'Auto-On'
            
        else:
            # DerivedExecute didn't return anything. Thus we assume it 
            # has assigned the shape, and thus we don't do anything.
            # Moreover, we assume that it is no longer a lattice object, so:
            if obj.isLattice == 'Auto-On':
                obj.isLattice = 'Auto-Off'
                
            if obj.ExposePlacement:
                if obj.Shape.ShapeType == "Compound":
                    children = obj.Shape.childShapes()
                    if len(children) == 1:
                        obj.Placement = children[0].Placement
                        obj.Shape = children[0]
                    else:
                        obj.Placement = App.Placement()
                else:
                    #nothing to do - FreeCAD will take care to make obj.Placement and obj.Shape.Placement synchronized.
                    pass
        return
    
    def derivedExecute(self,obj):
        '''For overriding by derived class. If this returns a list of placements,
            it's going to be used to build the shape. If returns None, it is assumed that 
            derivedExecute has already assigned the shape, and no further actions are needed. 
            Moreover, None is a signal that the object is not a lattice array, and it will 
            morph into a non-lattice if isLattice is set to auto'''
        return []
                
    def verifyIntegrity(self):
        try:
            if self.__init__.__func__ is not LatticeFeature.__init__.__func__:
                FreeCAD.Console.PrintError("__init__() of lattice object is overridden. Please don't! Fix it!\n")
            if self.execute.__func__ is not LatticeFeature.execute.__func__:
                FreeCAD.Console.PrintError("execute() of lattice object is overridden. Please don't! Fix it!\n")
        except AttributeError as err:
            pass # quick-n-dirty fix for Py3. TODO: restore the functionality in Py3, or remove this routine altogether.
            
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
                    
    def __getstate__(self):
        return None

    def __setstate__(self,state):
        return None
    
    def disableAttacher(self, selfobj, enable= False):
        if selfobj.isDerivedFrom('Part::Part2DObject'):
            attachprops = [
                'Support', 
                'MapMode', 
                'MapReversed', 
                'MapPathParameter', 
                'AttachmentOffset', 
            ]
            for prop in attachprops:
                selfobj.setEditorMode(prop, 0 if enable else 2)
            if enable:
                selfobj.MapMode = selfobj.MapMode #trigger attachment, to make it update property states
    
    def onDocumentRestored(self, selfobj):
        #override to have attachment!
        self.disableAttacher(selfobj)

    
class ViewProviderLatticeFeature(object):
    "A View Provider for base lattice object"

    def __init__(self,vobj):
        '''Don't override. Override derivedInit, please!'''
        vobj.Proxy = self
        vobj.addProperty('App::PropertyString', 'Type', "Lattice", "module_name.class_name of this object, for proxy recovery", 0, True, True)
        vobj.Type = self.__module__ + '.' + type(self).__name__

        
        prop = "DontUnhideOnDelete"
        vobj.addProperty("App::PropertyBool",prop,"Lattice","Makes the element be populated into object's Placement property")
        vobj.setEditorMode(prop, 2) # set hidden
        
        self.derivedInit(vobj)

    def derivedInit(self,vobj):
        pass
       
    def verifyIntegrity(self):
        try:
            if self.__init__.__func__ is not ViewProviderLatticeFeature.__init__.__func__:
                FreeCAD.Console.PrintError("__init__() of lattice object view provider is overridden. Please don't! Fix it!\n")
        except AttributeError as err:
            pass # quick-n-dirty fix for Py3. TODO: restore the functionality in Py3, or remove this routine altogether.

    def getIcon(self):
        return getIconPath("Lattice.svg")

    def attach(self, vobj):
        self.ViewObject = vobj
        self.Object = vobj.Object

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
            FreeCAD.Console.PrintError("Error in onDelete: " + str(err))
        return True


def assureProperty(docobj, proptype, propname, defvalue, group, tooltip):
    """assureProperty(docobj, proptype, propname, defvalue, group, tooltip): adds
    a property if one is missing, and sets its value to default. Does nothing if property 
    already exists. Returns True if property was created, or False if not."""
    
    if hasattr(docobj, propname):
        #todo: check type match
        return False
        
    docobj.addProperty(proptype, propname, group, tooltip)
    if defvalue is not None:
        setattr(docobj, propname, defvalue)
    return True

    
 # ----------------------utility functions -------------------------------------

def makeMoveFromTo(plmFrom, plmTo):
    '''makeMoveFromTo(plmFrom, plmTo): construct a placement that moves something 
    from one placement to another placement'''
    return plmTo.multiply(plmFrom.inverse())

def getPlacementsList(documentObject, context = None, suppressWarning = False):
    '''getPlacementsList(documentObject, context = None): extract list of placements 
    from an array object. Context is an object to report as context, when displaying 
    a warning if the documentObject happens to be a non-lattice.'''
    if not isObjectLattice(documentObject):
        if not suppressWarning:
            lattice2Executer.warning(context, documentObject.Name + " is not a placement or an array of placements. Results may be unexpected.")
    leaves = LCE.AllLeaves(documentObject.Shape)
    return [leaf.Placement for leaf in leaves]

def splitSelection(sel):
    '''splitSelection(sel): splits sel (use getSelectionEx()) into lattices and non-lattices.
    returns a tuple: (lattices, shapes). lattices is a list, containing all objects 
    that are lattices (placements of arrays of placements). shapes contains all 
    the rest. The lists conain SelectionObjects, not the actual document objects.'''
    lattices = []
    shapes = []
    for selobj in sel:
        if isObjectLattice(selobj.Object):
            lattices.append(selobj)
        else:
            shapes.append(selobj)
    return (lattices, shapes)

