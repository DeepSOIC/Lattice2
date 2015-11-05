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

__title__="CompoundFilter module for FreeCAD"
__author__ = "DeepSOIC"
__url__ = ""


try:
    from latticeBaseFeature import isObjectLattice
except Exception:
    # I want to keep the module easy to strip off Lattice wb, so:
    def isObjectLattice(obj):
        return False

# -------------------------- common stuff --------------------------------------------------

def makeCompoundFilter(name):
    '''makeCompoundFilter(name): makes a CompoundFilter object.'''
    obj = FreeCAD.ActiveDocument.addObject("Part::FeaturePython",name)
    _CompoundFilter(obj)
    _ViewProviderCompoundFilter(obj.ViewObject)
    return obj

class _CompoundFilter:
    "The CompoundFilter object"
    def __init__(self,obj):
        self.Type = "CompoundFilter"
        obj.addProperty("App::PropertyLink","Base","CompoundFilter","Compound to be filtered")
        
        obj.addProperty("App::PropertyEnumeration","FilterType","CompoundFilter","")
        obj.FilterType = ['bypass','specific items','collision-pass','window-volume','window-area','window-length','window-distance']
        obj.FilterType = 'bypass'
        
        # properties controlling "specific items" mode
        obj.addProperty("App::PropertyString","items","CompoundFilter","list of indexes of childs to be returned (like this: 1,4,8:10).")

        obj.addProperty("App::PropertyLink","Stencil","CompoundFilter","Object that defines filtering")
        
        obj.addProperty("App::PropertyFloat","WindowFrom","CompoundFilter","Value of threshold, expressed as a percentage of maximum value.")
        obj.WindowFrom = 80.0
        obj.addProperty("App::PropertyFloat","WindowTo","CompoundFilter","Value of threshold, expressed as a percentage of maximum value.")
        obj.WindowTo = 100.0

        obj.addProperty("App::PropertyFloat","OverrideMaxVal","CompoundFilter","Volume threshold, expressed as percentage of the volume of largest child")
        obj.OverrideMaxVal = 0
        
        obj.addProperty("App::PropertyBool","Invert","CompoundFilter","Output shapes that are rejected by filter, instead")
        obj.Invert = False
        
        obj.Proxy = self
        

    def execute(self,obj):
        #validity check
        if isObjectLattice(obj.Base):
            import latticeExecuter
            latticeExecuter.warning(obj,"A generic shape is expected, but a lattice object was supplied. It will be treated as a generic shape.")

        rst = [] #variable to receive the final list of shapes
        shps = obj.Base.Shape.childShapes()
        if obj.FilterType == 'bypass':
            rst = shps
        elif obj.FilterType == 'specific items':
            rst = []
            flags = [False] * len(shps)
            ranges = obj.items.split(';')
            for r in ranges:
                r_v = r.split(':')
                if len(r_v) == 1:
                    i = int(r_v[0])
                    rst.append(shps[i])
                    flags[i] = True
                elif len(r_v) == 2 or len(r_v) == 3:
                    ifrom = None   if len(r_v[0].strip()) == 0 else   int(r_v[0])                    
                    ito = None     if len(r_v[1].strip()) == 0 else   int(r_v[1])
                    istep = None   if len(r_v[2].strip()) == 0 else   int(r_v[2])
                    rst=rst+shps[ifrom:ito:istep]
                    for b in flags[ifrom:ito:istep]:
                        b = True
                else:
                    raise ValueError('index range cannot be parsed:'+r)
            if obj.Invert :
                rst = []
                for i in xrange(0,len(shps)):
                    if not flags[i]:
                        rst.append(shps[i])
        elif obj.FilterType == 'collision-pass':
            stencil = obj.Stencil.Shape
            for s in shps:
                d = s.distToShape(stencil)
                if bool(d[0] < DistConfusion) ^ bool(obj.Invert):
                    rst.append(s)
        elif obj.FilterType == 'window-volume' or obj.FilterType == 'window-area' or obj.FilterType == 'window-length' or obj.FilterType == 'window-distance':
            vals = [0.0] * len(shps)
            for i in xrange(0,len(shps)):
                if obj.FilterType == 'window-volume':
                    vals[i] = shps[i].Volume
                elif obj.FilterType == 'window-area':
                    vals[i] = shps[i].Area
                elif obj.FilterType == 'window-length':
                    vals[i] = shps[i].Length
                elif obj.FilterType == 'window-distance':
                    vals[i] = shps[i].distToShape(obj.Stencil.Shape)[0]
            
            maxval = max(vals)
            if obj.Stencil:
                if obj.FilterType == 'window-volume':
                    vals[i] = obj.Stencil.Shape.Volume
                elif obj.FilterType == 'window-area':
                    vals[i] = obj.Stencil.Shape.Area
                elif obj.FilterType == 'window-length':
                    vals[i] = obj.Stencil.Shape.Length
            if obj.OverrideMaxVal:
                maxval = obj.OverrideMaxVal
            
            valFrom = obj.WindowFrom / 100.0 * maxval
            valTo = obj.WindowTo / 100.0 * maxval
            
            for i in xrange(0,len(shps)):
                if bool(vals[i] >= valFrom and vals[i] <= valTo) ^ obj.Invert:
                    rst.append(shps[i])
        else:
            raise ValueError('Filter mode not implemented:'+obj.FilterType)
        
        if len(rst) == 0:
            scale = 1.0
            if not obj.Base.Shape.isNull():
                scale = obj.Base.Shape.BoundBox.DiagonalLength/math.sqrt(3)/math.sqrt(len(shps))
            if scale < DistConfusion * 100:
                scale = 1.0
            print scale
            obj.Shape = markers.getNullShapeShape(scale)
            raise ValueError('Nothing passes through the filter') #Feeding empty compounds to FreeCAD seems to cause rendering issues, otherwise it would have been a good idea to output nothing.
        
        if len(rst) > 1:
            obj.Shape = Part.makeCompound(rst)
        else: # don't make compound of one shape, output it directly
            sh = rst[0]
            sh.transformShape(sh.Placement.toMatrix(),True) #True = make copy
            sh.Placement = FreeCAD.Placement()
            obj.Shape = sh
            
        return
        
        
