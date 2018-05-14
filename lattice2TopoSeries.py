#***************************************************************************
#*                                                                         *
#*   Copyright (c) 2017 - Victor Titov (DeepSOIC)                          *
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

__title__="Lattice TopoSeries feature"
__author__ = "DeepSOIC"
__url__ = ""
__doc__ = "Lattice TopoSeries feature: generates series of shapes by subsequencing sublinks"

import math

import FreeCAD as App
import Part

from lattice2Common import *
import lattice2BaseFeature
import lattice2Executer as Executer
import lattice2Markers as markers
import lattice2Subsequencer as Subsequencer

# --------------------------- general routines ------------------------------------------------

def findAllLinksTo(doc_obj, exclude = []):
    """findAllLinksTo(doc_obj): finds all link properties pointing to supplied object. 
    Returns them as list of tuples (dependent_object_name, property_name). Does not include 
    expression links."""
    ret = []
    doc = doc_obj.Document
    for obj in set(doc_obj.InList): # InList sometimes reports same object multiple times. Wrapping with set() removes the duplicates. 
        if obj in exclude:
            continue
        for prop_name in obj.PropertiesList:
            typ = obj.getTypeIdOfProperty(prop_name)
            if typ == 'App::PropertyLink':
                if readProperty(doc, obj.Name, prop_name) is doc_obj:
                    ret.append((obj.Name, prop_name))
            elif typ == 'App::PropertyLinkList':
                if doc_obj in readProperty(doc, obj.Name, prop_name):
                    ret.append((obj.Name, prop_name))
            elif typ == 'App::PropertyLinkSub':
                val = readProperty(doc, obj.Name, prop_name)
                if val is not None   and   doc_obj is val[0]:
                    ret.append((obj.Name, prop_name))
            elif typ == 'App::PropertyLinkSubList':
                if doc_obj in [tup[0] for tup in readProperty(doc, obj.Name, prop_name)]:
                    ret.append((obj.Name, prop_name))
    return ret
    
def readProperty(doc, object_name, property_name):
    return getattr(doc.getObject(object_name), property_name)

def writeProperty(doc, object_name, property_name, value):
    setattr(doc.getObject(object_name), property_name, value)

# -------------------------- document object --------------------------------------------------

def makeLatticeTopoSeries(name):
    '''makeLatticeTopoSeries(name): makes a LatticeTopoSeries object.'''
    return lattice2BaseFeature.makeLatticeFeature(name, LatticeTopoSeries, ViewProviderLatticeTopoSeries)

