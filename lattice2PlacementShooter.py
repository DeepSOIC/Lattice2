import FreeCAD as App
from PySide import QtCore
if App.GuiUp:
    import FreeCADGui as Gui
    from PySide import QtCore, QtGui
    Qt = QtCore.Qt
    from FreeCADGui import PySideUic as uic

from lattice2Placement import makeLatticePlacement
from lattice2Executer import executeFeature
from lattice2Common import msgError, getIconPath
from lattice2JoinArrays import makeJoinArrays

o = App.Vector() #zero vector

MODESTRINGS = ['origin', 'camera', 'surface', 'surfaceU', 'surfaceV']

def calculatePlace(selectionex, mode, view): #returns App.Placement
    sel = selectionex[0]
    pos = sel.PickedPoints[0]
    if mode == 'origin':
        return App.Placement(pos, App.Rotation())
    elif mode == 'camera':
        camrot = view.getCameraOrientation()
        return App.Placement(
            pos, 
            App.Rotation(
                -camrot.multVec(App.Vector(0,0,1)),
                o,
                camrot.multVec(App.Vector(0,1,0))
            )
        )
    elif mode in ['surface', 'surfaceU', 'surfaceV']:
        sh1 = sel.SubObjects[0] if sel.HasSubObjects else sel.Object.Shape
        #FIXME: transform sh1 to be in active coordinate system?
        import Part
        sh2 = Part.Vertex(pos)
        dist,pts,infos = sh1.distToShape(sh2)
        if len(infos)>1:
            raise ValueError("more than one solution, ambiguous point")
        pos = pts[0][0]
        ttype, index, uv, dontcare, dontcare, dontcare = infos[0]
        if ttype == 'Face':
            face = sh1.Faces[index]
            normal = face.normalAt(*uv)
            (tangU, tangV) = face.tangentAt(*uv)
        elif ttype == "Edge":
            if mode == 'surface':
                mode = 'surfaceU'
            if mode == 'surfaceV':
                raise ValueError("Edges have no v parameter")
            edge = sh1.Edges[index]
            normal = o
            tangU = edge.tangentAt(uv)
        else:
            raise ValueError("can't make it tangent to a {ttype}".format(ttype= ttype))
        
        if mode == 'surface':
            return App.Placement(pos, App.Rotation(o, o, normal))
        elif mode == 'surfaceU':
            return App.Placement(pos, App.Rotation(tangU, o, normal))
        elif mode == 'surfaceV':
            return App.Placement(pos, App.Rotation(tangV, o, normal))
    else:
        raise KeyError('calculatePlace(): mode {mode} is unsupported'.format(mode= mode))


def make(mode, container):
    plm = calculatePlace(Gui.Selection.getSelectionEx(), mode, Gui.activeView())
    plmobj = makeLatticePlacement('Dart')
    plmobj.Placement = plm
    executeFeature(plmobj)
    if container is not None:
        container.Links = container.Links + [plmobj]
    return plmobj

def modify(plmobj, mode):
    plm = calculatePlace(Gui.Selection.getSelectionEx(), mode, Gui.activeView())
    plmobj.Placement = plm
    executeFeature(plmobj)
    return plmobj

    
def startShooter():
    sel = Gui.Selection.getSelectionEx()
    container = None
    if len(sel) == 1 and hasattr(sel[0].Object, 'Type') and sel[0].Object.Type == 'lattice2JoinArrays.JoinArrays':
        container = sel[0].Object
        
    task = TaskPlacementShooter()
    task.openTask(container)
    return task

