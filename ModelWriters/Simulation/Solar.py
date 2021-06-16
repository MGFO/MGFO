import math
import random

from .BaseSimulator import BaseSimulator as BS

class SolarIrradianceSimulator(BS):
    """
    summer_sunrise_advance is the advancement of sunrise time in summer
    """
    
    def __init__(self, max_irradiation = 1000.0, summer_sunrise_advance = 1.1, cloudy_days = 0.15, post_random_up = 0.03, post_random_down = 0.03):
        super().__init__(model = 'solar_plus_clouds', 
                         post_random_up = post_random_up, post_random_down = post_random_down)     
    
        self.base_value = max_irradiation
        self.models['solar_plus_clouds'] = self.model_solar_plus_clouds
        self.summer_sunrise_advance = summer_sunrise_advance
        self.cloudy_days = cloudy_days
        #cloud status perseverance
        self.current_day = None
        self.current_day_cloudy = False
        self.current_day_cloud_density = 1.0
    
    def model_solar_plus_clouds(self, scene):
        
        d = scene['day']
        h = scene['hour']
        if self.current_day != d:
            self.current_day = d
            if random.uniform(0,1) < self.cloudy_days:
                self.current_day_cloudy = True
                self.current_day_cloud_density = random.uniform(0.2, 0.6)
            else:
                self.current_day_cloudy = False
                self.current_day_cloud_density = 1.0
        
        radiation = self.base_value

        variation = 0.75 - 0.25*math.cos((d + 10.0)/365.0*2*math.pi)  

        sunrise = 7.0 + self.summer_sunrise_advance*math.cos((d + 10.0)/365.0*2*math.pi)    #es una aproximacion, no basada en modelos matematicos
        sunset = 19.0 - self.summer_sunrise_advance*math.cos((d + 10.0)/365.0*2*math.pi)

        tempo = 0.0
        
        if sunrise <= h  and h <= sunset:
            tempo = math.sin((h-sunrise)/(sunset-sunrise)*math.pi)

        return radiation*variation*self.current_day_cloud_density*tempo