class LatticeTopoSeries(lattice2BaseFeature.LatticeFeature):
    "The Lattice TopoSeries object"
    
    def derivedInit(self,obj):
        self.Type = "LatticeTopoSeries"
                
        obj.addProperty("App::PropertyLink","ObjectToTake","Lattice TopoSeries","Object to collect permutations of. Can be any generic shape, as well as an array of placements.")
        obj.addProperty("App::PropertyLink","ObjectToLoopOver","Lattice TopoSeries","Array object to subsequence sublinks to.")
                
        obj.addProperty("App::PropertyEnumeration", "CycleMode", "Lattice TopoSeries", "Sets how to treat the ObjectToLoopOver")
        obj.CycleMode = ["Open", "Periodic"]
                
        obj.addProperty("App::PropertyEnumeration","Recomputing","Lattice TopoSeries","Sets recomputing policy.")
        obj.Recomputing = ["Disabled", "Recompute Once", "Enabled"]
        obj.Recomputing = "Disabled" # recomputing TopoSeries can be very long, so disable it by default
        
    def makeSubsequence(self, selfobj, object_to_loop):
        
        # gather up the links
        links = findAllLinksTo(object_to_loop, exclude= [selfobj])
        if self.isVerbose():
            print ("All links to {feature}:\n    {links}"
                   .format(feature= object_to_loop.Document.Name+"."+object_to_loop.Name,
                           links= "\n    ".join([link[0]+"."+link[1] for link in links])      )    )
        
        # subsequencing
        # prepare dict of link values
        linkdict = {} #key is tuple (object_name, property_name). Value is the value of property.
        for link in links:
            link_val = readProperty(object_to_loop.Document, link[0], link[1])
            linkdict[link] = link_val
        # do the subsequencing
        ret = Subsequencer.Subsequence_LinkDict(
                                  linkdict, 
                                  loop= ('Till end' if selfobj.CycleMode == 'Open' else 'All around'), 
                                  object_filter= [object_to_loop]                             )
        if self.isVerbose():
            print ("Subsequence made. Length: {n_seq}".format(n_seq= ret[0]))
            print ("Links subsequenced: \n    {links}"
                   .format(links= "\n    ".join([link[0]+"."+link[1] for link in ret[1].keys()]))   )
        return ret

    
    def isVerbose(self):
        return True
    
    def derivedExecute(self,selfobj):
        
        if selfobj.Recomputing == "Disabled":
            raise ValueError(selfobj.Name+": recomputing of this object is currently disabled. Modify 'Recomputing' property to enable it.")
        try:            

            # do the subsequencing in this document first, to verify stuff is set up correctly, and to obtain sequence length
            if self.isVerbose():
                print ("In-place pre-subsequencing, for early check")
            n_seq, subs_linkdict = self.makeSubsequence(selfobj, screen(selfobj.ObjectToLoopOver))
            
            
            bGui = bool(App.GuiUp) and Executer.globalIsCreatingLatticeFeature #disabled for most recomputes, because it causes a crash if property edits are approved by hitting Enter
            if bGui:
                import PySide
                progress = PySide.QtGui.QProgressDialog(u"Recomputing "+selfobj.Label, u"Abort", 0, n_seq+1)
                progress.setModal(True)
                progress.show()
            
            doc1 = selfobj.Document
            doc2 = App.newDocument()
            object_to_take_in_doc2 = None # define the variable, to prevent del() in finally block from raising another error
            object_to_loop_in_doc2 = None
            try:
                if self.isVerbose():
                    print ("Copying object with dependencies to a temporary document...")

                doc2.copyObject(screen(selfobj.ObjectToTake), True)
                
                if self.isVerbose():
                    print ("Enabling nested para/toposeries, if any...")
                #if there are nested para/toposeries in the dependencies, make sure to enable them
                for objd2 in doc2.Objects:
                    if hasattr(objd2,"Recomputing"):
                        try:
                            objd2.Recomputing = "Enabled"
                            objd2.purgeTouched()
                        except exception:
                            Executer.warning(selfobj,"Failed to enable recomputing of "+objd2.Name)
                
                object_to_take_in_doc2 = doc2.getObject(screen(selfobj.ObjectToTake).Name)
                object_to_loop_in_doc2 = doc2.getObject(screen(selfobj.ObjectToLoopOver).Name)
                if bGui:
                    progress.setValue(1)
                    
                if self.isVerbose():
                    print ("Repeating subsequencing in temporary document...")
                n_seq, subs_linkdict = self.makeSubsequence(selfobj, object_to_loop_in_doc2)                
                
                output_shapes = []
                for i in range(n_seq):
                    if self.isVerbose():
                        print ("Computing {x}/{y}".format(x= i+1, y= n_seq))

                    for key in subs_linkdict:
                        writeProperty(doc2, key[0], key[1], subs_linkdict[key][i])
                    
                    #recompute
                    doc2.recompute()
                    
                    #get shape
                    shape = None
                    for obj in doc2.Objects:
                        if 'Invalid' in obj.State:
                            Executer.error(obj,"Recomputing shape for subsequence index "+repr(i)+" failed.")
                            
                            scale = 1.0
                            try:
                                if not screen(selfobj.ObjectToTake).Shape.isNull():
                                    scale = screen(selfobj.ObjectToTake).Shape.BoundBox.DiagonalLength/math.sqrt(3)
                            except Exception:
                                pass
                            if scale < DistConfusion * 100:
                                scale = 1.0
                            shape = markers.getNullShapeShape(scale)
                    if shape is None:
                        shape = object_to_take_in_doc2.Shape.copy()
                    output_shapes.append(shape)
                    
                    #update progress
                    if bGui:
                        progress.setValue(progress.value()+1)
                        if progress.wasCanceled():
                            raise Executer.CancelError()
                    
            finally:
                #delete all references, before destroying the document. Probably not required, but to be sure...
                if self.isVerbose():
                    print ("Cleanup...")

                del(object_to_take_in_doc2)
                del(object_to_loop_in_doc2)
                doc2_name = doc2.Name
                del(doc2)
                App.closeDocument(doc2_name)
                if bGui:
                    progress.setValue(n_seq+1)

                
            selfobj.Shape = Part.makeCompound(output_shapes)

            output_is_lattice = lattice2BaseFeature.isObjectLattice(screen(selfobj.ObjectToTake))
            if 'Auto' in selfobj.isLattice:
                new_isLattice = 'Auto-On' if output_is_lattice else 'Auto-Off'
                if selfobj.isLattice != new_isLattice:#check, to not cause onChanged without necessity (onChange messes with colors, it's better to keep user color)
                    selfobj.isLattice = new_isLattice                    
        finally:
            if selfobj.Recomputing == "Recompute Once":
                selfobj.Recomputing = "Disabled"
        return "suppress" # "suppress" disables most convenience code of lattice2BaseFeature. We do it because we build a nested array, which are not yet supported by lattice WB.

