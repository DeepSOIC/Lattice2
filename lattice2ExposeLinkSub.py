#***************************************************************************
#*                                                                         *
#*   Copyright (c) 2016 - Victor Titov (DeepSOIC)                          *
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

__title__= "Lattice ExposeLinkSub tool for FreeCAD"
__author__ = "DeepSOIC"
__doc__ = "Tool to expose LinkSub properties of objects, by spawning a SubLink object for each sublinked element, and redirecting the links"

from lattice2Common import *
import lattice2SubLink as LSL
import lattice2Executer as Executer
import FreeCAD as App

def ExposeLinkSub(feature, propname):
    # read links out into reflist variable
    if feature.getTypeIdOfProperty(propname) == 'App::PropertyLinkSubList':
        reflist = getattr(feature,propname)
    elif feature.getTypeIdOfProperty(propname) == 'App::PropertyLinkSub':
        (obj, subnames) = getattr(feature,propname)
        reflist = [(obj,subname) for subname in subnames]
        if len(reflist)>1:
            raise ValueError("Link of type 'App::PropertyLinkSub' points to more than one subelement. Not supported yet.")
        del (obj)
    else:
        raise ValueError("Link type not supported: "+feature.getTypeIdOfProperty(propname))
    if reflist is None:
        raise ValueError("Nothing is linked, nothing to do")
        #return
        
    # make SubLinks objects, and redirect the links in reflist
    for i in range(len(reflist)):
        (obj, subname) = reflist[i]
        if "Face" in subname: 
            newsubname = "Face1"
        elif "Edge" in subname: 
            newsubname = "Edge1"
        elif "Vertex" in subname: 
            newsubname = "Vertex1"
        else: 
            App.Console.PrintLog("Link %prop of feature %feat links either to whole object, or to something unknown. Subname is %sub. Skipped.\n"
                                 .replace("%prop",propname)
                                 .replace("%feat",feature.Name)
                                 .replace("%sub",repr(subname))  )
            continue
        sublink = LSL.CreateSubLink(obj, [subname])
        reflist[i] = (sublink,newsubname)
    del obj
    
    # write back
    if feature.getTypeIdOfProperty(propname) == 'App::PropertyLinkSubList':
        setattr(feature,propname,reflist)
    elif feature.getTypeIdOfProperty(propname) == 'App::PropertyLinkSub':
        setattr(feature,propname,reflist[0])
    
def cmdExposeLinkSubs():
    sel = FreeCADGui.Selection.getSelectionEx()
    if len(sel) != 1:
        raise SelectionError(   "Bad selection", "Select one object, first! You have selected %i objects".replace("%i",str(len(sel)))   )
    App.ActiveDocument.openTransaction("Expose LinkSub of "+sel[0].Object.Name)
    obj = sel[0].Object
    cnt = 0
    try:
        for propname in obj.PropertiesList:
            if 'App::PropertyLinkSub' in obj.getTypeIdOfProperty(propname):
                if getattr(obj,propname) is None:  continue
                try:
                    if obj.isDerivedFrom("Part::Part2DObject") and propname == "Support":
                        if False == askYesNo("Support", "ExposeLinkSub is about to expose Support link of %feat. This will cause PartDesign additive operations to start new objects instead of adding to support solid, and subtractive PartDesign operations to fail. Expose the support link?"
                                                        .replace("%feat",obj.Label)):
                            continue
                    ExposeLinkSub(obj, propname)
                    cnt += 1
                except Exception as err:
                    Executer.warning(None,"Attempting to expose sublink property %prop of %feat caused an error:\n%err"
                                          .replace("%prop",propname)
                                          .replace("%feat",obj.Name)
                                          .replace("%err",err.message)   )
        if cnt == 0:
            raise ValueError("No links to expose were found.")
    except Exception:
        App.ActiveDocument.abortTransaction()
        raise
        
    
# candidate for transferring
def askYesNo(title, message):
    '''Displays messagebox with three buttons: yes, no, abort. yes -> returns True. no -> returns False. abort -> raises CancelError'''
    from PySide import QtGui
    mb = QtGui.QMessageBox()
    mb.setIcon(mb.Icon.Question)
    mb.setText(message)
    mb.setWindowTitle(title)
    btnAbort = mb.addButton(QtGui.QMessageBox.StandardButton.Abort)
    btnYes = mb.addButton(QtGui.QMessageBox.StandardButton.Yes)
    btnNo = mb.addButton(QtGui.QMessageBox.StandardButton.No)
    mb.setDefaultButton(btnYes)
    mb.exec_()
    if mb.clickedButton() is btnAbort:
        raise CancelError()
    return mb.clickedButton() is btnYes



class _CommandExposeLinkSub:
    "Command to expose ..LinkSub.. properties of other features"
    def GetResources(self):
        return {
                'MenuText': QtCore.QT_TRANSLATE_NOOP("Lattice2_ExposeLinkSub","Expose links to subelements"),
                'Accel': "",
                'ToolTip': QtCore.QT_TRANSLATE_NOOP("Lattice2_ExposeLinkSub","Expose links to subelements: create SubLink features as proxies for subelement dependencies of selected object")}
        
    def Activated(self):
        try:
            if len(FreeCADGui.Selection.getSelection())==0:
                infoMessage("ExposeLinkSub",
                    "'Expose links to subelements' command. Exposes subelement links of an object by creating SubLink features as proxies for subelement dependencies.\n\n"+
                    "Please select one object, then invoke the command.")
                return
            cmdExposeLinkSubs()
        except Exception as err:
            msgError(err)
            
    def IsActive(self):
        if App.ActiveDocument:
            return True
        else:
            return False
            
FreeCADGui.addCommand('Lattice2_ExposeLinkSub', _CommandExposeLinkSub())

exportedCommands = ['Lattice2_ExposeLinkSub']

