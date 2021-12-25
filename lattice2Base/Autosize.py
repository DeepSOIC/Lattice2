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

__title__= "Lattice2 Autosize module"
__author__ = "DeepSOIC"
__url__ = ""
__doc__ = (
"""helper module for Lattice add-on workbench for FreeCAD. Routines used to guess sizes for primitives.
"""
)

from . import Rounder
from . import Containers

import FreeCAD as App
import math
from math import radians


def convenientModelWidth():
    """convenientModelWidth(): returns a size that will conveniently fit in the width of screen"""
    return Autosize().convenientModelWidth()
def convenientModelSize():
    """convenientModelSize(): returns a size of a box that will conveniently fit in the screen"""
    return Autosize().convenientModelSize()
def minimalSize():
    """minimalSize(): returns a size that will be barely recognizable on the screen (it is a rounded pick radius in model space)"""
    return Autosize().minimalSize()
def convenientMarkerSize():
    """convenientMarkerSize(): size of object to be able to comfortably select faces"""
    return Autosize().convenientMarkerSize()
def convenientFeatureSize():
    """convenientFeatureSize(): size in between marker size and model size. Should be reasonable to edit, but not fill the whole screen."""
    return Autosize().convenientFeatureSize()
def convenientPosition():
    return Autosize().convenientPosition()

def getLocalOriginPosition():
    ac = Containers.activeContainer()
    if ac is None:
        return App.Vector()
    elif ac.isDerivedFrom('App::Document'): #special case for v0.16
        return App.Vector()
    else:
        return Containers.Container(ac).getFullTransform().Base

def _printTraceback(err):
    import traceback
    tb = traceback.format_exc()
    App.Console.PrintError("Lattice Autosize error: {err}\n{tb}\n\n".format(err= str(err), tb= tb))


class ViewportInfo(object):
    camera_type = 'perspective' #string: perspective or orthographic
    camera_placement = App.Placement(App.Vector(0,0,1), App.Rotation())
    camera_focalplacement = App.Placement()
    camera_focaldist = 1.0
    camera_heightangle = radians(45) #total horizontal view angle, in radians (for perspective camera)
    camera_height = 1 #screen height in model space (mm), for orthographic camera
    viewport_size_px = (1800,1000) #width, height of viewport, in pixels
    viewport_size_mm = (1.8,1.0) #width, height of viewport (on focal plane), in mm
    mm_per_px = 1.0 / 1000.0 #rough mm-to-pixel ratio (accurate on focal plane)
    false_viewport = True # if true, no actual viewport was queried (e.g. non-gui mode, or activeview is non-3d)
    
    pickradius_px = 5
    pickradius_mm = 0.1
    
    def __init__(self, viewer = None):
        try:
            if not(App.GuiUp or viewer is not None):
                return
                
            if viewer == None:
                import FreeCADGui as Gui
                viewer = Gui.ActiveDocument.ActiveView
            
            if not hasattr(viewer, 'getCameraNode'):
                return
                
            import pivy
            cam = viewer.getCameraNode()
            self.camera_type = 'perspective' if isinstance(cam, pivy.coin.SoPerspectiveCamera) else 'orthographic'
            self.camera_placement = App.Placement(
                App.Vector(cam.position.getValue().getValue()), 
                App.Rotation(*cam.orientation.getValue().getValue())
            )
            self.camera_focaldist = cam.focalDistance.getValue()
            self.camera_focalplacement = self.camera_placement.multiply(App.Placement(App.Vector(0,0,-self.camera_focaldist), App.Rotation()))
            
            if self.camera_type == 'perspective':
                self.camera_heightangle = cam.heightAngle.getValue()
                self.camera_height = math.tan(self.camera_heightangle / 2) * self.camera_focaldist * 2 
            else:
                self.camera_height = cam.height.getValue()
                self.camera_focaldist = self.camera_height / 2 / math.tan(radians(45)/2) #in parallel projection, focal distance has strange values. Reconstructing a focal distance for a typical perspective camera...

            self.false_viewport = False
    
            rman = viewer.getViewer().getSoRenderManager()
            self.viewport_size_px = tuple(rman.getWindowSize())
            
            mmppx = self.camera_height/self.viewport_size_px[1]
            self.mm_per_px = mmppx
            
            self.viewport_size_mm = (self.viewport_size_px[0]*mmppx, self.viewport_size_px[1]*mmppx)
            
            self.pickradius_px = App.ParamGet("User parameter:BaseApp/Preferences/View").GetFloat("PickRadius", 5.0)
            self.pickradius_mm = self.pickradius_px * mmppx
            
        except Exception as err:
            import traceback
            tb = traceback.format_exc()
            App.Console.PrintError("Lattice Autosize: failed to query viewport: {err}\n{tb}\n\n".format(err= str(err), tb= tb))

