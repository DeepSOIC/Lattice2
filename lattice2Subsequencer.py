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

__title__="Subsequencer: module with code to extract chains of similar elements from compounds"
__author__ = "DeepSOIC"
__url__ = ""

# -----------------------<CONSTANTS>-------------------------
TRAVERSAL_MODES = ['Compund children','Compound leaves']
LOOP_MODES = ['Till end', 'All around', 'All from first']
# -----------------------</CONSTANTS>------------------------

# -----------------------<EXCEPTIONS>------------------------
class TraversalError(TypeError):
    "Error to raise when extracting children from compound fails"
    pass
    
class SubsequencingError(ValueError):
    "General error, that subsequencing is impossible or failed"
    pass
   
class SubsequencingError_LinkType(SubsequencingError):
    "Subsequencing can't be applied to this link type (e.g. App::PropertyLink)."
    pass

class SubsequencingError_LinkValue(SubsequencingError):
    "Type of links to subsequence are right, but they happen to be links to whole objects, or otherwise impossible to iterate"
    pass
# -----------------------</EXCEPTIONS>------------------------

# -----------------------<HELPER STUFF>-----------------------
class HashableShape(object):
    "Decorator for Part.Shape, that can be used as key in dicts. Based on isSame method."
    def __init__(self, shape):
        self.Shape = shape
        self.hash = shape.hashCode()

    def __eq__(self, other):
        return self.Shape.isSame(other.Shape)

    def __hash__(self):
        return self.hash

def traverseCompound(compound, traversal):
    if traversal == 'Compund children':
        if compound.ShapeType != 'Compound':
            raise TraversalError("Shape is not compound; can't traverse it in direct children mode.")
        return compound.childShapes()
    elif traversal == 'Compound leaves':
        import lattice2CompoundExplorer as LCE
        return LCE.allLeaves(compound)

element_extractors = {
    "Vertex": (lambda sh: sh.Vertexes),
    "Edge": (lambda sh: sh.Edges),
    "Wire": (lambda sh: sh.Wires),
    "Face": (lambda sh: sh.Faces),
    "Shell": (lambda sh: sh.Shells),
    "Solid": (lambda sh: sh.Solids),
    "CompSolid": (lambda sh: sh.CompSolids),
    "Compound": (lambda sh: sh.Compounds),
}    
        
def getIndexesIntoList(element, list_of_shapes):
    """Finds this element in shapes in list_of_shapes. This is a generator function (to be
    used if there are multiple occurences of the element). 
    [(index_into_list, element_type_string, subelement_index), ...]"""
    
    element_type_string = element.ShapeType
    element_extractor = element_extractors[element_type_string]
    
    ret = []
    
    for i_sh in xrange(len(list_of_shapes)):
        elements = element_extractor(list_of_shapes[i_sh])
        for i_el in xrange(len(elements)):
            if elements[i_el].isEqual(element):
                # to make link more robust, use negative index if one is closer to the end
                if i_el * 2 > len(elements):
                    i_el = i_el - len(elements)
                yield (i_sh, element_type_string, i_el)
# -----------------------</HELPER STUFF>-----------------------

# -------------------<LINK TYPE CONVERSION>--------------------

def linkSubList_convertToOldStyle(references):
    ("input: [(obj1, (sub1, sub2)), (obj2, (sub1, sub2))]\n"
    "output: [(obj1, sub1), (obj1, sub2), (obj2, sub1), (obj2, sub2)]")
    result = []
    for tup in references:
        if type(tup[1]) is tuple or type(tup[1]) is list:
            for subname in tup[1]:
                result.append((tup[0], subname))
            if len(tup[1]) == 0:
                result.append((tup[0], ''))
        elif isinstance(tup[1],basestring):
            # old style references, no conversion required
            result.append(tup)
    return result

def toLinkSubList(linksub):
    if linksub is None:
        return []
    object, subs = linksub
    if not hasattr(subs, '__iter__'):
        subs = [subs]
    return [(object, sub) for sub in subs]

def toLinkSub(linksublist):
    if not linksublist:
        return None
    linksublist = linkSubList_convertToOldStyle(linksublist)
    subs = []
    object = linksublist[0][0]
    for itobj, sub in linksublist:
        if itobj is not object:
            raise ValueError("LinkSubList can't be converted into LinkSub because it links to more than one object.")
        subs.append(sub)
    return (object, subs)

# -------------------</LINK TYPE CONVERSION>--------------------
        
# ---------------------------<API>------------------------------

