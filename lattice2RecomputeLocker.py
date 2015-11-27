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
        elif typ == 'App::PropertyLinkSubList':
            setattr(obj,propname,val)

    

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
        
    def RecomputeFeature(self, selfobj, featureToRecompute, bUndoable = True):
        oldState = selfobj.LockRecomputes
        doc = selfobj.Document
        if bUndoable:
            doc.openTransaction("Recompute "+featureToRecompute.Name)
        if hasattr(featureToRecompute, "Proxy"):
            #Python feature - easy!
            featureToRecompute.Proxy.execute(featureToRecompute)
            featureToRecompute.purgeTouched()
        else:
            #non-Py feature. Hard.
            #overview: FreeCAD will recompute just one feature, if it is the 
            #only one that is touched, and no other features depend on it. So 
            #that's what we are to do: untouch all other features, and remove 
            #all links. 
            #save touched flags, to restore them later
            touched_dict = self.collectTouchedDict(selfobj)
            try:
                #temporarily remove all links to the object
                unlinker = Unlinker()
                unlinker.unlinkObject(featureToRecompute)
                try:
                    #set desired document touched state
                    for docobj in doc.Objects:
                        if docobj is not featureToRecompute:
                            docobj.purgeTouched()
                        else:
                            touch(docobj)
                    try:
                        #do the business =)
                        selfobj.LockRecomputes = False
                        doc.recompute()
                        #and restore the mess we've created...
                    finally:
                        selfobj.LockRecomputes = oldState
                                            
                    
                finally:
                    unlinker.restoreLinks()
            finally:
                self.restoreTouched(selfobj,touched_dict)                    
            
            #feature recomputed - purge its touched
            featureToRecompute.purgeTouched()
            #feature should have changed, so mark all dependent stuff as touched
            for docobj in featureToRecompute.InList:
                touch(docobj)
        if bUndoable:
            doc.commitTransaction()
            
    def collectTouchedDict(self, selfobj):
        doc = selfobj.Document
        dict = {}
        for docobj in doc.Objects:
            dict[docobj.Name] = 'Touched' in docobj.State
        return dict
            
    def restoreTouched(self, selfobj, dict):
        doc = selfobj.Document
        for docobj in doc.Objects:
            if dict[docobj.Name] != 'Touched' in docobj.State:
                if dict[docobj.Name] == True:
                    touch(docobj)
                else:
                    docobj.purgeTouched()
                    
    
class Unlinker:
    '''An object to temporarily unlink an object, and to restore the links afterwards'''
    def __init__(self):
        #List of actions for restoring the links is going to be saved here. It 
        # is a list tuples: (object, 'property name', oldvalue).
        self.actionList = [] 
        
    def unlinkObject(self, featureToUnlink):
        '''Redirects all links to this object, to make it possible to recompute it individually. TODO: expressions!!'''
        doc = featureToUnlink.Document
        ListOfDependentObjects = featureToUnlink.InList #<rant> naming list of objects that are dependent on the feature as InList is bullshit. InList should have been list of inputs - that is, list of objects this feature depends on. But it's back-to-front. =<
        if len(self.actionList) > 0:
            raise ValueError("unlinker hasn't restored the changes it did previously. Can't unlink another object.")
        for obj in ListOfDependentObjects:
            for propname in obj.PropertiesList:
                try:
                    typ = obj.getTypeIdOfProperty(propname)
                    val = getattr(obj,propname)
                    bool_changed = True
                    if typ == 'App::PropertyLink':                    
                        setattr(obj,propname,None)
                    elif typ == 'App::PropertyLinkSub':
                        #val is (feature,["Edge1","Face2"])
                        setattr(obj,propname,None)
                    elif typ == 'App::PropertyLinkList':
                        setattr(obj,propname,[])
                    elif typ == 'App::PropertyLinkSubList':
                        setattr(obj,propname,[])
                    else:
                        bool_changed = False
                    
                    if bool_changed:
                        self.actionList.append((obj,propname,val))
                except Exception as err:
                    LE.error(None, "While temporarily removing all links to an object, an error occured.\n" +
                             "Error:"+err.message+"\n" +
                             "object = "+obj.Name+"\n" +
                             "property = "+propname+"\n" +
                             "value to be restored = "+repr(value))
                    
    def restoreLinks(self):
        for (obj, propname, value) in self.actionList:
            try:
                setattr(obj,propname,value)
            except Exception as err:
                LE.error(None, "An error occured while restoring links.\n" +
                         "Error:"+err.message+"\n" +
                         "object = "+obj.Name+"\n" +
                         "property = "+propname+"\n" +
                         "value to be restored = "+repr(value))
        self.actionList = []

