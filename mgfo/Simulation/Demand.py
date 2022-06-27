import math
import random

from .BaseSimulator import BaseSimulator as BS

class DemandSimulator(BS):
    """
    Demand simulator is at its core a piecewise simulator, plus a season component
    sine-based, north-hemisfere referenced, that is, winter starts Dec. 21
    growth parameter from scenes is taken into account.
    """
    
    def __init__(self, hour_steps = None, hour_values = None, summer_peak = 0.3, winter_peak = 0.2, post_random_up = 0.2, post_random_down = 0.2):
        super().__init__(model = 'seasoned_piecewise', post_random_up = post_random_up, post_random_down = post_random_down)
        
        self.summer_peak = summer_peak
        self.winter_peak = winter_peak
        
        if hour_steps and hour_values:
            self.piecewise_hours = hour_steps
            self.piecewise_values = hour_values
        elif hour_steps or hour_values:
            raise ValueError("Hour steps and values must be set simultaneously")
        else:
            self.piecewise_hours =  [ 6.0, 8.0, 18.0, 22.0, 24.0]
            self.piecewise_values = [ 0.2, 0.4,  0.5,  1.0,  0.3]            
    
        self.models['seasoned_piecewise'] = self.model_seasoned_piecewise
        
    def model_seasoned_piecewise(self, scene):
        #initial value, hourly-based:
        val = self.models['piecewise'](scene)
        
        d = scene['day']
        #year is divided in two seasons: winter, peaking on -10th, and summer, peaking in 172th
        #then, summer season starts the day 172 - 3/8*365 = 36th up to 36th + 182 = 219th day
        #This way, summer holds spring and summer. In mid-spring there are a warm season minimmum.
        #The same corresponds to mid-fall
        
        season_coef = math.cos((d + 10.0)/182.5*2*math.pi)  
        if d < 36 or d > 219:
            val = val*(1+self.winter_peak*season_coef)
        else:
            val = val*(1+self.summer_peak*season_coef)
        
        if 'growth' in scene:
            val = val * scene['growth']
            
        return val
