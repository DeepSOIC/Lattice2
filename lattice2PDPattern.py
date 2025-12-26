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

__title__="Lattice PartDesign Pattern object: a partdesign pattern based on Lattice array."
__author__ = "DeepSOIC"
__url__ = ""

import FreeCAD as App
import Part

from lattice2Common import *
import lattice2BaseFeature
import lattice2Executer
from lattice2ShapeCopy import shallowCopy, transformCopy_Smart

from lattice2PopulateCopies import DereferenceArray


class FeatureUnsupportedError(RuntimeError):
    pass
class NotPartDesignFeatureError(RuntimeError):
    pass
class FeatureFailure(RuntimeError):
    pass
class ScopeError(RuntimeError):
    pass


class MultiTransformSettings(object):
    selfintersections = False #if True, take care of intersections between occurrences. If False, optimize assuming occurrences do not intersect.
    sign_override = +1 #+1 for keep sign, -1 for invert, +2 for force positive, -2 for force negative
    use_basefeature = False # take basefeature of a body as an additive operation
    debug = False # output compound instead of boolean result


def makeFeature():
    '''makeFeature(): makes a PartDesignPattern object.'''
    obj = activeBody().newObject("PartDesign::FeaturePython","LatticePattern")
    LatticePDPattern(obj)
    if FreeCAD.GuiUp:        
        ViewProviderLatticePDPattern(obj.ViewObject)
    return obj

def getBodySequence(body, skipfirst = False, use_basefeature = False):
    visited = set()
    result = []
    # start from thw tip, and walk up the sequence
    curfeature = body.Tip
    while True:
        if curfeature in visited:
            raise ValueError("Feature sequence is looped in {body}".format(body= body.Name))
        if curfeature is None:
            break
        if not curfeature.isDerivedFrom('PartDesign::Feature'):
            break
        if not body.hasObject(curfeature):
            break
        if curfeature.isDerivedFrom('PartDesign::FeatureBase'):
            #base feature for body. Stop here..
            if use_basefeature:
                result.insert(0, curfeature)
            break
        visited.add(curfeature)
        result.insert(0, curfeature)
        curfeature = curfeature.BaseFeature 
    if skipfirst:
        result.pop(0)
    return result

def feature_sign(feature, raise_if_unsupported = False):
    """feature_sign(feature, raise_if_unsupported = False): returns +1 for additive PD features, -1 for subtractive PD features, and 0 for the remaining (unsupported)"""
    additive_types = [
        'PartDesign::Pad',
        'PartDesign::Revolution',
        'PartDesign::FeatureBase',
    ]
    subtractive_types = [
        'PartDesign::Pocket',
        'PartDesign::Groove',
        'PartDesign::Hole',
    ]
    def unsupported():
        if raise_if_unsupported:
            raise FeatureUnsupportedError("Feature {name} is neither additive nor subtractive. Unsupported.".format(name= feature.Name))
        else:
            return 0

    if not feature.isDerivedFrom('PartDesign::Feature'):
        raise NotPartDesignFeatureError("Feature {name} is not a PartDesign feature. Unsupported.".format(name= feature.Name))
    if hasattr(feature, 'AddSubType'): #part-o-magic; possibly PartDesign future
        t = feature.AddSubType
        if t == 'Additive':
            return +1
        elif t == 'Subtractive':
            return -1
        else:
            return unsupported()
    typ = feature.TypeId
    if typ in additive_types:
        return 1
    if typ in subtractive_types:
        return -1
    if 'Additive' in typ:
        return +1
    if 'Subtractive' in typ:
        return -1
    if typ == 'PartDesign::Boolean':
        t = feature.Type
        if t == 'Fuse':
            return +1
        elif t == 'Cut':
            return -1
        else:
            return unsupported()
    return unsupported()
    
def getShapeCheckNull(obj, prop_name):
    sh = getattr(obj, prop_name)
    if sh.isNull():
        raise ValueError(f"{obj.Label}/{prop_name} shape is null")
    return sh

