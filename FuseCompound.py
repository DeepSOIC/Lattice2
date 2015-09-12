import FreeCAD, Part

if FreeCAD.GuiUp:
    import FreeCADGui
    from PySide import QtCore, QtGui

__title__="FuseCompound module for FreeCAD"
__author__ = "DeepSOIC"
__url__ = ""

#-------------------------- translation-related code ----------------------------------------
#Thanks, yorik! (see forum thread "A new Part tool is being born... JoinFeatures!"
#http://forum.freecadweb.org/viewtopic.php?f=22&t=11112&start=30#p90239 )
try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s
try:
    _encoding = QtGui.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)
#--------------------------/translation-related code ----------------------------------------


# -------------------------- common stuff --------------------------------------------------
def getParamRefine():
    return FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/Part/Boolean").GetBool("RefineModel")

def makeFuseCompound(name):
    '''makeFuseCompound(name): makes a FuseCompound object.'''
    obj = FreeCAD.ActiveDocument.addObject("Part::FeaturePython",name)
    _FuseCompound(obj)
    obj.Refine = getParamRefine()
    _ViewProviderFuseCompound(obj.ViewObject)
    return obj

class _FuseCompound:
    "The FuseCompound object"
    def __init__(self,obj):
        self.Type = "FuseCompound"
        obj.addProperty("App::PropertyLink","Base","FuseCompound","Compound with self-intersections to be fused")
        obj.addProperty("App::PropertyBool","Refine","FuseCompound","True = refine resulting shape. False = output as is.")
        obj.addProperty("App::PropertyInteger","recomputeQuota","FuseCompound","recompute limiter. Will decrease by one each time it recomputes. Setting to zero disables recomputes. Setting negative makes recomputes unlimited.")
        obj.recomputeQuota = -1
        obj.Proxy = self
        

    def execute(self,obj):
        rst = None
        shps = obj.Base.Shape.childShapes()
        if len(shps) > 1:
            rst = shps[0].multiFuse(shps[1:])
            if obj.Refine:
                rst = rst.removeSplitter()
            obj.Shape = rst
        else:
            obj.Shape = shps[0]
        return
        
        
class _ViewProviderFuseCompound:
    "A View Provider for the FuseCompound object"

    def __init__(self,vobj):
        vobj.Proxy = self
       
    def getIcon(self):
        return getIconPath("Lattice_FuseCompound.svg")

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

def CreateFuseCompound(name):
    FreeCAD.ActiveDocument.openTransaction("Create FuseCompound")
    FreeCADGui.addModule("FuseCompound")
    FreeCADGui.doCommand("f = FuseCompound.makeFuseCompound(name = '"+name+"')")
    FreeCADGui.doCommand("f.Base = FreeCADGui.Selection.getSelection()[0]")
    FreeCADGui.doCommand("f.Proxy.execute(f)")
    FreeCADGui.doCommand("f.purgeTouched()")
    FreeCADGui.doCommand("f.Base.ViewObject.hide()")
    FreeCADGui.doCommand("f = None")
    FreeCAD.ActiveDocument.commitTransaction()

def getIconPath(icon_dot_svg):
    return ":/icons/" + icon_dot_svg

# -------------------------- /common stuff --------------------------------------------------

# -------------------------- Gui command --------------------------------------------------

class _CommandFuseCompound:
    "Command to create FuseCompound feature"
    def GetResources(self):
        return {'Pixmap'  : getIconPath("Lattice_FuseCompound.svg"),
                'MenuText': QtCore.QT_TRANSLATE_NOOP("Lattice_FuseCompound","Fuse compound"),
                'Accel': "",
                'ToolTip': QtCore.QT_TRANSLATE_NOOP("Lattice_FuseCompound","Fuse objects contained in a compound")}
        
    def Activated(self):
        if len(FreeCADGui.Selection.getSelection()) == 1 :
            CreateFuseCompound(name = "FuseCompound")
        else:
            mb = QtGui.QMessageBox()
            mb.setIcon(mb.Icon.Warning)
            mb.setText(_translate("Lattice_FuseCompound", "Select a shape that is a compound whose children intersect, first!", None))
            mb.setWindowTitle(_translate("Lattice_FuseCompound","Bad selection", None))
            mb.exec_()
            
    def IsActive(self):
        if FreeCAD.ActiveDocument:
            return True
        else:
            return False
            
FreeCADGui.addCommand('Lattice_FuseCompound', _CommandFuseCompound())

exportedCommands = ['Lattice_FuseCompound']

# -------------------------- /Gui command --------------------------------------------------