def Subsequence_basic(link, traversal, loop):
    """Subsequence_basic(link, traversal, loop): low-level function powering Subsequencing. Transforms
    a single sub-link into a list of sub-links to every child of the linked compound.
    
    link: tuple (object, subelement), where object is a document object, and subelement is 
    a string like 'Edge3'.
    
    traversal: either of values from TRAVERSAL_MODES, that sets how to enumerate children
    
    loop: either of values from LOOP_MODES. Sets which children to use.
    
    returns: list of links [(object,subelement), ....]"""
    
    # extract shapes of the array
    compound = link[0].Shape
    children = traverseCompound(compound, traversal)

    # parse link string. Input: element_string. Output: element_shape, element_type_string
    element_string = link[1]
    if not issubclass(type(element_string), basestring):
        raise TypeError("Second element of link tuple must be a string, not {typ}".format(typ= type(element_string).__name__))
    element_type_string = None
    for key in element_extractors.keys():
        if element_string.startswith(key):
            element_type_string = key
            break
    if element_type_string is None:
        # raise ValueError("Subelement string format not recognized")
        # resort to generic FreeCAD method
        element_shape = compound.getElement(element_string)
    else:
        # use negative-index-aware method
        #extract index from string:
        index = -1 + int(    element_string[  len(element_type_string)  :  ]    )
        element_shape = element_extractors[element_type_string](compound)[index]
    
    # convert global element index to index in child 
    i_first_child, element_type_string, i_in_child = getIndexesIntoList(element_shape, children).next()
    if loop == 'All from first':
        i_first_child = 0
    
    elements = element_extractors[element_type_string](compound) 
    index_dict = dict([(HashableShape(elements[i]), i) for i in xrange(len(elements))])
    
    # find the element in each child, find out its global index, and output result in a form of a string for a link
    ret = [] #list of tuples (object, subelement_string)
    for i in range(    len(children) if loop != 'Till end' else len(children) - i_first_child    ):
        i_child = (i + i_first_child) % len(children)
        element = element_extractors[element_type_string](children[i_child])[i_in_child]
        ret.append((
            link[0],
            element_type_string + str(index_dict[HashableShape(element)]+1)
        ))
    return ret

def Subsequence_LinkSubList(linksublist, traversal = TRAVERSAL_MODES[0], loop = LOOP_MODES[0], object_filter = None, index_filter = None):
    """Subsequence_LinkSubList(linksublist, traversal = TRAVERSAL_MODES[0], loop = 'Till end', object_filter = None):
    form a list of values for iterating over elements in App::PropertyLinkSubList.
    
    linksublist: the value of property (either of type [(object, sub), ..], or 
    [(object, [sub1, sub2, ...]), ...]
    
    traversal: how to unpack compounds
    
    loop: sets which children to process.
    
    object_filter: list or set of objects that should be considered being arrays. If 
    omitted, all links to subelements are attempted to be enumerated as arrays.
    
    index_list: list or set of ints, that sets which parts of link are to be subsequenced. 
    If None, all elements are attempted to be subsequenced, and only if none can be, an error 
    is raised. If index_list is specified, it is treated as strict, and if any 
    corresponding sublink can't be subsequenced, an error is raised.
    
    return: list of values that can be assigned to the link in a loop.
    """
    
    linksublist = linkSubList_convertToOldStyle(linksublist)
    if object_filter is None:
        object_filter = [obj for (obj,sub) in linksublist] #number of links is likely quite low, so using sets might give more of a penalty than gain

    loops = [] #list to receive subsequences for made for pieces of the link
    n_seq = None
    i = -1
    for object,sub in linksublist:
        i += 1
        if (sub 
            and (object in object_filter) 
            and (index_filter is None or i in index_filter)
            and hasattr(object, "Shape")     ):
            try:
                seq = Subsequence_basic((object, sub), traversal, loop)
                if len(seq) < 2:
                    from lattice2Executer import warning
                    warning(None, u"Subsequencing link index {i} to {sub} of '{obj}' yielded only one item."
                            .format(i= i, obj= object.Label, sub= sub))
            except TraversalError:
                if index_filter is not None:
                    raise # re-raise. When index list is given, treat it as that it must be subsequenced.
                loops.append((object,sub))
                continue
            loops.append(seq)
            if n_seq is None:
                n_seq = len(seq)
            else:
                n_seq = min(n_seq, len(seq))
        else:
            if index_filter and i in index_filter:
                if not sub:
                    raise SubsequencingError_LinkValue("Sublink part {index} can't be subsequenced, because it's a link to whole object, not to subelement.".format(index= i))
            loops.append((object,sub))
    assert(len(loops) == len(linksublist))
    if n_seq is None:
        raise SubsequencingError_LinkValue("In supplied link, nothing to loop over compounds was found.")
    
    # expand non-subsequenced parts of linksublist
    for i_loop in range(len(loops)):
        if type(loops[i_loop]) is not list:
            loops[i_loop] = [loops[i_loop]]*n_seq
    
    # form the result
    ret = []
    for i_seq in range(n_seq):
        ret.append(
            [loop[i_seq] for loop in loops]
        )
    return ret
    

