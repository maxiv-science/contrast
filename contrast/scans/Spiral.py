from .Scan import SoftwareScan
from .AScan import DScan
from ..environment import macro, MacroSyntaxError
from ..motors import all_are_motors
import numpy as np
import time


from .Scan import SoftwareScan
from .AScan import DScan, AScan
from ..environment import macro, MacroSyntaxError
from ..motors import all_are_motors
import numpy as np
import time

@macro
class SpiralScan(DScan):
    """
    Software scan across a 2D Archimedes spiral centered on the 
    current position. ::
        
        spiralscan <motor1> <motor2> <stepsize> <positions> <exp_time>
    """

    def __init__(self, m1, m2, stepsize, npos, exptime, **kwargs):
        # Parse arguments. We're inheriting DScan to get its nice run()
        # method, but we'll call the SoftwareScan constructor anyway bacause
        # we're not interested in DScan's way of parsing arguments.
        try:
            SoftwareScan.__init__(self, float(exptime))
            self.motors = [m1, m2]
            self.stepsize = float(stepsize)
            self.n_positions = int(npos)
            assert all_are_motors(self.motors)
        except:
            raise MacroSyntaxError

    def _generate_positions(self):
        starting = [m.position() for m in self.motors]
        for t in range(self.n_positions):
            A = self.stepsize * np.sqrt(t/np.pi)
            B = np.sqrt(4*np.pi*t)
            yield {self.motors[0].name: starting[0] + A * np.cos(B),
                   self.motors[1].name: starting[1] + A * np.sin(B)}

@macro
class FermatScan(AScan):
    """
    Software scan in the shape of a fermat spiral (good for ptychography scan).
    The center of the spiral will be the center of the given rectangle.
    Both motors have to be in the same units. ::
        
        fermatscan <motor1> <start> <stop> <motor2> <start> <stop> <stepsize> <exp_time>

    optional keyword arguments:
        optimize: boolean ... will try to solve the traveling salesman problem
                              WARNING: can be slow for large scans!
    """

    def __init__(self, m1, l1_l, l1_u, m2, l2_l, l2_u, stepsize, exptime, **kwargs):
        try:
            SoftwareScan.__init__(self, float(exptime))
            self.motors = [m1, m2]
            self.limits = [[l1_l, l1_u],[l2_l, l2_u]]
            self.stepsize = float(stepsize)
            self.optimize = False
            self.calc_positions()
            self.n_positions = int(len(self.pos_12))
            assert all_are_motors(self.motors)
        except:
            raise MacroSyntaxError

    def calc_positions(self):
        # scaling factors and angular step width
        c_0    = 0.524   # 3rd closest neighbor is on average one step away
        c      = c_0*self.stepsize
        phi    = 0.5*(1+np.sqrt(5))
        phi_0  = 2*np.pi/(1+phi)
        # center and size of the rectangular scan field
        center = [0.5*(l[0]+l[1]) for l in self.limits] 
        size   = [np.abs(l[0]-l[1]) for l in self.limits]
        # max radius of and scan points in the spiral
        r_max  = 0.5*np.sqrt(size[0]**2+size[1]**2)
        n_max  = int(np.ceil((r_max/c)**2))
        # calculate all positions until n_max (and thus r_max)
        n      = np.linspace(0,n_max,n_max+1, endpoint=True)
        pos_1  = c*np.sqrt(n)*np.sin(n*phi_0)+center[0]
        pos_2  = c*np.sqrt(n)*np.cos(n*phi_0)+center[1]
        # remove positions outside the scan rectangle
        pos_12 = []
        for i, p1 in enumerate(pos_1):
            p2 = pos_2[i]
            if not(p1>self.limits[0][0]):
                continue
            if not(p1<self.limits[0][1]):
                continue
            if not(p2>self.limits[1][0]):
                continue
            if not(p2<self.limits[1][1]):
                continue
            pos_12.append([p1,p2])
        pos_12 = np.array(pos_12)
        # finding a short(er) scan path
        if self.optimize:
            # basically... solving the TSP problem
            best_path = self.two_opt(pos_12)
            self.pos_12 = pos_12[best_path]
        else:
            # sort on the first motor axis
            best_path = np.argsort(pos_12[:,0])
            self.pos_12 = pos_12[best_path]

    def _generate_positions(self):
        #generate the positions in the improved order
        for i, pos in enumerate(self.pos_12):
            yield {self.motors[0].name: pos[0],
                   self.motors[1].name: pos[1]}

    def two_opt(self, cities, improvement_threshold=0.5, max_iter=4):
        # 2-opt Algorithm adapted from https://en.wikipedia.org/wiki/2-opt
        # from https://stackoverflow.com/questions/25585401/travelling-salesman-in-scipy

        # Calculate the euclidian distance in n-space of the route r 
        # traversing cities c, ending at the path start.
        def path_distance(r,c): 
            return np.sum([np.linalg.norm(c[r[p]]-c[r[p-1]]) for p in range(len(r))])

        # Reverse the order of all elements from element i to element k in array r.
        def two_opt_swap(r,i,k): 
            return np.concatenate((r[0:i],r[k:-len(r)+i-1:-1],r[k+1:len(r)]))

        route = np.arange(cities.shape[0])
        improvement_factor = 1 
        iterations = 0
        best_distance = path_distance(route,cities) 
        while improvement_factor > improvement_threshold and iterations<max_iter: 
            distance_to_beat = best_distance 
            for swap_first in range(1,len(route)-2): 
                for swap_last in range(swap_first+1,len(route)): 
                    new_route = two_opt_swap(route,swap_first,swap_last)
                    new_distance = path_distance(new_route,cities) 
                    if new_distance < best_distance: 
                        route = new_route
                        best_distance = new_distance 
            improvement_factor = 1 - best_distance/distance_to_beat 
            iterations += 1
        return route
