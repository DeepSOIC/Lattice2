#***************************************************************************
#*                                                                         *
#*   Copyright (c) 2018 - Victor Titov (DeepSOIC)                          *
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

__title__="CoinGlue module of FreeCAD add-on Lattice2"
__author__ = "DeepSOIC"
__url__ = ""
__doc__ = "Glue and conversion routines between coin and freecad"

def cointransform(placement, scale = 1.0, modifyme = None):
    """cointransform(placement, scale = 1.0, modifyme = None): creates/updates SoTransform node from FreeCAD.Placement.
    modifyme: the existing node to be modified.
    Returns: SoTransform node (new if modifyme is None else modifyme)"""

    from pivy import coin
    tr = coin.SoTransform() if modifyme is None else modifyme
    tr.scaleFactor.setValue(scale,scale,scale)
    tr.translation.setValue(*tuple(placement.Base))
    tr.rotation.setValue(*placement.Rotation.Q)
    return tr
    
def readNodeFromFile(fullpath):
    """readNodeFromFile(fullpath): reads a file. Returns SoSeparator node, containing the read out stuff."""
    from pivy import coin
    i = coin.SoInput()
    if not i.openFile(fullpath): raise ValueError("Failed to open file: {fn}".format(fn= fullpath))
    import pivy
    sep = pivy.SoDB.readAll(i)
    i.closeFile()
    return sep
