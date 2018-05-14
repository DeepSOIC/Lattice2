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

__title__="Lattice Recompute Locker: hack to manual recompute of documents."
__author__ = "DeepSOIC"
__url__ = ""

import FreeCAD as App

from lattice2Common import *
import lattice2Executer as LE

def touch(obj):
    '''some bastard object like Fusion ignore calls to touch() method. This shuold work around that problem.'''
    obj.touch()
    if hasattr(obj,"Proxy"):
        #fixes mystery crash when touching recomputeLocker when it's locked
        return
        
    # the workaround is to reassign some properties...
    for propname in obj.PropertiesList:
        typ = obj.getTypeIdOfProperty(propname)
        val = getattr(obj,propname)
        if typ == 'App::PropertyLink': 
            setattr(obj,propname,val)
        elif typ == 'App::PropertyLinkSub': 
            #val is (feature,["Edge1","Face2"])
            setattr(obj,propname,val)
        elif typ == 'App::PropertyLinkList':
            setattr(obj,propname,val)
        #elif typ == 'App::PropertyLinkSubList': #disabled due to FreeCAD bug #2602
        #    setattr(obj,propname,val)

def touchEverything(doc):
    touch_count = 0
    for obj in doc.Objects:
        try:
            touch(obj)
            touch_count += 1
        except:
            App.Console.PrintError('Failed to touch object {objname}\n'
                                   .format(objname= obj.Name)   )
    if touch_count == 0:
        raise ValueError("forceRecompute: failed to touch any object!")

def recomputeFeature(featureToRecompute, bUndoable = True):
    doc = featureToRecompute.Document
    if bUndoable:
        doc.openTransaction("Recompute "+featureToRecompute.Name)
    if hasattr(featureToRecompute, 'Recomputing'):
        if featureToRecompute.Recomputing == 'Disabled': #toposeries, paraseries...
            featureToRecompute.Recomputing = 'Recompute Once'
    if hasattr(featureToRecompute, "recompute"):
        # new FreeCAD! yay!
        featureToRecompute.recompute()
    elif hasattr(featureToRecompute, "Proxy"):
        #Python feature - easy!
        featureToRecompute.Proxy.execute(featureToRecompute)
    else:
        infoMessage("RecomputeFeature","Selected feature is a C++ feature. Recomputing them with this command was temporarily disabled, because it is known to break dependencies. The command will be frozen, till a reliable way of recomputing c++ feature gets exposed.")
        return
    featureToRecompute.purgeTouched()
    for docobj in featureToRecompute.InList:
        touch(docobj)
    if bUndoable:
        doc.commitTransaction()

def makeRecomputeLocker(name):
    '''makeRecomputeLocker(name): makes a RecomputeLocker document object.'''
    obj = FreeCAD.ActiveDocument.addObject("App::FeaturePython",name)
    LatticeRecomputeLocker(obj)
    ViewProviderLatticeRecomputeLocker(obj.ViewObject)
    return obj

class LatticeRecomputeLocker:
    "The LatticeRecomputeLocker object. Mainly used as a mean to stop FreeCAD's automatic recomputes."
    def __init__(self,obj):
        self.Type = "LatticeRecomputeLocker"
        
        obj.addProperty("App::PropertyLink","LinkToSelf","Lattice RecomputeLocker","Link to self, that breaks the DAG, which causes standard FreeCAD recomputes to fail.")
        
        obj.addProperty("App::PropertyBool","LockRecomputes","Lattice RecomputeLocker", "Set to true to disable automatic recomputes in FreeCAD")
        
        obj.Proxy = self
        
    def onChanged(self, obj, prop): #prop is a string - name of the property
        if prop == "LockRecomputes":
            if obj.LockRecomputes:
                obj.LinkToSelf = obj
            else:
                obj.LinkToSelf = None
                
    def execute(self, obj):
        pass
        
    def RecomputeDocument(self, obj, bUndoable = True):
        oldState = obj.LockRecomputes
        obj.LockRecomputes = False
        doc = obj.Document
        if bUndoable:
            doc.openTransaction("Recompute document")
        doc.recompute()
        if bUndoable:
            doc.commitTransaction()
        obj.LockRecomputes = oldState
                    
    def collectTouchedDict(self, selfobj):
        doc = selfobj.Document
        dict = {}
        for docobj in doc.Objects:
            dict[docobj.Name] = 'Touched' in docobj.State
        return dict
            
    def restoreTouched(self, selfobj, dict):
        doc = selfobj.Document
        for docobj in doc.Objects:
            if dict[docobj.Name] != ('Touched' in docobj.State):
                if dict[docobj.Name] == True:
                    touch(docobj)
                else:
                    docobj.purgeTouched()
                    
    
