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
import lattice2BaseFeature
import lattice2Executer
import lattice2CompoundExplorer as LCE
from lattice2BoundBox import getPrecisionBoundBox #needed for alignment

import lattice2Markers as markers

import FreeCAD as App
import Part


__title__="BoundingBox module for FreeCAD"
__author__ = "DeepSOIC"
__url__ = ""


def findFont(font_file_name):
    '''checks for existence of the file in a few locations and returns the full path of the first one found'''
    
    import os

    if os.path.isabs(font_file_name):
        if not os.path.exists(font_file_name):
            raise ValueError("Font file not found: " + font_file_name )
        return font_file_name


    dirlist = [] #list of directories to probe

    import lattice2Dummy
    lattice_path = os.path.dirname(lattice2Dummy.__file__)
    dirlist.append(lattice_path + "/fonts")
    
    if len(App.ActiveDocument.FileName) > 0:
        dirlist.append(os.path.dirname(App.ActiveDocument.FileName))
        
    dirlist.append(os.path.abspath(os.curdir))
    
    #todo: figure out the path to system fonts, and add it here
    
    #do the probing
    for _dir in dirlist:
        if os.path.exists(_dir + "/" + font_file_name):
            return _dir + "/" + font_file_name
    raise ValueError("Font file not found: "+font_file_name +". Locations probed: \n"+'\n'.join(dirlist))


# -------------------------- document object --------------------------------------------------

def makeLatticeShapeString(name):
    '''makeBoundBox(name): makes a BoundBox object.'''
    typ = 'Part::Part2DObjectPython' if activeBody() else 'Part::FeaturePython'
    obj = FreeCAD.ActiveDocument.addObject(typ, name)
    LatticeShapeString(obj)
    if FreeCAD.GuiUp:        
        ViewProviderLatticeShapeString(obj.ViewObject)
    return obj

class FoolFeatureDocumentObject:
    '''A class that is to be fed to Draft ShapeString object instead of a real one, to obtain shapes it generates'''
    def __init__(self):
        self.Placement = App.Placement()
        self.Shape = Part.Shape()
        self.properties = []
        self.Proxy = None
        self.PropertiesList=[]
    
    def addProperty(self, proptype, propname, group = None, hint = None, locked = False):
        setattr(self,propname,None)
        self.properties.append((proptype, propname, group, hint, locked))
        return self
    
    def positionBySupport(self):
        return False
    

