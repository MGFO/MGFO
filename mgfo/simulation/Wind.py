import math
import random

from .BaseSimulator import BaseSimulator as BS

class Weibull(BS):
    def __init__(self, c = 10.0, k = 1.8):
        super().__init__(model = 'weibull', post_random_model = 'none')
    
        self.models['weibull'] = self.model_weibull
        self.c = c
        self.k = k
            
    def model_weibull(self, scene):
        return random.weibullvariate(self.c,self.k)
            
class CorrelatedWeibull(BS):
    """
    CorrelatedWeibull wind speed simulator
    
    Given c and k parameters of the wind speed distribution in the site, this simulator
    generates a time-correlated wind velocity. Temporal correlation is important to study interaction with
    energy storage equipment.
    If statistical properties are more important that temporal correlation, Pure Weibull is suggested.
    
    Parameters are the standar c and k parameters of the Weibull distribution and the d parameter, that models
    the mean hourly variation of the wind speed, lower d values implies greater jumps.
    """
    
    def __init__(self, c = 10.0, k = 1.8, d = 1.0, initial_speed = None):
        super().__init__(model = 'temporal_weibull', post_random_model = 'none')
    
        self.models['temporal_weibull'] = self.model_temporal_weibull
        self.c = c
        self.k = k
        self.d = d
        
        if not initial_speed:
            self.v = random.weibullvariate(1/self.c,self.k)
        else:
            self.v = initial_speed
    
    def WeibullCDF(self, x, c, k):
        return 1.0 - math.exp(-math.pow(x/c, k))


    def model_temporal_weibull(self, scene):
        left = self.WeibullCDF(self.v, self.c, self.k)

        r = random.uniform(0,1)
        delta = random.expovariate(self.d)
        
        v = self.v
        if r <= left:
            v = v - delta
            v = 0 if v < 0 else v
        else:
            v = v + delta

        self.v = v
        return v
        