class ViewProviderLatticeRecomputeLocker:
    "A View Provider for LatticeRecomputeLocker object"

    def __init__(self,vobj):
        vobj.Proxy = self
        
    def getIcon(self):
        return getIconPath("Lattice2_RecomputeLocker_Feature.svg")

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
                'ToolTip': QtCore.QT_TRANSLATE_NOOP("Lattice2_RecomputeLocker","Make recompute locker object. Doing this is necessary to enable recompute locking hacktionality.")}
        
    def Activated(self):
        if getLocker() is None:
            FreeCADGui.addModule("lattice2RecomputeLocker")
            FreeCADGui.doCommand("lattice2RecomputeLocker.makeRecomputeLocker('LatticeRecomputeLocker')")
        else:
            mb = QtGui.QMessageBox()
            mb.setIcon(mb.Icon.Warning)
            mb.setText(translate("Lattice2_RecomputeLocker", "A recompute locker object already exists in this document. Only one such object can be made.", None))
            mb.setWindowTitle(translate("Lattice2_RecomputeLocker","Nothing to do", None))
            mb.exec_()
            
    def IsActive(self):
        return bool(App.ActiveDocument) and getLocker() is None
            
FreeCADGui.addCommand('Lattice2_RecomputeLocker_MakeFeature', _CommandMakeLockerObj())

class _CommandLockRecomputes:
    "Command to lock automatic recomputes"
    def GetResources(self):
        return {'Pixmap'  : getIconPath("Lattice2_RecomputeLocker_LockRecomputes.svg"),
                'MenuText': QtCore.QT_TRANSLATE_NOOP("Lattice2_RecomputeLocker","Lock recomputes"),
                'Accel': "",
                'ToolTip': QtCore.QT_TRANSLATE_NOOP("Lattice2_RecomputeLocker","Lock recomputes: prevent FreeCAD's automatic recomputes from doing anything.")}
        
    def Activated(self):
        if getLocker is not None:
            FreeCADGui.addModule("lattice2RecomputeLocker")
            FreeCADGui.doCommand("lattice2RecomputeLocker.getLocker().LockRecomputes = True")
        else:
            mb = QtGui.QMessageBox()
            mb.setIcon(mb.Icon.Warning)
            mb.setText(translate("Lattice2_RecomputeLocker", "There is no recompute locker object in the document. Please create one, first.", None))
            mb.setWindowTitle(translate("Lattice2_RecomputeLocker","fail", None))
            mb.exec_()
            
    def IsActive(self):
        return getLocker() is not None
            
FreeCADGui.addCommand('Lattice2_RecomputeLocker_LockRecomputes', _CommandLockRecomputes())

class _CommandUnlockRecomputes:
    "Command to unlock automatic recomputes"
    def GetResources(self):
        return {'Pixmap'  : getIconPath("Lattice2_RecomputeLocker_UnlockRecomputes.svg"),
                'MenuText': QtCore.QT_TRANSLATE_NOOP("Lattice2_RecomputeLocker","Unlock recomputes"),
                'Accel': "",
                'ToolTip': QtCore.QT_TRANSLATE_NOOP("Lattice2_RecomputeLocker","Unlock recomputes: switch on FreeCAD's automatic recomputes.")}
        
    def Activated(self):
        if getLocker is not None:
            FreeCADGui.addModule("lattice2RecomputeLocker")
            FreeCADGui.doCommand("lattice2RecomputeLocker.getLocker().LockRecomputes = False")
        else:
            mb = QtGui.QMessageBox()
            mb.setIcon(mb.Icon.Warning)
            mb.setText(translate("Lattice2_RecomputeLocker", "There is no recompute locker object in the document. Please create one, first.", None))
            mb.setWindowTitle(translate("Lattice2_RecomputeLocker","fail", None))
            mb.exec_()
            
    def IsActive(self):
        return getLocker() is not None
            
