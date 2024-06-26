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

import FreeCAD, Part
from lattice2Executer import CancelError
if FreeCAD.GuiUp:
    import FreeCADGui
    from PySide import QtCore, QtGui

def translate(context, text, disambig):
    #Lattice2 is not translatable, sorry...
    return text


def getParamRefine():
    return FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/Part/Boolean").GetBool("RefineModel")
def getParamPDRefine():
    return FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/PartDesign").GetBool("RefineModel")

def getIconPath(icon_dot_svg):
    return ":/icons/" + icon_dot_svg

class SelectionError(FreeCAD.Base.FreeCADError):
    '''Error that isused inside Gui command code'''
    def __init__(self, title, message):
        self.message = message
        self.args = (message,)
        self.title = title

def msgError(err = None, message = u'{errmsg}'):
    import sys
    if err is None:
        err = sys.exc_info()[1]
    if type(err) is CancelError: return # doesn't work! Why!
    if hasattr(err, "isCancelError") and err.isCancelError: return   #workaround

    # can we get a traceback?
    b_tb =  err is sys.exc_info()[1]
    if b_tb:
        import traceback
        tb = traceback.format_exc()
        import FreeCAD as App
        App.Console.PrintError(tb+'\n')
    
    #make messagebox object
    from PySide import QtGui
    mb = QtGui.QMessageBox()
    mb.setIcon(mb.Icon.Warning)
    
    #fill in message
    errmsg = ''
    if hasattr(err,'message'):
        if isinstance(err.message, dict):
            errmsg = err.message['swhat']
        elif len(err.message) > 0:
            errmsg = err.message
        else: 
            errmsg = str(err)
    else:
        errmsg = str(err)
    mb.setText(message.format(errmsg= errmsg, err= err))
    
    # fill in title
    if hasattr(err, "title"):
        mb.setWindowTitle(err.title)
    else:
        mb.setWindowTitle("Error")
        
    #add traceback button
    if b_tb:
        btnClose = mb.addButton(QtGui.QMessageBox.StandardButton.Close)
        btnCopy = mb.addButton("Copy traceback", QtGui.QMessageBox.ButtonRole.ActionRole)
        mb.setDefaultButton(btnClose)
        
    mb.exec_()
    if b_tb:
        if mb.clickedButton() is btnCopy:
            cb = QtGui.QClipboard()
            cb.setText(tb)
        

def infoMessage(title, message):
    mb = QtGui.QMessageBox()
    mb.setIcon(mb.Icon.Information)
    mb.setText(message)
    mb.setWindowTitle(title)
    mb.exec_()

def deselect(sel):
    '''deselect(sel): remove objects in sel from selection'''
    for selobj in sel:
        FreeCADGui.Selection.removeSelection(selobj.Object)
        
# OCC's Precision::Confusion; should have taken this from FreeCAD but haven't found; unlikely to ever change.
DistConfusion = 1e-7
ParaConfusion = 1e-8

if FreeCAD.GuiUp:
    import lattice2_rc

def screen(feature):
    """screen(feature): protects link properties from being overwritten. 
    This is to be used as workaround for a bug where modifying an object accessed through 
    a link property of another object results in the latter being touched.
    
    returns: feature"""
    if not hasattr(feature,"isDerivedFrom"):
        return feature
    if not feature.isDerivedFrom("App::DocumentObject"):
        return feature
    if feature.Document is None:
        return feature
    feature = getattr(feature.Document, feature.Name)
    return feature

def activeBody():
    if FreeCAD.ActiveDocument is None: return None
    if not hasattr(FreeCADGui.ActiveDocument.ActiveView, 'getActiveObject'): #prevent errors in 0.16
        return None
    return FreeCADGui.ActiveDocument.ActiveView.getActiveObject("pdbody")
    
def bodyOf(feature):
    body = feature.getParentGeoFeatureGroup()
    if body.isDerivedFrom('PartDesign::Body'):
        return body
    else:
        return None


# Older FreeCAD has Support, newer has AttachmentSupport: https://github.com/FreeCAD/FreeCAD/issues/12894

def getAttachmentSupport(documentObject):
    if hasattr(documentObject, 'AttachmentSupport'):
        return documentObject.AttachmentSupport
    elif hasattr(documentObject, 'Support'):
        return documentObject.Support
    raise AttributeError('No support property found')