class ViewProviderLatticeRecomputeLocker:
    "A View Provider for LatticeRecomputeLocker object"

    def __init__(self,vobj):
        vobj.Proxy = self
        
    def getIcon(self):
        if self.Object.LockRecomputes:
            return getIconPath("Lattice2_RecomputeLocker_Locked.svg")
        else:
            return getIconPath("Lattice2_RecomputeLocker_Unlocked.svg")

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

# --------------------------------/document object------------------------------



# --------------------------------Gui commands----------------------------------

def getLocker():
    if hasattr(App.ActiveDocument,"LatticeRecomputeLocker"):
        return App.ActiveDocument.LatticeRecomputeLocker
    else:
        return None

class _CommandMakeLockerObj:
    "Command to create RecomputeLocker feature"
    def GetResources(self):
        return {'Pixmap'  : getIconPath("Lattice2_RecomputeLocker_MakeFeature.svg"),
                'MenuText': QtCore.QT_TRANSLATE_NOOP("Lattice2_RecomputeLocker","Make recompute locker object"),
                'Accel': "",
                'ToolTip': QtCore.QT_TRANSLATE_NOOP("Lattice2_RecomputeLocker","Make recompute locker object. Doing this is necessary to enable recompute locking hacktionality."),
                'CmdType':"ForEdit"}
        
    def Activated(self):
        if getLocker() is None:
            FreeCADGui.addModule("lattice2RecomputeLocker")
            FreeCADGui.doCommand("lattice2RecomputeLocker.makeRecomputeLocker('LatticeRecomputeLocker')")
            FreeCADGui.doCommand("App.ActiveDocument.LatticeRecomputeLocker.purgeTouched()")
        else:
            mb = QtGui.QMessageBox()
            mb.setIcon(mb.Icon.Warning)
            mb.setText(translate("Lattice2_RecomputeLocker", "A recompute locker object already exists in this document. Only one such object can be made.", None))
            mb.setWindowTitle(translate("Lattice2_RecomputeLocker","Nothing to do", None))
            mb.exec_()
            
    def IsActive(self):
        if not App.ActiveDocument: return False
        if hasattr(App.ActiveDocument,'RecomputesFrozen'):
            return False # new FreeCAD, with proper recompute disablement. Disable the hack.
        else:
            return (bool(App.ActiveDocument) and getLocker() is None)
            
if FreeCAD.GuiUp:
    FreeCADGui.addCommand('Lattice2_RecomputeLocker_MakeFeature', _CommandMakeLockerObj())

class _CommandLockRecomputes:
    "Command to lock automatic recomputes"
    def GetResources(self):
        return {'Pixmap'  : getIconPath("Lattice2_RecomputeLocker_LockRecomputes.svg"),
                'MenuText': QtCore.QT_TRANSLATE_NOOP("Lattice2_RecomputeLocker","Lock recomputes"),
                'Accel': "",
                'ToolTip': QtCore.QT_TRANSLATE_NOOP("Lattice2_RecomputeLocker","Lock recomputes: prevent FreeCAD's automatic recomputes."),
                'CmdType':"ForEdit"}
        
    def Activated(self):
        if hasattr(App.ActiveDocument,'RecomputesFrozen'):
            FreeCADGui.doCommand("App.ActiveDocument.RecomputesFrozen = True")
        elif getLocker() is not None:
            FreeCADGui.addModule("lattice2RecomputeLocker")
            FreeCADGui.doCommand("lattice2RecomputeLocker.getLocker().LockRecomputes = True")
            FreeCADGui.doCommand("lattice2RecomputeLocker.getLocker().touch()") #gets rid of the tick, plus updates the icon.
        else:
            mb = QtGui.QMessageBox()
            mb.setIcon(mb.Icon.Warning)
            mb.setText(translate("Lattice2_RecomputeLocker", "There is no recompute locker object in the document. Please create one, first.", None))
            mb.setWindowTitle(translate("Lattice2_RecomputeLocker","fail", None))
            mb.exec_()
            
    def IsActive(self):
        if not App.ActiveDocument: return False
        if hasattr(App.ActiveDocument,'RecomputesFrozen'):
            return App.ActiveDocument.RecomputesFrozen == False 
        else:
            return getLocker() is not None and not getLocker().LockRecomputes
            
if FreeCAD.GuiUp:
    FreeCADGui.addCommand('Lattice2_RecomputeLocker_LockRecomputes', _CommandLockRecomputes())