class _ViewProviderCompoundFilter:
    "A View Provider for the CompoundFilter object"

    def __init__(self,vobj):
        vobj.Proxy = self
        vobj.addProperty("App::PropertyBool","DontUnhideOnDelete","CompoundFilter","When this object is deleted, Base and Stencil are unhidden. This flag stops it from happening.")       
        vobj.setEditorMode("DontUnhideOnDelete", 2) # set hidden
        
    def getIcon(self):
        return getIconPath("Lattice_CompoundFilter.svg")

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
        children = [self.Object.Base]
        if self.Object.Stencil:
            children.append(self.Object.Stencil)
        return children

    def onDelete(self, feature, subelements): # subelements is a tuple of strings
        if not self.ViewObject.DontUnhideOnDelete:
            try:
                self.Object.Base.ViewObject.show()
                if self.Object.Stencil:
                    self.Object.Stencil.ViewObject.show()
            except Exception as err:
                FreeCAD.Console.PrintError("Error in onDelete: " + err.message)
        return True

def CreateCompoundFilter(name):
    sel = FreeCADGui.Selection.getSelection()
    FreeCAD.ActiveDocument.openTransaction("Create CompoundFilter")
    FreeCADGui.addModule("CompoundFilter")
    FreeCADGui.addModule("latticeExecuter")
    FreeCADGui.doCommand("f = CompoundFilter.makeCompoundFilter(name = '"+name+"')")
    FreeCADGui.doCommand("f.Base = App.ActiveDocument."+sel[0].Name)
    FreeCADGui.doCommand("f.Base.ViewObject.hide()")
    if len(sel) == 2:
        FreeCADGui.doCommand("f.Stencil = App.ActiveDocument."+sel[1].Name)
        FreeCADGui.doCommand("f.Stencil.ViewObject.hide()")
        FreeCADGui.doCommand("f.FilterType = 'collision-pass'")
    else:
        FreeCADGui.doCommand("f.FilterType = 'window-volume'")    
    FreeCADGui.doCommand("latticeExecuter.executeFeature(f)")
    FreeCADGui.doCommand("f = None")
    FreeCAD.ActiveDocument.commitTransaction()


