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
from PySide import QtGui

globalIsCreatingLatticeFeature = False

def executeFeature(obj):
    global globalIsCreatingLatticeFeature
    globalIsCreatingLatticeFeature = True
    try:
        obj.Proxy.execute(obj)
        obj.purgeTouched()
    except Exception as err:
        mb = QtGui.QMessageBox()
        mb.setIcon(mb.Icon.Warning)
        mb.setText("While excuting feature '"+obj.Name+"', an error occured:\n" + err.message)
        mb.setWindowTitle("Error")
        mb.exec_()
    finally:
        globalIsCreatingLatticeFeature = False
        
        
def warning(obj,message):
    '''
    warning(obj,message): smart warning message function. If feature is being 
    created, a warning message pops up. If otherwise, the warning is printed 
    into console.
    '''
    global globalIsCreatingLatticeFeature
    if globalIsCreatingLatticeFeature:
        mb = QtGui.QMessageBox()
        mb.setIcon(mb.Icon.Warning)
        mb.setText(u"Warning: \n" + message)
        mb.setWindowTitle("Warning")
        mb.exec_()
    else:
        if obj is not None:
            FreeCAD.Console.PrintWarning(obj.Name + ": " + message)
        else:
            FreeCAD.Console.PrintWarning(message)
