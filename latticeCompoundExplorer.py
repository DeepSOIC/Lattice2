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

import Part

class CompoundExplorer:
    """
    CompoundExplorer: Iterator class to traverse compound hierarchy.
    Usage:
    for (child, msg, it) in latticeBaseFeature.CompoundExplorer(App.ActiveDocument.Compound.Shape):
        #child is a shape. 
        #msg is int equal to one of three constants:
        #    CompoundExplorer.MSG_LEAF  - child is a leaf (non-compound)
        #    CompoundExplorer.MSG_DIVEDOWN  - child is a compound that is about to be traversed
        #    CompoundExplorer.MSG_BUBBLEUP  - child is a compound that was just finished traversing        
        #it is reference to iterator class (can be useful to extract current depth, or index stack)
        print '    ' * it.curDepth(), (child, msg)
    
    Output:
    (<Compound object at 0000002FD26E5FC0>, 2)
        (<Solid object at 0000002FCD21D380>, 1)
        (<Compound object at 0000002FCD21D280>, 2)
            (<Solid object at 0000002FCD21D7C0>, 1)
            (<Solid object at 0000002FCD21D440>, 1)
        (<Compound object at 0000002FCD21D280>, 3)
    (<Compound object at 0000002FD26E5FC0>, 3)
    """
    
    #constants
    MSG_LEAF = 1 #the iterator has output a leaf of the compound structure tree (a shape that is not a compound)
    MSG_DIVEDOWN = 2 #the iterator is entering a subcompound. Shape is the subcompound about to be iterated
    MSG_BUBBLEUP = 3 #the iterator has finished traversing a subcompound and leaves it. Shape is the compound that was just iterated through.
    
    def __init__(self, compound):
        self.compound = compound
        
        self.indexStack = [-1]
        
        #childStructure: list of lists of shapes.
        # It is for storing the stack of childShapes. The last in the 
        # list is the list of children being traversed at the moment.
        # When just starting, the list contains the base shape - the compound itself.
        # After first iteration, childShapes of compound are added as a second item.
        # If among those childshapes, a subcompound is encountered, its childShapes are added as the next item.
        # When finishing the iteration of a subcompound, the last item is removed from this list.
        # The length of this list should always be equal to the length of indexStack
        self.childStructure = [[compound]] 
        
        self.lastMsg = self.MSG_BUBBLEUP
        
    def __iter__(self):
        return self
        
    def nxtDepth(self):
        '''
        nxtDepth(): Returns depth inside compound hierarchy that is being entered (applicable when depth is changing, i.e. msg != MSG_LEAF). 
        For reference: depth of the base shape (compound that was supplied when initiating the loop) is zero.
        '''
        assert(len(self.indexStack) == len(self.childStructure))
        return len(self.indexStack) - 1
        
    def prevDepth(self):
        '''
        prevDepth(): Returns depth inside compound hierarchy that is being left (applicable when depth is changing, i.e. msg != MSG_LEAF). 
        For reference: depth of the base shape (compound that was supplied when initiating the loop) is zero.
        '''
        if self.lastMsg == self.MSG_BUBBLEUP:
            return self.nxtDepth() + 1
        elif self.lastMsg == self.MSG_DIVEDOWN:
            return self.nxtDepth() - 1
        else:
            return self.nxtDepth()

    def curDepth(self):
        '''
        curDepth(): Returns depth inside compound hierarchy of the item that was just returned. 
        For reference: depth of the base shape (compound that was supplied when initiating the loop) is zero.
        '''
        if self.lastMsg == self.MSG_BUBBLEUP:
            return self.nxtDepth() 
        elif self.lastMsg == self.MSG_DIVEDOWN:
            return self.nxtDepth() - 1
        else:
            return self.nxtDepth()
        
    def next(self):
        """Returns a tuple: (child,message,self). """
        d = self.nxtDepth()
        if d == -1:
            raise StopIteration()
            
        self.indexStack[d] += 1
        i = self.indexStack[d]
        if i > len(self.childStructure[d])-1: #index gone out of range - finished traversing a subcompound
            msg = self.MSG_BUBBLEUP
            self.indexStack.pop()
            self.childStructure.pop()
            if len(self.indexStack) == 0:
                raise StopIteration()
            i = self.indexStack[d-1]
            sh = self.childStructure[d-1][i]
        else:
            sh = self.childStructure[d][i]
            if sh.ShapeType == 'Compound':
                msg = self.MSG_DIVEDOWN
                self.indexStack.append(-1)
                self.childStructure.append(sh.childShapes())
            else:
                msg = self.MSG_LEAF
        assert(msg != 0)
        self.lastMsg = msg
        return (sh, msg, self)


def CalculateNumberOfLeaves(compound):
    '''CalculateNumberOfLeaves(compound): calculates the number of non-compound shapes (leaves) in the compound tree. Slow; good candidate for transferring into C++.'''
    if compound.ShapeType != 'Compound':
        return 1
    else:
        children = compound.childShapes(False,False)
        cnt = 0
        for ch in children:
            cnt += CalculateNumberOfLeaves(ch)
        return cnt
        
def AllLeaves(compound):
    'AllLeaves(compound): Traverses the compound and collects all the leaves into a single list'
    output = []
    for (child, msg, it) in CompoundExplorer(compound):
        if msg == it.MSG_LEAF:
            output.append(child)
    return output