def getFeatureShapes(feature):
    sign = feature_sign(feature, raise_if_unsupported= True)
    if hasattr(feature, 'AddSubShape'):
        sh = shallowCopy(getShapeCheckNull(feature, 'AddSubShape'))
        sh.Placement = feature.Placement
        return [(sign, sh)]
    elif feature.isDerivedFrom('PartDesign::Boolean'):
        return [(sign, getShapeCheckNull(obj,'Shape')) for obj in feature.Group]
    elif feature.isDerivedFrom('PartDesign::FeatureBase'):
        sh = shallowCopy(getShapeCheckNull(feature,'Shape'))
        return [(sign, sh)]
    else:
        raise FeatureUnsupportedError("Feature {name} is not supported.".format(name= feature.Name))
        
def is_supported(feature):
    if hasattr(feature, 'Proxy') and hasattr(feature.Proxy, 'applyTransformed'):
        return True
    try:
        sign = feature_sign(feature, raise_if_unsupported= True)
        return True
    except (FeatureUnsupportedError, NotPartDesignFeatureError):
        return False

def applyFeature(baseshape, feature, transforms, mts):
    if hasattr(feature, 'Proxy') and hasattr(feature.Proxy, 'applyTransformed'):
        return feature.Proxy.applyTransformed(feature, baseshape, transforms, mts)
    task = getFeatureShapes(feature)
    for sign,featureshape in task:
        actionshapes = []
        for transform in transforms:
            actionshapes.append(shallowCopy(featureshape, transform))
            
        if mts.selfintersections:
            pass #to fuse the shapes to baseshape one by one
        else:
            actionshapes = [Part.Compound(actionshapes)] #to fuse all at once, saving for computing intersections between the occurrences of the feature
            
        for actionshape in actionshapes:
            assert(sign != 0)
            realsign = sign * mts.sign_override
            if abs(mts.sign_override) == +2:
                realsign = int(mts.sign_override / 2)
            if realsign > 0:
                if not mts.debug:
                    baseshape = baseshape.fuse(actionshape)
                else:
                    baseshape = append_to_compound(baseshape, actionshape)
            elif realsign < 0:
                if not mts.debug:
                    baseshape = baseshape.cut(actionshape)
                else:
                    baseshape = append_to_compound(baseshape, actionshape.reversed()) 
    if baseshape.isNull():
        raise FeatureFailure('applying {name} failed - returned shape is null'.format(name= feature.Name))
    return baseshape

def append_to_compound(cmp, sh):
    """append_to_compound(cmp, sh): appends a shape to a compound. cmp can be not a compound, too (any shape type, or None). returns result
    """
    if cmp is None:
        cmp = Part.Compound()
    if cmp.ShapeType != 'Compound':
        cmp = Part.Compound([cmp])
    return Part.Compound(cmp.childShapes() + [sh])