# -------------------------- /common stuff --------------------------------------------------

# -------------------------- Gui command --------------------------------------------------

class _CommandCompoundFilter:
    "Command to create CompoundFilter feature"
    def GetResources(self):
        return {'Pixmap'  : getIconPath("Lattice_CompoundFilter.svg"),
                'MenuText': QtCore.QT_TRANSLATE_NOOP("Lattice_CompoundFilter","Compound Filter"),
                'Accel': "",
                'ToolTip': QtCore.QT_TRANSLATE_NOOP("Lattice_CompoundFilter","Compound Filter: remove some childs from a compound")}
        
    def Activated(self):
        if len(FreeCADGui.Selection.getSelection()) == 1 or len(FreeCADGui.Selection.getSelection()) == 2 :
            CreateCompoundFilter(name = "CompoundFilter")
        else:
            mb = QtGui.QMessageBox()
            mb.setIcon(mb.Icon.Warning)
            mb.setText(translate("Lattice_CompoundFilter", "Select a shape that is a compound, first! Second selected item (optional) will be treated as a stencil.", None))
            mb.setWindowTitle(translate("Lattice_CompoundFilter","Bad selection", None))
            mb.exec_()
            
    def IsActive(self):
        if FreeCAD.ActiveDocument:
            return True
        else:
            return False
            
FreeCADGui.addCommand('Lattice_CompoundFilter', _CommandCompoundFilter())

class _CommandExplode:
    "Command to explode compound with parametric links to its children"
    def GetResources(self):
        return {'Pixmap'  : getIconPath("Lattice_Explode.svg"),
                'MenuText': QtCore.QT_TRANSLATE_NOOP("Lattice_CompoundFilter","Explode compound"),
                'Accel': "",
                'ToolTip': QtCore.QT_TRANSLATE_NOOP("Lattice_CompoundFilter","Explode compound: each member of compound as a separate object")}
        
    def Activated(self):
        if len(FreeCADGui.Selection.getSelection()) == 1 :
            FreeCAD.ActiveDocument.openTransaction("Explode")
            
            try:
                obj = FreeCADGui.Selection.getSelection()[0]
                sh = obj.Shape
                obj.ViewObject.hide()
                for i in range(0, len(sh.childShapes(False,False))):
                    cf = makeCompoundFilter(name = 'child')
                    cf.Label = u'Child' + unicode(i)
                    cf.Base = obj
                    cf.FilterType = 'specific items'
                    cf.items = str(i)
                    cf.ViewObject.DontUnhideOnDelete = True
                FreeCAD.ActiveDocument.recompute()
            except Exception:
                FreeCAD.ActiveDocument.abortTransaction()
                raise
                
            FreeCAD.ActiveDocument.commitTransaction()

        else:
            mb = QtGui.QMessageBox()
            mb.setIcon(mb.Icon.Warning)
            mb.setText(translate("Lattice_CompoundFilter", "Select a shape that is a compound, first!", None))
            mb.setWindowTitle(translate("Lattice_CompoundFilter","Bad selection", None))
            mb.exec_()
            
    def IsActive(self):
        if FreeCAD.ActiveDocument:
            return True
        else:
            return False
            
FreeCADGui.addCommand('Lattice_Explode', _CommandExplode())

exportedCommands = ['Lattice_CompoundFilter', 'Lattice_Explode']

# -------------------------- /Gui command --------------------------------------------------