class LatticeShapeString:
    "The LatticeShapeString object"
    def __init__(self,obj):
        self.Type = "LatticeShapeString"
        
        
        #initialize accompanying Draft ShapeString
        self.makeFoolObj(obj)
        foolObj = self.foolObj
        
        #add Draft ShapeString's properties to document object in possession of our LatticeShapeString
        for (proptype, propname, group, hint, locked) in foolObj.properties:
            if propname != "String": #we'll define our own string property
                obj.addProperty(proptype,propname,"Lattice ShapeString",hint)
        
        
        obj.addProperty("App::PropertyLink","ArrayLink","Lattice ShapeString","array to use for the shapestring")

        obj.addProperty("App::PropertyStringList","Strings","Lattice ShapeString","Strings to put at each placement.")

        obj.addProperty("App::PropertyEnumeration","XAlign","Lattice ShapeString","Horizontal alignment of individual strings")
        obj.XAlign = ['None','Left','Right','Middle']

        obj.addProperty("App::PropertyEnumeration","YAlign","Lattice ShapeString","Vertical alignment of individual strings")
        obj.YAlign = ['None','Top','Bottom','Middle']

        obj.addProperty("App::PropertyBool","AlignPrecisionBoundBox","Lattice ShapeString","Use precision bounding box for alignment. Warning: slow!")
        
        obj.addProperty("App::PropertyFile","FullPathToFont","Lattice ShapeString","Full path of font file that is actually being used.")
        obj.setEditorMode("FullPathToFont", 1) # set read-only
                
        #FIXME: make Draft take care of this
        if not getattr(obj, "Justification", True): #fill only if present but empty
                obj.Justification = ["Top-Left", "Top-Center", "Top-Right",
                        "Middle-Left", "Middle-Center", "Middle-Right",
                        "Bottom-Left", "Bottom-Center", "Bottom-Right"]
                obj.Justification = "Middle-Center"

        #FIXME: make Draft take care of this
        if not getattr(obj, "JustificationReference", True): #fill only if present but empty
                obj.JustificationReference = ["Cap Height", "Shape Height"]
                obj.JustificationReference = "Cap Height"

        obj.Proxy = self
        
        self.setDefaults(obj)
        
    def makeFoolObj(self,obj):
        '''Makes an object that mimics a Part::FeaturePython, and makes a Draft 
        ShapeString object on top of it. Both are added as attributes to self. 
        This is needed to re-use Draft ShapeString'''
        
        if hasattr(self, "foolObj"):
            return
        foolObj = FoolFeatureDocumentObject()
        from Draft import _ShapeString
        self.draft_shape_string = _ShapeString(foolObj) 
        self.foolObj = foolObj

        
    def setDefaults(self, obj):
        '''initializes the properties, so that LatticeShapeString can be used with no initial fiddling'''
        obj.FontFile = "FreeUniversal-Regular.ttf"
        obj.Size = 10
        obj.Tracking = 0
        obj.Strings = ['string1','string2']

    def execute(self,obj):
        nOfStrings = len(obj.Strings)
        lattice = screen(obj.ArrayLink)
        if lattice is None:
            plms = [App.Placement() for i in range(0,nOfStrings)]
        else:
            if not lattice2BaseFeature.isObjectLattice(lattice):
                lattice2Executer.warning(obj,"ShapeString's link to array must point to a lattice. It points to a generic shape. Results may be unexpected.")
            leaves = LCE.AllLeaves(lattice.Shape)
            plms = [leaf.Placement for leaf in leaves]
        
        #update foolObj's properties
        self.makeFoolObj(obj) #make sure we have one - fixes defunct Lattice ShapeString after save-load
        for (proptype, propname, group, hint, locked) in self.foolObj.properties:
            if propname != "String": #ignore "String", that will be taken care of in the following loop
                if hasattr(obj, propname):
                    setattr(self.foolObj, propname, getattr(obj, propname))
        self.foolObj.FontFile = findFont(obj.FontFile)
        obj.FullPathToFont = self.foolObj.FontFile
        
        shapes = []
        n_nonempty = 0
        for i in range(  0 ,  min(len(plms),len(obj.Strings))  ):
            if len(obj.Strings[i]) > 0:
                #generate shapestring using Draft
                self.foolObj.String = obj.Strings[i]
                self.foolObj.Shape = None
                self.draft_shape_string.execute(self.foolObj)
                shape = self.foolObj.Shape #might still be None if the string is just whitespace
            else:
                shape = None

            if shape is None:
                # add empty compound
                shape = Part.Compound([])
                shape.Placement = plms[i].multiply(shape.Placement)
                shapes.append(shape)
            else:
                #calculate alignment point
                if obj.XAlign == 'None' and obj.YAlign == 'None':
                    pass #need not calculate boundbox
                else:
                    if obj.AlignPrecisionBoundBox:
                        bb = getPrecisionBoundBox(shape)
                    else:
                        bb = shape.BoundBox

                alignPnt = App.Vector()
                
                if obj.XAlign == 'Left':
                    alignPnt.x = bb.XMin
                elif obj.XAlign == 'Right':
                    alignPnt.x = bb.XMax
                elif obj.XAlign == 'Middle':
                    alignPnt.x = bb.Center.x

                if obj.YAlign == 'Bottom':
                    alignPnt.y = bb.YMin
                elif obj.YAlign == 'Top':
                    alignPnt.y = bb.YMax
                elif obj.YAlign == 'Middle':
                    alignPnt.y = bb.Center.y
                
                #Apply alignment
                shape.Placement = App.Placement(alignPnt*(-1.0), App.Rotation()).multiply(shape.Placement)
                
                #Apply placement from array
                shape.Placement = plms[i].multiply(shape.Placement)
                
                shapes.append(shape)
                n_nonempty += 1
       
        if n_nonempty == 0:
            scale = 1.0
            if lattice is not None:
                scale = lattice.Shape.BoundBox.DiagonalLength/math.sqrt(3)/math.sqrt(len(shps))
            if scale < DistConfusion * 100:
                scale = 1.0
            obj.Shape = markers.getNullShapeShape(scale)
            raise ValueError('No strings were converted into shapes') #Feeding empty compounds to FreeCAD seems to cause rendering issues, otherwise it would have been a good idea to output nothing.
        result = Part.makeCompound(shapes)
        result.Placement = obj.Placement
        obj.Shape = result
        

    def __getstate__(self):
        return None

    def __setstate__(self,state):
        return None
        
    def dumps(self):
        return None

    def loads(self,state):
        return None

        
