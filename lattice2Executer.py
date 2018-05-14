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

__title__="A helper module for execution of features of Lattice workbench"
__author__ = "DeepSOIC"
__url__ = ""

import FreeCAD
if FreeCAD.GuiUp:
    from PySide import QtGui

globalIsCreatingLatticeFeature = False

def executeFeature(obj):
    global globalIsCreatingLatticeFeature
    globalIsCreatingLatticeFeature = True
    try:
        obj.Proxy.execute(obj)
        obj.purgeTouched()
    except CancelError:
        obj.Document.abortTransaction()
        raise
    except Exception as err:
        try:
            error(obj,str(err))
        except CancelError:
            obj.Document.abortTransaction()
            raise            
    finally:
        globalIsCreatingLatticeFeature = False
        
        
def warning(obj,message,forceMessage = None):
    '''
    warning(obj,message, forceMessage = None): smart warning message function. If feature is being 
    created, a warning message pops up. If otherwise, the warning is printed 
    to the console/report view.
    If forceMessage is True, the message is shown regardless; if False, the message is suppressed).
    '''
    _showMsg(obj, message, forceMessage, _type= u'Warning')

def error(obj,message, forceMessage = None):
    '''
    error(obj, message, forceMessage = None): smart error message function. If feature is being 
    created, an error message pops up. If otherwise, the error is printed 
    to the console/report view.
    If forceMessage is True, the message is shown regardless; if False, the message is suppressed).
    '''
    _showMsg(obj, message, forceMessage, _type= u'Error')
    
def _showMsg(obj, message, forceMessage, _type):
    '''showMsg(obj, message, _type): convenience function, contains the shared code of error() and warning()'''
    global globalIsCreatingLatticeFeature
    if (globalIsCreatingLatticeFeature or forceMessage == True) and not forceMessage == False:
        mb = QtGui.QMessageBox()
        mb.setIcon(mb.Icon.Warning)
        mb.setText(_type + u": \n" + message)
        mb.setWindowTitle(_type)
        btnAbort = mb.addButton(QtGui.QMessageBox.StandardButton.Abort)
        btnOK = mb.addButton("Continue",QtGui.QMessageBox.ButtonRole.ActionRole)
        mb.setDefaultButton(btnOK)
        mb.exec_()
        if mb.clickedButton() is btnAbort:
            raise CancelError()
            
    else:
        if _type == 'Warning':
            printfunc = FreeCAD.Console.PrintWarning
        else:
            printfunc = FreeCAD.Console.PrintError
            
        if obj is not None:
            printfunc(obj.Name + ": " + message+"\n")
        else:
            printfunc(message+"\n")
    

class CancelError(Exception):
    def __init__(self):
        self.message = "Canceled by user"
        self.args = (self.message,)
        self.isCancelError = True