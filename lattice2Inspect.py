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

__title__="Command to inspect selected object compounding structure"
__author__ = "DeepSOIC"
__url__ = ""

import FreeCAD as App
import Part

from latticeCommon import *
import latticeCompoundExplorer as LCE
import latticeBaseFeature

def shapeInfoString(shape):
    strMsg = shape.ShapeType 
    if shape.ShapeType == 'Vertex':
        strMsg += " ("+repr(list(shape.Point))+")"
    elif shape.ShapeType == 'Edge':
        strMsg += " ("+repr(shape.Curve)+")"
    elif shape.ShapeType == 'Wire':
        strMsg += " ("+str(len(shape.childShapes()))+" segments)"
    elif shape.ShapeType == 'Face':
        strMsg += " ("+repr(shape.Surface)+")"
    elif shape.ShapeType == 'Shell':
        strMsg += " ("+str(len(shape.childShapes()))+" faces)"
    elif shape.ShapeType == 'Solid':
        strMsg += " ("+str(len(shape.childShapes()))+" shells)"
    elif shape.ShapeType == 'CompSolid':
        strMsg += " ("+str(len(shape.childShapes()))+" solids)"
    elif shape.ShapeType == 'Compound':
        strMsg += " ("+str(len(shape.childShapes()))+" objects)"
    return strMsg

class _CommandInspect:
    "Command to inspect compounding structure"
        
    def __init__(self):
        pass
    
    def GetResources(self):
        return {'Pixmap'  : getIconPath("Lattice_Inspect.svg"),
                'MenuText': QtCore.QT_TRANSLATE_NOOP("Lattice_Inspect","Inspect selection") , # FIXME: not translation-friendly!
                'Accel': "",
                'ToolTip': QtCore.QT_TRANSLATE_NOOP("Lattice_Inspect","Lattice Inspect: display info on compounding structure of selected object.")}
        
    def Activated(self):
        sel = FreeCADGui.Selection.getSelectionEx()[0]
        isLattice = latticeBaseFeature.isObjectLattice(sel.Object)
        
        strStructure = []
        if not hasattr(sel.Object,"Shape"):
            strStructure = ["<object has no shape!>"]
        for (child, msg, it) in LCE.CompoundExplorer(sel.Object.Shape):
            #child is a shape. 
            #msg is int equal to one of three constants:
            #    CompoundExplorer.MSG_LEAF  - child is a leaf (non-compound)
            #    CompoundExplorer.MSG_DIVEDOWN  - child is a compound that is about to be traversed
            #    CompoundExplorer.MSG_BUBBLEUP  - child is a compound that was just finished traversing        
            #it is reference to iterator class (can be useful to extract current depth, or index stack)
            if msg == LCE.CompoundExplorer.MSG_LEAF or msg == LCE.CompoundExplorer.MSG_DIVEDOWN:
                try:
                    strMsg =  '    ' * it.curDepth() + shapeInfoString(child)
                    if msg == LCE.CompoundExplorer.MSG_DIVEDOWN:
                        strMsg += ":"
                except Exception as err:
                    strMsg = "ERROR: " + err.message
                strStructure.append(unicode(strMsg))
            
        strSubInfo = []
        if sel.HasSubObjects:
            subNames = sel.SubElementNames
            subObjects = sel.SubObjects
            for i in range(0,len(subNames)):
                strMsg = subNames[i] + ": "
                child = subObjects[i]
                
                try:
                    strMsg += shapeInfoString(child)
                except Exception as err:
                    strMsg += "ERROR: " + err.message
                strSubInfo.append(unicode(strMsg))
        
        allText = u''
        if sel.HasSubObjects:
            allText += u"Selected " + str(len(sel.SubElementNames)) + u" subelements:\n"
            allText += u'\n'.join(strSubInfo) + u'\n\n'
        
        allText += u'Selected document object:\n'
        allText += u'  Name = ' + unicode(sel.Object.Name) + u'\n'
        allText += u'  Label = ' + sel.Object.Label + u'\n'
        allText += u'  Is Lattice = ' + unicode(repr(isLattice)) + u'\n'
        allText += u'Structure: \n'
        allText += u'\n'.join(strStructure)
        mb = QtGui.QMessageBox()
        mb.setIcon(mb.Icon.Information)
        mb.setText(allText)
        mb.setWindowTitle(translate("Lattice_Inspect","Selection info", None))
        
        btnClose = mb.addButton(QtGui.QMessageBox.StandardButton.Close)
        btnCopy = mb.addButton("Copy to clipboard",QtGui.QMessageBox.ButtonRole.ActionRole)
        mb.setDefaultButton(btnClose)
        mb.exec_()
        
        if mb.clickedButton() is btnCopy:
            cb = QtGui.QClipboard()
            cb.setText(allText)

    def IsActive(self):
        if len(FreeCADGui.Selection.getSelectionEx()) == 1:
            return True
        else:
            return False

FreeCADGui.addCommand('Lattice_Inspect',_CommandInspect())

exportedCommands = ['Lattice_Inspect']