FreeCADGui.addCommand('Lattice2_RecomputeLocker_UnlockRecomputes', _CommandUnlockRecomputes())

class _CommandRecomputeFeature:
    "Command to unlock automatic recomputes"
    def GetResources(self):
        return {'Pixmap'  : getIconPath("Lattice2_RecomputeLocker_RecomputeFeature.svg"),
                'MenuText': QtCore.QT_TRANSLATE_NOOP("Lattice2_RecomputeLocker","Recompute feature"),
                'Accel': "",
                'ToolTip': QtCore.QT_TRANSLATE_NOOP("Lattice2_RecomputeLocker","RecomputeFeature: recompute selected objects.")}
        
    def Activated(self):
        sel = FreeCADGui.Selection.getSelectionEx()
        if getLocker is not None:
            FreeCADGui.addModule("lattice2RecomputeLocker")
            for selobj in sel:
                FreeCADGui.doCommand("lattice2RecomputeLocker.getLocker().Proxy.RecomputeFeature(lattice2RecomputeLocker.getLocker(), App.ActiveDocument."+selobj.ObjectName+")")
        else:
            mb = QtGui.QMessageBox()
            mb.setIcon(mb.Icon.Warning)
            mb.setText(translate("Lattice2_RecomputeLocker", "There is no recompute locker object in the document. Please create one, first.", None))
            mb.setWindowTitle(translate("Lattice2_RecomputeLocker","fail", None))
            mb.exec_()
            
    def IsActive(self):
        return getLocker() is not None   and   len(FreeCADGui.Selection.getSelectionEx()) > 0
            
FreeCADGui.addCommand('Lattice2_RecomputeLocker_RecomputeFeature', _CommandRecomputeFeature())


class _CommandRecomputeDocument:
    "Command to recompute whole document"
    def GetResources(self):
        return {'Pixmap'  : getIconPath("Lattice2_RecomputeLocker_RecomputeDocument.svg"),
                'MenuText': QtCore.QT_TRANSLATE_NOOP("Lattice2_RecomputeLocker","Recompute document"),
                'Accel': "",
                'ToolTip': QtCore.QT_TRANSLATE_NOOP("Lattice2_RecomputeLocker","Recompute document: recompute the document, ignoring that recomputes are locked.")}
        
    def Activated(self):
        if getLocker is not None:
            FreeCADGui.addModule("lattice2RecomputeLocker")
            FreeCADGui.doCommand("lattice2RecomputeLocker.getLocker().Proxy.RecomputeDocument(lattice2RecomputeLocker.getLocker())")
        else:
            mb = QtGui.QMessageBox()
            mb.setIcon(mb.Icon.Warning)
            mb.setText(translate("Lattice2_RecomputeLocker", "There is no recompute locker object in the document. Please create one, first.", None))
            mb.setWindowTitle(translate("Lattice2_RecomputeLocker","fail", None))
            mb.exec_()
            
    def IsActive(self):
        return getLocker() is not None
            
FreeCADGui.addCommand('Lattice2_RecomputeLocker_RecomputeDocument', _CommandRecomputeDocument())


exportedCommands = [
    "Lattice2_RecomputeLocker_MakeFeature",
    "Lattice2_RecomputeLocker_LockRecomputes",
    "Lattice2_RecomputeLocker_UnlockRecomputes",
    "Lattice2_RecomputeLocker_RecomputeFeature",
    "Lattice2_RecomputeLocker_RecomputeDocument",
    ]
    
    
def msgbox(strmsg):
    mb = QtGui.QMessageBox()
    mb.setIcon(mb.Icon.Warning)
    mb.setText(strmsg)
    mb.setWindowTitle("debug")
    mb.exec_()