class ViewProviderLatticeTopoSeries(lattice2BaseFeature.ViewProviderLatticeFeature):

    def getIcon(self):
        return getIconPath("Lattice2_TopoSeries.svg")  
        
    def claimChildren(self):
        return [screen(self.Object.ObjectToTake)]

# -------------------------- /document object --------------------------------------------------

# -------------------------- Gui command --------------------------------------------------



def CreateLatticeTopoSeries(name, shapeObj, loopObj):
    FreeCADGui.addModule("lattice2TopoSeries")
    FreeCADGui.addModule("lattice2Executer")
    
    #fill in properties
    FreeCADGui.doCommand("f = lattice2TopoSeries.makeLatticeTopoSeries(name='"+name+"')")
    FreeCADGui.doCommand("f.ObjectToTake = App.ActiveDocument."+shapeObj.Name)
    FreeCADGui.doCommand("f.ObjectToLoopOver = App.ActiveDocument."+loopObj.Name)
    
    #execute
    FreeCADGui.doCommand("f.Recomputing = 'Recompute Once'")
    FreeCADGui.doCommand("lattice2Executer.executeFeature(f)")
    
    #hide something
    FreeCADGui.doCommand("f.ObjectToTake.ViewObject.hide()")
        
    #finalize
    FreeCADGui.doCommand("Gui.Selection.addSelection(f)")
    FreeCADGui.doCommand("f = None")

def cmdCreateSeries():
    sel = FreeCADGui.Selection.getSelectionEx()
    if len(sel) == 2 :
        doc = FreeCAD.ActiveDocument #remember it! Recomputing TopoSeries messes up ActiveDocument, so committing transaction is screwed up...
        if sel[1].Object.Shape.ShapeType != "Compound":
            raise SelectionError("Bad selection", "Second selected object ({label}) should be an array of shapes (a compound). It is not.".format(label= sel[1].Object.Label))
        doc.openTransaction("TopoSeries")
        CreateLatticeTopoSeries("TopoSeries",sel[0].Object, sel[1].Object)
        deselect(sel)
        doc.commitTransaction()
    else:
        raise SelectionError("Bad selection","Please select two objects, first. First one is the result shape to collect variation of. Second one is an array to loop over.")

class _CommandLatticeTopoSeries:
    "Command to create LatticeTopoSeries feature"
    def GetResources(self):
        return {'Pixmap'  : getIconPath("Lattice2_TopoSeries.svg"),
                'MenuText': QtCore.QT_TRANSLATE_NOOP("Lattice2_TopoSeries","TopoSeries"),
                'Accel': "",
                'ToolTip': QtCore.QT_TRANSLATE_NOOP("Lattice2_TopoSeries","TopoSeries: generate an array of shapes by subsequencing (looping subelement links across an array).")}
        
    def Activated(self):
        try:
            if len(FreeCADGui.Selection.getSelection())==0:
                infoMessage("TopoSeries",
                    "TopoSeries command. Generates an array of shapes by subsequencing links in dependencies (looping subelement links across an array).\n\n"+
                    "Please select an object to generate array from, and an array object to loop over (order of selection matters!). Then invoke the command.\n\n"+
                    "TopoSeries will find all objects that link to the array object, and if a link is a link to subelement (e.g., to Edge1), it will advance it to the corresponding subelements of next array child. Then recompute the result shape and output it as a child. So on until any link goes out of bounds (or it will go around, if 'CycleMode' property is set to `Periodic`)."
                    )
                return
            cmdCreateSeries()
        except Exception as err:
            msgError(err)
            
    def IsActive(self):
        if FreeCAD.ActiveDocument:
            return True
        else:
            return False
            
if FreeCAD.GuiUp:
    FreeCADGui.addCommand('Lattice2_TopoSeries', _CommandLatticeTopoSeries())

exportedCommands = ['Lattice2_TopoSeries']