class TaskPlacementShooter(object):
    form = None # task widget
    modeRadios = None #list of tuples (radioButton, modestring)
    doc = None
    container = None
    activePlacement = None
    
    # init and stuff
    
    def __init__(self):
        import os
        self.form=uic.loadUi(os.path.dirname(__file__) + '/ui/TaskPlacementShooter.ui')
        self.form.setWindowTitle("Placement Shooter")
        self.modeRadios = [
            (self.form.oriOrigin,  'origin' ),
            (self.form.oriCamera,  'camera' ),
            (self.form.oriSurface, 'surface'),
            (self.form.oriSurfaceU, 'surfaceU'),
            (self.form.oriSurfaceV, 'surfaceV'),
        ]
        QtCore.QObject.connect(self.form.btnUnedit, QtCore.SIGNAL('clicked()'), self.uneditButtonClicked)

    def openTask(self, container = None):
        self.doc = App.ActiveDocument if container is None else container.Document

        self.doc.openTransaction("Placement Shooter")

        self.container = container        
        if self.container is None:
            self.container = makeJoinArrays('ShotArray')
    
        self.updateMessage()

        self.visibilityAutomationBegin()

        Gui.Control.closeDialog() #just in case something else was being shown
        Gui.Control.showDialog(self)
        Gui.Selection.clearSelection()
        Gui.Selection.addObserver(self)
    
    # task dialog callbacks
    
    def getStandardButtons(self):
        return int(QtGui.QDialogButtonBox.Ok) | int(QtGui.QDialogButtonBox.Cancel)

    def cleanUp(self):
        Gui.Selection.removeObserver(self)

    def clicked(self,button):
        pass

    def accept(self):
        if self.container:
            if len(self.container.Links) == 0:
                return reject()
        self.doc.commitTransaction()
        self.cleanUp()
        Gui.Control.closeDialog()
        self.visibilityAutomationEnd()
        App.ActiveDocument.recompute()

    def reject(self):
        self.doc.abortTransaction()
        self.cleanUp()
        Gui.Control.closeDialog()
        self.visibilityAutomationEnd()

    #selection observer callback
    
    def addSelection(self,docname,objname,subname,pnt):
        if not Gui.Control.activeDialog(): #the dialog was closed without us noticing?
            self.cleanUp()
            return
        if App.ActiveDocument is not self.doc:
            return

        sel = Gui.Selection.getSelectionEx()
        if len(sel) != 1:
            return
        
        sel = sel[0]
        if self.container is not None and sel.Object in self.container.Links:
            self.activePlacement = sel.Object
            self.showError(None)
        else:
            try:
                if len(sel.PickedPoints) != 1:
                    return
                
                if self.activePlacement is None:
                    make(self.getMode(), self.container)
                else:
                    modify(self.activePlacement, self.getMode())
                
                Gui.Selection.clearSelection()
                
                self.showError(None)
                self.activePlacement = None
                
            except Exception as err:
                self.showError(err)
        
        self.updateMessage()
        
    # slots
    
    def uneditButtonClicked(self):
        self.activePlacement = None
        self.updateMessage()
    
    # helpers
    
    def updateMessage(self):
        if self.activePlacement is None:
            self.form.message.setText("adding placements to '{container}'".format(container= self.container.Label if self.container is not None else self.doc.Label))
            self.form.btnUnedit.hide()
        else:
            self.form.message.setText("modifying '{placement}'".format(placement= self.activePlacement.Label))
            self.form.btnUnedit.show()
    
    def showError(self, err):
        if err is None:
            errmsg = '<html><head/><body><p><span style=" color:#00af00;">ok</span></p></body></html>'
        else:
            errmsg = '<html><head/><body><p><span style=" color:#ff0000;">{err}</span></p></body></html>'.format(err= str(err))
        self.form.status.setText(errmsg)
    
    def getMode(self):
        for radio, modestring in self.modeRadios:
            if radio.isChecked():
                return modestring
        return '??'
        
    def visibilityAutomationBegin(self):
        if self.container is not None:
            self.container.ViewObject.Visibility = False
            for child in self.container.Links:
                child.Visibility = True
    
    def visibilityAutomationEnd(self):
        if self.container is not None:
            try:
                self.container.ViewObject.Visibility = True
                for child in self.container.Links:
                    child.Visibility = False
            except ReferenceError:
                # deleted, happens if new array creation is canceled
                pass



class CommandPlacementShooter:
    def GetResources(self):
        return {'Pixmap'  : getIconPath("Lattice2_PlacementShooter.svg"),
                'MenuText': "Placement shooter...",
                'Accel': "",
                'ToolTip': "Placement Shooter: interactively create placements by clicking surfaces of objects."}
        
    def Activated(self):
        startShooter()
            
    def IsActive(self):
        if App.ActiveDocument:
            return True
        else:
            return False
            
if App.GuiUp:
    Gui.addCommand('Lattice2_PlacementShooter', CommandPlacementShooter())

exportedCommands = ['Lattice2_PlacementShooter']