class _CommandUnlockRecomputes:
    "Command to unlock automatic recomputes"
    def GetResources(self):
        return {'Pixmap'  : getIconPath("Lattice2_RecomputeLocker_UnlockRecomputes.svg"),
                'MenuText': QtCore.QT_TRANSLATE_NOOP("Lattice2_RecomputeLocker","Unlock recomputes"),
                'Accel': "",
                'ToolTip': QtCore.QT_TRANSLATE_NOOP("Lattice2_RecomputeLocker","Unlock recomputes: switch on FreeCAD's automatic recomputes."),
                'CmdType':"ForEdit"}
        
    def Activated(self):
        if hasattr(App.ActiveDocument,'RecomputesFrozen'):
            FreeCADGui.doCommand("App.ActiveDocument.RecomputesFrozen = False")
        elif getLocker() is not None:
            FreeCADGui.addModule("lattice2RecomputeLocker")
            FreeCADGui.doCommand("lattice2RecomputeLocker.getLocker().LockRecomputes = False")
            FreeCADGui.doCommand("lattice2RecomputeLocker.getLocker().purgeTouched()") #gets rid of the tick, plus updates the icon.
        else:
            mb = QtGui.QMessageBox()
            mb.setIcon(mb.Icon.Warning)
            mb.setText(translate("Lattice2_RecomputeLocker", "There is no recompute locker object in the document. Please create one, first.", None))
            mb.setWindowTitle(translate("Lattice2_RecomputeLocker","fail", None))
            mb.exec_()
            
    def IsActive(self):
        if not App.ActiveDocument: return False
        if hasattr(App.ActiveDocument,'RecomputesFrozen'):
            return App.ActiveDocument.RecomputesFrozen == True 
        else:
            return getLocker() is not None and getLocker().LockRecomputes
            
if FreeCAD.GuiUp:
    FreeCADGui.addCommand('Lattice2_RecomputeLocker_UnlockRecomputes', _CommandUnlockRecomputes())

class _CommandRecomputeFeature:
    "Command to recompute single object"
    def GetResources(self):
        return {'Pixmap'  : getIconPath("Lattice2_RecomputeLocker_RecomputeFeature.svg"),
                'MenuText': QtCore.QT_TRANSLATE_NOOP("Lattice2_RecomputeLocker","Recompute feature"),
                'Accel': "",
                'ToolTip': QtCore.QT_TRANSLATE_NOOP("Lattice2_RecomputeLocker","RecomputeFeature: recompute selected objects."),
                'CmdType':"ForEdit"}
        
    def Activated(self):
        sel = FreeCADGui.Selection.getSelectionEx()
        FreeCADGui.addModule("lattice2RecomputeLocker")
        for selobj in sel:
            FreeCADGui.doCommand("lattice2RecomputeLocker.recomputeFeature(App.ActiveDocument."+selobj.ObjectName+")")
            
    def IsActive(self):
        return len(FreeCADGui.Selection.getSelectionEx()) > 0
            
if FreeCAD.GuiUp:
    FreeCADGui.addCommand('Lattice2_RecomputeLocker_RecomputeFeature', _CommandRecomputeFeature())


class _CommandRecomputeDocument:
    "Command to recompute whole document"
    def GetResources(self):
        return {'Pixmap'  : getIconPath("Lattice2_RecomputeLocker_RecomputeDocument.svg"),
                'MenuText': QtCore.QT_TRANSLATE_NOOP("Lattice2_RecomputeLocker","Recompute document"),
                'Accel': "",
                'ToolTip': QtCore.QT_TRANSLATE_NOOP("Lattice2_RecomputeLocker","Recompute document: recompute the document, ignoring that recomputes are locked."),
                'CmdType':"ForEdit"}
        
    def Activated(self):
        try:
            if hasattr(App.ActiveDocument, 'RecomputesFrozen'):
                FreeCADGui.doCommand(
                    '_lock = App.ActiveDocument.RecomputesFrozen\n'
                    'App.ActiveDocument.RecomputesFrozen = False\n'
                    'App.ActiveDocument.recompute()\n'
                    'App.ActiveDocument.RecomputesFrozen = _lock\n'
                    'del _lock\n'
                )
            else: #old FC, hacky recompute control
                if getLocker() is not None:
                    FreeCADGui.addModule("lattice2RecomputeLocker")
                    FreeCADGui.doCommand("lattice2RecomputeLocker.getLocker().Proxy.RecomputeDocument(lattice2RecomputeLocker.getLocker())")
                else:
                    FreeCADGui.doCommand("App.ActiveDocument.recompute()")
        except Exception as err:
            msgError(err)
            
    def IsActive(self):
        return App.ActiveDocument is not None
            
