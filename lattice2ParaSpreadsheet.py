#***************************************************************************
#*                                                                         *
#*   Copyright (c) 2016 - Victor Titov (DeepSOIC)                          *
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

__title__="Lattice ParaSeries spreadsheet helper functions and commands"
__author__ = "DeepSOIC"
__url__ = ""
__doc__ = "Lattice ParaSeries spreadsheet helper functions and commands"


def RC_from_A1(A1_style_link):
    '''given a string like "A1", returns a tuple of two ints (row, col). Row and col are zero-based; address row index is one-based'''
    
    #assuming only two letter column
    if A1_style_link[1].isalpha():
        colstr = A1_style_link[0:2]
        rowstr = A1_style_link[2:]
    else:
        colstr = A1_style_link[0:1]
        rowstr = A1_style_link[1:]
    
    row = int(rowstr)-1
    
    colstr = colstr.upper()
    NUM_LETTERS = ord("Z")-ord("A")+1
    A = ord("A")
    mult = 1
    col = -1
    for ch in colstr[::-1]:
        col += mult * (ord(ch) - A + 1)
        mult *= NUM_LETTERS
        
    return (row,col)

def A1_from_RC(row, col):
    '''outputs an address of A1-style, given row and column indexes (zero-based)'''
    NUM_LETTERS = ord("Z")-ord("A")+1
    A = ord("A")
    colstr = chr(A + col % NUM_LETTERS)
    col -= col % NUM_LETTERS
    col /= NUM_LETTERS
    if col > 0:
        colstr = chr(A + col % (NUM_LETTERS+1) - 1) + colstr
    
    rowstr = str(row+1)
    
    return colstr + rowstr

def read_refs_value_table(spreadsheet):
    '''read_refs_value_table(spreadsheet): 
    reads out a tabe of parameters and values for ParaSeries from a specially constructed 
    spreadsheet. The first row of spreadsheet lists the parameters to be changed, 
    like 'Box.Height'. Other rows define the values.
    
    Returns tuple of two. First is list of parameter refs (strings). Second is a table of values (list of rows)'''
    
    # read out list of parameters
    r = 0
    c = 0
    params = []
    for c in range(RC_from_A1("ZZ0")[1]):
        try:
            tmp = spreadsheet.get(A1_from_RC(r,c))
            if not( type(tmp) is str or type(tmp) is unicode ):
                raise TypeError("Parameter reference must be a string; it is {type}".format(type= type(tmp).__name__))
            params.append(tmp)
        except ValueError: # ValueError is thrown in attempt to read empty cell
            break
    num_params = len(params)
    if num_params == 0:
        raise ValueError("Reading out parameter references from spreadsheet failed: no parameter reference found on A1 cell.")
    
    # read out values
    values = []
    num_nonempty_rows = 0
    num_empty_rows_in_a_row = 0
    while True:
        n_vals_got = 0
        r += 1
        val_row = [None]*num_params
        for c in range(num_params):
            try:
                val_row[c] = spreadsheet.get(A1_from_RC(r,c))
                n_vals_got += 1
            except ValueError: # ValueError is thrown in attempt to read empty cell
                pass
        values.append(val_row)
        if n_vals_got == 0:
            num_empty_rows_in_a_row += 1
            if num_empty_rows_in_a_row > 1000:
                break
        else:
            num_empty_rows_in_a_row = 0
            num_nonempty_rows += 1
        
    # trim off the last train of empty rows
    if num_empty_rows_in_a_row > 0: #always true...
        values = values[0:-num_empty_rows_in_a_row]
    
    if num_nonempty_rows == 0:
        raise ValueError("Value table is empty. Please fill the spreadsheet with values, not just references to parameters.")
    return (params, values)


