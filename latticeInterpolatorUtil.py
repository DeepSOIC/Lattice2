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
        # _y_multiplicator for - it is the scaling applied to Y coordinates of 
        # the interpolation points. Doing this will make u parameter of the 
        # spline equivalent to X coordinate.
        if y_max - y_min < 1e-40:
            self._y_multiplicator = 1.0
        else:
            self._y_multiplicator = 1e-20*min_x_step/(y_max - y_min)
        
        self._y_demultiplicator = 1.0/self._y_multiplicator
        
        # create the spline
        if not hasattr(self,"_spline"):
            self._spline = Part.BSplineCurve()
        spline = self._spline
        
        points_for_spline = [App.Vector(XPoints[i], YPoints[i]*self._y_multiplicator, 0.0) for i in range(0,len(XPoints))]
        spline.interpolate(points_for_spline)
        
        #precache some scaling values for faster calculation of value()
        self._u1 = spline.FirstParameter
        self._u2 = spline.LastParameter
        self._x_to_u_scale = (self._u2 - self._u1) / (self._x_max - self._x_min)
        
    def value(self, x):
        return self._spline.value(    self._u1 + x*self._x_to_u_scale    ).y * self._y_demultiplicator