class Autosize(ViewportInfo):
    convenient_model_size_multiplier = 0.4
    def __init__(self, viewer = None):
        super(Autosize, self).__init__(viewer)
    
    def convenientModelWidth(self):
        """convenientModelWidth(): returns a size that will conveniently fit in the width of screen"""
        try:
            return Rounder.roundToNiceValue(self._convenientModelWidth())
        except Exception as err:
            _printTraceback(err)
            return 10.0
            
    def convenientModelSize(self):
        """convenientModelSize(): returns a size of a box that will conveniently fit in the screen"""
        try:
            return Rounder.roundToNiceValue(self._convenientModelSize())
        except Exception as err:
            _printTraceback(err)
            return 10.0

    def minimalSize(self):
        """minimalSize(): returns a size that will be barely recognizable on the screen (it is a rounded pick radius in model space)"""
        try:
            return Rounder.roundToNiceValue(self._minimalSize())
        except Exception as err:
            _printTraceback(err)
            return 0.1

    def convenientMarkerSize(self):
        """convenientMarkerSize(): size of object to be able to comfortably select faces"""
        try:
            return Rounder.roundToNiceValue(self._convenientMarkerSize())
        except Exception as err:
            _printTraceback(err)
            return 1.0

    def convenientFeatureSize(self):
        """convenientFeatureSize(): size in between marker size and model size. Should be reasonable to edit, but not fill the whole screen."""
        try:
            return Rounder.roundToNiceValue(self._convenientFeatureSize())
        except Exception as err:
            _printTraceback(err)
            return 5.0
    
    def convenientPosition(self):
        try:
            if self.isPointInWorkingArea(getLocalOriginPosition()):
                return App.Vector()
            else:
                roundfocal = Rounder.roundToNiceValue(self.camera_focaldist*0.5)
                result =  App.Vector(
                    [Rounder.roundToPrecision(coord, roundfocal) for coord in tuple(self.camera_focalplacement.Base)]
                )
                return result
        except Exception as err:
            _printTraceback(err)
            return App.Vector()
    
    def _convenientModelWidth(self):
        if self.false_viewport:
            return 10.0
        else:
            return self.viewport_size_mm[0] * self.convenient_model_size_multiplier
    def _convenientModelSize(self):
        """_convenientMarkerSize(): (unrounded) returns size of an object that would fill most of the working area"""
        if self.false_viewport:
            return 10.0
        else:
            return min(self.viewport_size_mm[0], self.viewport_size_mm[1]) * self.convenient_model_size_multiplier
            
    def _minimalSize(self):
        """_minimalSize(): (unrounded) returns minimum object size that can be seen on screen on focal plane"""
        if self.false_viewport:
            return 0.1
        else:
            return self.pickradius_mm

    def _convenientMarkerSize(self):
        """_convenientMarkerSize(): (unrounded) returns maker size that is usefully large to select faces and understand its rotation"""
        if self is None:
            self = ViewportInfo()
        if self.false_viewport:
            return 1.0
        else:
            return self.pickradius_mm * 10

    def _convenientFeatureSize(self):
        """_convenientMarkerSize(): (unrounded) returns size of an object that would fill most of the working area"""
        if self is None:
            self = ViewportInfo()
        return math.sqrt(self._convenientModelSize() * self._convenientMarkerSize())
        
    def isPointInWorkingArea(self, point = App.Vector()):
        """isPointInWorkingArea(): returns True if point is not far from the visible area of focal plane. Point should be given in document coordinate system."""
        p_foc = self.camera_focalplacement.inverse().multVec(point)
        #p_foc is point in focal-plane CS. X and Y are along focal plane. Z is against view direction (positive = towards the camera).
        mheight = self.viewport_size_mm[1]*0.8
        mwidth = self.viewport_size_mm[0]*0.8
        f = self.camera_focaldist
        if abs(p_foc.x) > mwidth*0.5 or abs(p_foc.y) > mheight*0.5 or p_foc.z > f*0.5 or p_foc.z < -2*f:
            return False
        else:
            return True

