from latticeCommon import *
import latticeMarkers as markers
import math

__title__="CompoundFilter module for FreeCAD"
__author__ = "DeepSOIC"
__url__ = ""



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
        obj.FilterType = ['bypass','specific items','collision-pass','window-volume','window-area']
        obj.FilterType = 'bypass'
        
        # properties controlling "specific items" mode
        obj.addProperty("App::PropertyString","items","CompoundFilter","list of indexes of childs to be returned (like this: 1,4,8-10)")

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
        rst = [] #variable to receive the final list of shapes
        shps = obj.Base.Shape.childShapes()
        if obj.FilterType == 'bypass':
            rst = shps
        elif obj.FilterType == 'specific items':
            rst = []
            flags = [False] * len(shps)
            ranges = obj.items.split(';')
            for r in ranges:
                r_v = r.split('-')
                if len(r_v) == 1:
                    i = int(r_v[0])
                    rst.append(shps[i])
                    flags[i] = True
                elif len(r_v) == 2:
                    ifrom = int(r_v[0])
                    ito = int(r_v[1])+1 #python treats range's 'to' value as not-inclusive. I want the string to list in inclusive manner.
                    rst=rst+shps[ifrom:ito]
                    for b in flags[ifrom:ito]:
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
        elif obj.FilterType == 'window-volume' or obj.FilterType == 'window-area':
            vals = [0.0] * len(shps)
            for i in xrange(0,len(shps)):
                if obj.FilterType == 'window-volume':
                    vals[i] = shps[i].Volume
                elif obj.FilterType == 'window-area':
                    vals[i] = shps[i].Area
            
            maxval = max(vals)
            if obj.Stencil:
                if obj.FilterType == 'window-volume':
                    vals[i] = obj.Stencil.Shape.Volume
                elif obj.FilterType == 'window-area':
                    vals[i] = obj.Stencil.Shape.Area
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
        
        obj.Shape = Part.makeCompound(rst)
        return
        
        
class _ViewProviderCompoundFilter:
    "A View Provider for the CompoundFilter object"

    def __init__(self,vobj):
        vobj.Proxy = self
       
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

def CreateCompoundFilter(name):
    FreeCAD.ActiveDocument.openTransaction("Create CompoundFilter")
    FreeCADGui.addModule("CompoundFilter")
    FreeCADGui.doCommand("f = CompoundFilter.makeCompoundFilter(name = '"+name+"')")
    FreeCADGui.doCommand("f.Base = FreeCADGui.Selection.getSelection()[0]")
    if len(FreeCADGui.Selection.getSelection()) == 2:
        FreeCADGui.doCommand("f.Stencil = FreeCADGui.Selection.getSelection()[1]")
        FreeCADGui.doCommand("f.FilterType = 'collision-pass'")
    else:
        FreeCADGui.doCommand("f.FilterType = 'window-volume'")    
    FreeCADGui.doCommand("f.Proxy.execute(f)")
    FreeCADGui.doCommand("f.purgeTouched()")
    FreeCADGui.doCommand("f.Base.ViewObject.hide()")
    FreeCADGui.doCommand("f = None")
    FreeCAD.ActiveDocument.commitTransaction()


# -------------------------- /common stuff --------------------------------------------------

# -------------------------- Gui command --------------------------------------------------

class _CommandCompoundFilter:
    "Command to create CompoundFilter feature"
    def GetResources(self):
        return {'Pixmap'  : getIconPath("Lattice_CompoundFilter.svg"),
                'MenuText': QtCore.QT_TRANSLATE_NOOP("Lattice_CompoundFilter","Fuse compound"),
                'Accel': "",
                'ToolTip': QtCore.QT_TRANSLATE_NOOP("Lattice_CompoundFilter","Fuse objects contained in a compound")}
        
    def Activated(self):
        if len(FreeCADGui.Selection.getSelection()) == 1 or len(FreeCADGui.Selection.getSelection()) == 2 :
            CreateCompoundFilter(name = "CompoundFilter")
        else:
            mb = QtGui.QMessageBox()
            mb.setIcon(mb.Icon.Warning)
            mb.setText(_translate("Lattice_CompoundFilter", "Select a shape that is a compound, first! Second selected item (optional) will be treated as a stencil.", None))
            mb.setWindowTitle(_translate("Lattice_CompoundFilter","Bad selection", None))
            mb.exec_()
            
    def IsActive(self):
        if FreeCAD.ActiveDocument:
            return True
        else:
            return False
            
FreeCADGui.addCommand('Lattice_CompoundFilter', _CommandCompoundFilter())

exportedCommands = ['Lattice_CompoundFilter']

# -------------------------- /Gui command --------------------------------------------------