if FreeCAD.GuiUp:
    FreeCADGui.addCommand('Lattice2_RecomputeLocker_RecomputeDocument', _CommandRecomputeDocument())

class _CommandForceRecompute:
    "Command to force recompute of every feature"
    def GetResources(self):
        return {'Pixmap'  : getIconPath("Lattice2_RecomputeLocker_ForceRecompute.svg"),
                'MenuText': QtCore.QT_TRANSLATE_NOOP("Lattice2_RecomputeLocker","Force recompute"),
                'Accel': "Shift+F5",
                'ToolTip': QtCore.QT_TRANSLATE_NOOP("Lattice2_RecomputeLocker","Force recompute: recompute all features in the document."),
                'CmdType':"ForEdit"}
        
    def Activated(self):
        try:
            FreeCADGui.addModule("lattice2RecomputeLocker")
            FreeCADGui.doCommand("lattice2RecomputeLocker.touchEverything(App.ActiveDocument)")
            _CommandRecomputeDocument().Activated()
        except Exception as err:
            msgError(err)
            
    def IsActive(self):
        return App.ActiveDocument is not None
            
if FreeCAD.GuiUp:
    FreeCADGui.addCommand('Lattice2_RecomputeLocker_ForceRecompute', _CommandForceRecompute())


class _CommandTouch:
    "Command to touch a feature"
    def GetResources(self):
        return {'Pixmap'  : getIconPath("Lattice2_RecomputeLocker_Touch.svg"),
                'MenuText': QtCore.QT_TRANSLATE_NOOP("Lattice2_RecomputeLocker","Touch selected features"),
                'Accel': "Shift+F5",
                'ToolTip': QtCore.QT_TRANSLATE_NOOP("Lattice2_RecomputeLocker","Touch selected features: mark selected features as needing recomputing."),
                'CmdType':"ForEdit"}
        
    def Activated(self):
        FreeCADGui.addModule("lattice2RecomputeLocker")
        try:
            sel = FreeCADGui.Selection.getSelectionEx()
            if len(sel) == 0:
                infoMessage("Touch command",
                            "'Touch selected features' command. Touches selected objects. 'Touched' means the object was changed and should be recomputed; if nothing is touched, recomputing the document does nothing.\n\n"
                            "Please select objects to be marked as touched first, then invoke this command. If all selected objects are touched already, the 'Touched' state is undone (purged).")
                return
            n_touched = 0
            for so in sel:
                if 'Touched' in so.Object.State:
                    n_touched += 1
            if n_touched < len(sel):
                # not all selected objects are currently touched. Touch the remaining...
                FreeCADGui.doCommand("for so in Gui.Selection.getSelectionEx(): lattice2RecomputeLocker.touch(so.Object)")
            else:
                #all selected objects are already touched. 
                FreeCADGui.doCommand("for so in Gui.Selection.getSelectionEx(): so.Object.purgeTouched()")
                
        except Exception as err:
            msgError(err)
            
    def IsActive(self):
        return App.ActiveDocument is not None
            
if FreeCAD.GuiUp:
    FreeCADGui.addCommand('Lattice2_RecomputeLocker_Touch', _CommandTouch())

exportedCommands = [
    "Lattice2_RecomputeLocker_MakeFeature",
    "Lattice2_RecomputeLocker_LockRecomputes",
    "Lattice2_RecomputeLocker_UnlockRecomputes",
    "Lattice2_RecomputeLocker_RecomputeFeature",
    "Lattice2_RecomputeLocker_RecomputeDocument",
    "Lattice2_RecomputeLocker_ForceRecompute",
    "Lattice2_RecomputeLocker_Touch"
    ]
if int(App.Version()[1]) >= 17:
    exportedCommands.remove("Lattice2_RecomputeLocker_MakeFeature")
    
class CommandRecomputeGroup:
    def GetCommands(self):
        global exportedCommands
        return tuple(exportedCommands)

    def GetDefaultCommand(self): # return the index of the tuple of the default command. 
        return 0

    def GetResources(self):
        return { 'MenuText': 'Lattice recompute control:', 
                 'ToolTip': 'Document recompute controlling tools from Lattice2 workbench',
                 'CmdType':"ForEdit"}
        
    def IsActive(self): # optional
        return App.ActiveDocument is not None
if FreeCAD.GuiUp:
    FreeCADGui.addCommand('Lattice2_RecomputeLockerGroup', CommandRecomputeGroup())
    
    
def msgbox(strmsg):
    mb = QtGui.QMessageBox()
    mb.setIcon(mb.Icon.Warning)
    mb.setText(strmsg)
    mb.setWindowTitle("debug")
    mb.exec_()
