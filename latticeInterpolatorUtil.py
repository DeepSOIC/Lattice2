import FreeCAD as App
import Part


class InterpolateF:
    '''InterpolateF class interpolates an F(x) function from a set of points using BSpline interpolation'''

    def __init__(self, XPoints = None, YPoints = None):
        self.XPoints = XPoints
        self.YPoints = YPoints
        if XPoints is not None:
            self.recompute
        
    def recompute(self):
        '''call before using value(), if changing sample values via attributes'''
        
        #compute min-max
        XPoints = self.XPoints
        YPoints = self.YPoints
        x_max = max(XPoints)
        x_min = min(XPoints)
        self._x_max = x_max
        self._x_min = x_min
        if x_max - x_min <= (x_max + x_min)*1e-9:
            raise ValueError('X range too small')
        min_x_step = x_max - x_min #initialize
        for i in range(0,len(self.XPoints)-1):
            step = abs(  XPoints[i+1] - XPoints[i]  )
            if  step <= (x_max + x_min)*1e-9:
                raise ValueError("X points "+str(i)+"-"+str(i+1)+" are too close.")
            if step < min_x_step:
                min_x_step = step

        y_min = min(YPoints)
        y_max = max(YPoints)
        
        # we want to make sure the smallest X step is way larger than possible 
        # Y step, so only X points affect knotting. This is what we are using 
        # _x_multiplicator for - it is the scaling applied to X coordinates of 
        # the interpolation points. Doing this will make u parameter of the 
        # spline equivalent to X coordinate.
        self._x_multiplicator = 1e20*(y_max - y_min)/min_x_step 
        
        # This fixes nan outut if y span is zer length
        if y_max - y_min < 1e-40:
            self._x_multiplicator = 1.0
        
        # create the spline
        if not hasattr(self,"_spline"):
            self._spline = Part.BSplineCurve()
        spline = self._spline
        
        points_for_spline = [App.Vector(XPoints[i]*self._x_multiplicator, YPoints[i], 0.0) for i in range(0,len(XPoints))]
        spline.approximate(points_for_spline)
        
    def value(self, x):
        return self._spline.value(    (x - self._x_min)  /  (self._x_max - self._x_min)    ).y