class LatticePDPattern(object):
    def __init__(self,obj):
        obj.addProperty('App::PropertyLinkListGlobal','FeaturesToCopy',"Lattice Pattern","Features to be copied (can be a body)")
        obj.addProperty('App::PropertyLinkGlobal','PlacementsFrom',"Lattice Pattern","Reference placement (placement that marks where the original feature is)")
        obj.addProperty('App::PropertyLink','PlacementsTo',"Lattice Pattern","Target placements")
        
        obj.addProperty('App::PropertyEnumeration','Referencing',"Lattice Pattern","Reference placement mode (sets what to grab the feature by).")
        obj.Referencing = ['Origin','First item', 'Last item', 'Use PlacementsFrom']
        
        obj.addProperty('App::PropertyBool', 'IgnoreUnsupported', "Lattice Pattern", "Skip unsupported features such as fillets, instead of throwing errors")
        obj.addProperty('App::PropertyBool', 'SkipFirstInBody', "Lattice Pattern", "Skip first body feature (which may be used as support for the important features).")

        obj.addProperty('App::PropertyEnumeration', 'SignOverride', "Lattice Pattern", "Use it to change Pockets into Pads.")
        obj.SignOverride = ['keep', 'invert', 'as additive', 'as subtractive']
        
        obj.addProperty('App::PropertyBool', 'Selfintersections', "Lattice Pattern", "If True, take care of intersections between occurrences. If False, you get a slight speed boost.")
        
        obj.addProperty('App::PropertyBool', 'Refine', "PartDesign", "If True, remove redundant edges after this operation.")
        obj.Refine = getParamPDRefine()
        
        obj.addProperty('App::PropertyBool', 'SingleSolid', "PartDesign", "If True, discard solids not joined with the base.")

        self.assureProperties(obj)
        obj.AllowBaseFeature = True

        obj.Proxy = self

    def assureProperties(self, obj):
        lattice2BaseFeature.assureProperty(obj,'App::PropertyBool', 'AllowBaseFeature', False, "Lattice Pattern", "Allow using BaseFeature (this property is here mostly for backwards compatibility).") 
        lattice2BaseFeature.assureProperty(obj,'App::PropertyBool', 'Debug', False, "LatticePattern", "Output a compound instead of boolean result, to analyze boolean failures.") 
    
    def execute(self, selfobj):
        self.assureProperties(selfobj)

        if selfobj.BaseFeature is None:
            baseshape = Part.Compound([])
        else:
            baseshape = selfobj.BaseFeature.Shape
        
        mts = MultiTransformSettings()
        mts.sign_override = {'keep': +1, 'invert': -1, 'as additive': +2 , 'as subtractive': -2}[selfobj.SignOverride]
        mts.selfintersections = selfobj.Selfintersections
        mts.use_basefeature = selfobj.AllowBaseFeature
        mts.debug = selfobj.Debug
        
        result = self.applyTransformed(selfobj, baseshape, None, mts)
        if selfobj.SingleSolid:
            # not proper implementation, but should do for majority of cases: pick the largest solid.
            vmax = 0
            vmax_solid = None
            for s in result.Solids:
                v = s.Volume
                if v > vmax:
                    vmax = v
                    vmax_solid = s
            if vmax_solid is None:
                raise ValueError("No solids in result. Maybe the result is corrupted because of failed BOP, or all the material was removed in the end.")
            result = vmax_solid
        if selfobj.SingleSolid or len(result.Solids) == 1:
            result = transformCopy_Smart(result.Solids[0], selfobj.Placement)
        if selfobj.Refine:
            result = result.removeSplitter()
        selfobj.Shape = result
    
    def applyTransformed(self, selfobj, baseshape, transforms, mts):
        featurelist = []
        has_bodies = False
        has_features = False
        for lnk in selfobj.FeaturesToCopy:
            if lnk.isDerivedFrom('PartDesign::Body'):
                featurelist.extend(getBodySequence(lnk, skipfirst= selfobj.SkipFirstInBody, use_basefeature= mts.use_basefeature))
                has_bodies = True
            else:
                featurelist.append(lnk)
                has_features = True
        
        #check cross-links
        if selfobj.Referencing == 'Use PlacementsFrom':
            body_ref = bodyOf(selfobj.PlacementsFrom)
        else:
            body_ref = bodyOf(selfobj)
            for feature in featurelist:
                if bodyOf(feature) is not body_ref:
                    raise ScopeError('Reference placement and the feature are not in the same body (use Shapebinder or Ghost to bring the placement in).')
        
        
        placements = lattice2BaseFeature.getPlacementsList(selfobj.PlacementsTo, selfobj)
        placements = DereferenceArray(selfobj, placements, selfobj.PlacementsFrom, selfobj.Referencing)
        if selfobj.Referencing == 'First item' and transforms is None:
            placements.pop(0) #to not repeat the feature where it was applied already 
        elif selfobj.Referencing == 'Last item' and transforms is None:
            placements.pop() #to not repeat the feature where it was applied already 
        if not transforms is None:
            newplacements = []
            for transform in transforms:
                newplacements += [transform.multiply(plm) for plm in placements]
            placements = newplacements
        for feature in featurelist:
            try:
                baseshape = applyFeature(baseshape, feature, placements, mts)
            except FeatureUnsupportedError as err:
                if not selfobj.IgnoreUnsupported:
                    raise
                else:
                    App.Console.PrintLog('{name} is unsupported, skipped.\n'.format(name= feature.Name))
        return baseshape

    def __getstate__(self):
        return None

    def __setstate__(self,state):
        return None

    def dumps(self):
        return None

    def loads(self,state):
        return None


