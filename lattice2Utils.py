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

__title__="Utility functions for Lattice2"
__author__ = "DeepSOIC"
__url__ = ""

def sublinkFromApart(object, subnames):
    if type(subnames) is not list and type(subnames) is not tuple:
        subnames = [subnames]
    return (object, [str(sub) for sub in subnames])     if object is not None else     None

def syncSublinkApart(selfobj, prop, sublink_prop_name, obj_property_name, subnames_prop_name):
    """syncSublinkApart(selfobj, prop, sublink_prop_name, obj_property_name, subnames_prop_name):
    Function that synchronizes a sublink mirror property with split apart property pair.
    
    selfobj, prop: as in onChanged
    
    sublink_prop_name: name of property of type "App::PropertyLinkSub"
    
    obj_property_name, subnames_prop_name: names of apart properties. First must be 
    App::PropertyLink. Second can be PropertyString or PropertyStringList.
    """
    
    # check if changed property is relevant
    if not prop in (sublink_prop_name, obj_property_name, subnames_prop_name):
        return

    #if restoring, some of the properties may not exist yet. If they don't, skip, and wait for the last relevant onChanged.
    if not ( hasattr(selfobj, sublink_prop_name) and hasattr(selfobj, obj_property_name) and hasattr(selfobj, subnames_prop_name) ): 
        return
        
    sl = sublinkFromApart(getattr(selfobj,obj_property_name), getattr(selfobj,subnames_prop_name))
    if getattr(selfobj,sublink_prop_name) != sl: #assign only if actually changed, to prevent recursive onChanged calls
        if prop == sublink_prop_name:
            # update apart properties
            tup_apart = (None, [])     if getattr(selfobj,sublink_prop_name) is None else     getattr(selfobj,sublink_prop_name)
            if type(getattr(selfobj, subnames_prop_name)) is not list:
                tup_apart = (tup_apart[0], tup_apart[1][0] if len(tup_apart[1]) == 1 else "")
            setattr(selfobj, obj_property_name, tup_apart[0])
            if tup_apart[0] is not None:
                setattr(selfobj, subnames_prop_name, tup_apart[1])
        else:
            setattr(selfobj, sublink_prop_name, sl)