def Subsequence_LinkSub(linksub, traversal = TRAVERSAL_MODES[0], loop = LOOP_MODES[0], object_filter = None, index_filter = None):
    """Subsequence_LinkSub(linksub, traversal = TRAVERSAL_MODES[0], loop = LOOP_MODES[0], object_filter = None):
    form a list of values for iterating over elements in App::PropertyLinkSub.
    
    linksub: the value of property, like (object, ["Edge1", "Edge3"...])
    
    traversal: how to unpack compounds

    loop: sets which children to process.
    
    object_filter: list or set of objects that should be considered being arrays. If 
    omitted, all links to subelements are attempted to be enumerated as arrays.
    
    index_list: list or set of ints, that sets which parts of link are to be subsequenced. 
    If None, all elements are attempted to be subsequenced, and only if none can be, an error 
    is raised. If index_list is specified, it is treated as strict, and if any 
    corresponding sublink can't be subsequenced, an error is raised.
    
    return: list of values that can be assigned to the link in a loop.
    """
    object, subs = linksub
    if not hasattr(subs, '__iter__'):
        subs = [subs]
    linksublist = toLinkSubList(linksub)
    vals = Subsequence_LinkSubList(linksublist, traversal, loop, object_filter, index_filter)
    return [toLinkSub(v) for v in vals]

def Subsequence_auto(link, traversal = TRAVERSAL_MODES[0], loop = LOOP_MODES[0], object_filter = None, index_filter = None):
    """Subsequence_auto(link, traversal = TRAVERSAL_MODES[0], loop = LOOP_MODES[0], object_filter = None, index_filter = None):
    form a list of values for iterating over elements in App::PropertyLinkSub or 
    App::PropertyLinkSubList.
    
    link: the value of property
    
    traversal: how to unpack compounds
    
    loop: sets which children to process.

    object_filter: list or set of objects that should be considered being arrays. If 
    omitted, all links to subelements are attempted to be enumerated as arrays.
    
    index_list: list or set of ints, that sets which parts of link are to be subsequenced. 
    If None, all elements are attempted to be subsequenced, and only if none can be, an error 
    is raised. If index_list is specified, it is treated as strict, and if any 
    corresponding sublink can't be subsequenced, an error is raised.
    
    return: list of values that can be assigned to the link in a loop.
    """
    if type(link) is list:
        # linkSubList or linkList!
        if len(link) == 0:
            raise SubsequencingError_LinkValue("Cannot subsequence empty link (link is empty list).")
        if type(link[0]) is not tuple:
            raise SubsequencingError_LinkType("LinkList cannot be subsequenced (only LinkSub or LinkSubList can).")
        return Subsequence_LinkSubList(link, traversal, loop, object_filter, index_filter)
    elif type(link) is tuple:
        # linkSub!
        return Subsequence_LinkSub(link, traversal, loop, object_filter, index_filter)
    elif link is None:
        raise SubsequencingError_LinkValue("Cannot subsequence empty link (link is None).")
    else:
        raise SubsequencingError_LinkType("Link type not recognized.")

def Subsequence_LinkDict(link_dict, traversal = TRAVERSAL_MODES[0], loop = LOOP_MODES[0], object_filter = None, index_filter = None):
    """Subsequence_LinkDict(link_dict, traversal = TRAVERSAL_MODES[0], loop = LOOP_MODES[0], object_filter = None, index_filter = None):
    subsequence a heterogeneous list of links supplied as a dict.
    
    link_dict: dictionary. Key is any, value is the value of some link property. It can be 
    SubLink, SubList, and plain Link, and LinkList (last two are skipped).
    
    traversal: how to unpack compounds
    
    loop: sets which children to process.

    object_filter: list or set of objects that should be considered being arrays. If 
    omitted, all links to subelements are attempted to be enumerated as arrays.
    
    index_list: list or set of ints, that sets which parts of link are to be subsequenced. 
    If None, all elements are attempted to be subsequenced, and only if none can be, an error 
    is raised. If index_list is specified, it is treated as strict, and if any 
    corresponding sublink can't be subsequenced, an error is raised.
    
    return: tuple (int, dict). Int is the length of the subsequence. Dict contains the 
    subsequences. It is similar to input dikt, but link values were replaced with lists of
    link values. If a link failed to be subsequenced, the key/value pair is not added to 
    return dict at all."""
 
    ret_dict = {} #ret_dict is the dict to receive result
    err_dict = {}
    
    # subsequence all links
    n_seq = None # length of shortest subsequence; None means no subsequences were made yet.
    for key in link_dict.keys():
        link = link_dict[key]
        try:
            link_seq = Subsequence_auto(link, traversal, loop, object_filter, index_filter)
            n_seq = len(link_seq) if n_seq is None else min(n_seq, len(link_seq))
            ret_dict[key] = link_seq
        # silently absorb non-subsequencable links; fail only if everything fails
        except SubsequencingError_LinkType as err:
            err_dict[key] = err 
        except SubsequencingError_LinkValue as err:
            err_dict[key] = err
        
    # trim them to shortest subsequence
    if n_seq is None:
        raise SubsequencingError_LinkValue("In supplied links, nothing to loop over compounds was found. Key-by-key errors follow: {err_list}"
          .format(err_list= "\n".join([repr(key)+": "+err_dict[key].message for key in err_dict])))
    for key in ret_dict.keys():
        seq = ret_dict[key]
        seq = seq[0:n_seq]
        ret_dict[key] = seq
    
    # done!
    return (n_seq, ret_dict)