class ViewProviderLatticePDPattern:
    "A View Provider for the Lattice PartDesign Pattern object"

    def __init__(self,vobj):
        vobj.Proxy = self
       
    def getIcon(self):
        return getIconPath("Lattice2_PDPattern.svg")

    def attach(self, vobj):
        self.ViewObject = vobj
        self.Object = vobj.Object

  
    def __getstate__(self):
        return None

    def __setstate__(self,state):
        return None

    def dumps(self):
        return None

    def loads(self,state):
        return None

    def claimChildren(self):
        weakparenting = App.ParamGet("User parameter:BaseApp/Preferences/Mod/Lattice2").GetBool("WeakParenting", True)
        if weakparenting:
            return []
        return [self.Object.PlacementsTo]
        
    def onDelete(self, host_vp, subelements): # subelements is a tuple of strings
        # reconnect next PD feature to the one before self
        host = self.Object
        dependent_objs = host.InList
        for obj in dependent_objs:
            if getattr(obj,'BaseFeature',None) == host:
                obj.BaseFeature = host.BaseFeature

        return True
    
    def setEdit(self,vobj,mode):
        if mode != 0: 
            raise NotImplementedError()
        src = self.Object.FeaturesToCopy
        if len(src) == 1:
            if src[0].isDerivedFrom('PartDesign::Body'):
                FreeCADGui.ActiveDocument.ActiveView.setActiveObject("pdbody", src[0])
        return False



# -------------------------- /document object --------------------------------------------------

# -------------------------- Gui command --------------------------------------------------


def CreateLatticePDPattern(features, latticeObjFrom, latticeObjTo, refmode):
    FreeCADGui.addModule("lattice2PDPattern")
    FreeCADGui.addModule("lattice2Executer")
    
    #fill in properties
    FreeCADGui.doCommand("f = lattice2PDPattern.makeFeature()")
    reprfeatures = ', '.join(['App.ActiveDocument.'+f.Name for f in features])
    FreeCADGui.doCommand("f.FeaturesToCopy = [{features}]".format(features= reprfeatures))
    FreeCADGui.doCommand("f.PlacementsTo = App.ActiveDocument."+latticeObjTo.Name)
    if latticeObjFrom is not None:
        FreeCADGui.doCommand("f.PlacementsFrom = App.ActiveDocument."+latticeObjFrom.Name)        
    FreeCADGui.doCommand("f.Referencing = "+repr(refmode))
    
    #execute
    FreeCADGui.doCommand("lattice2Executer.executeFeature(f)")
    
    #hide something
    FreeCADGui.doCommand("f.PlacementsTo.ViewObject.hide()")
    FreeCADGui.doCommand("f.BaseFeature.ViewObject.hide()")
        
    #finalize
    FreeCADGui.doCommand("Gui.Selection.addSelection(f)")
    FreeCADGui.doCommand("f = None")


def cmdPDPattern():
    sel = FreeCADGui.Selection.getSelectionEx()
    (lattices, shapes) = lattice2BaseFeature.splitSelection(sel)
    if len(shapes) > 0 and len(lattices) == 2:
        FreeCAD.ActiveDocument.openTransaction("Lattice Pattern")
        latticeFrom = lattices[0]
        latticeTo = lattices[1]
        CreateLatticePDPattern([so.Object for so in shapes], latticeFrom.Object, latticeTo.Object,'Use PlacementsFrom')
        deselect(sel)
        FreeCAD.ActiveDocument.commitTransaction()
    elif len(shapes) > 0 and len(lattices) == 1:
        FreeCAD.ActiveDocument.openTransaction("Lattice Pattern")
        latticeTo = lattices[0]
        CreateLatticePDPattern([so.Object for so in shapes], None, latticeTo.Object,'First item')
        deselect(sel)
        FreeCAD.ActiveDocument.commitTransaction()
    else:
        raise SelectionError("Bad selection",
            "Please select either:\n"
             " one or more PartDesign features, and one or two placements/arrays \n"
             "or\n"
             " a template body and two placements/arrays, one from selected body and one from active body."
        )

# command defined in lattice2PDPatternCommand.py