class ViewProviderLatticeShapeString:
    "A View Provider for the LatticeShapeString object"

    def __init__(self,vobj):
        vobj.Proxy = self
       
    def getIcon(self):
        return getIconPath("Lattice2_ShapeString.svg")

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

def CreateLatticeShapeString(name):
    sel = FreeCADGui.Selection.getSelectionEx()
    FreeCAD.ActiveDocument.openTransaction("Create LatticeShapeString")
    FreeCADGui.addModule("lattice2ShapeString")
    FreeCADGui.addModule("lattice2Executer")
    FreeCADGui.addModule("lattice2Base.Autosize")
    FreeCADGui.doCommand("f = lattice2ShapeString.makeLatticeShapeString(name='"+name+"')")
    if len(sel) == 1:
        FreeCADGui.doCommand("f.ArrayLink = FreeCADGui.Selection.getSelection()[0]")
    else:
        FreeCADGui.doCommand("f.Placement.Base = lattice2Base.Autosize.convenientPosition()")
    FreeCADGui.doCommand("f.Size = lattice2Base.Autosize.convenientModelSize()/10")
    FreeCADGui.doCommand("lattice2Executer.executeFeature(f)")
    FreeCADGui.doCommand("f = None")
    FreeCAD.ActiveDocument.commitTransaction()


# -------------------------- /common stuff --------------------------------------------------

# -------------------------- Gui command --------------------------------------------------

class _CommandLatticeShapeString:
    "Command to create LatticeShapeString feature"
    def GetResources(self):
        return {'Pixmap'  : getIconPath("Lattice2_ShapeString.svg"),
                'MenuText': QtCore.QT_TRANSLATE_NOOP("Lattice2_ShapeString","ShapeString for arraying"),
                'Accel': "",
                'ToolTip': QtCore.QT_TRANSLATE_NOOP("Lattice2_ShapeString","Make strings at given placements")}
        
    def Activated(self):
        if len(FreeCADGui.Selection.getSelection()) == 0 or len(FreeCADGui.Selection.getSelection()) == 1:
            CreateLatticeShapeString(name = "Strings")
        else:
            mb = QtGui.QMessageBox()
            mb.setIcon(mb.Icon.Warning)
            mb.setText(translate("Lattice2_ShapeString", "Either select nothing, or just one lattice object! You seem to have more than one object selected.", None))
            mb.setWindowTitle(translate("Lattice2_ShapeString","Bad selection", None))
            mb.exec_()
            
    def IsActive(self):
        if FreeCAD.ActiveDocument:
            return True
        else:
            return False
            
if FreeCAD.GuiUp:
    FreeCADGui.addCommand('Lattice2_ShapeString', _CommandLatticeShapeString())

exportedCommands = ['Lattice2_ShapeString']

# -------------------------- /Gui command --------------------------------------------------
