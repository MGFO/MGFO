import pandas as pd

class SceneBuilder:
    """
    SceneBuilder class
    
    Based on description of the period of analysis for the target microgrid, SceneBuilder lets
    construct a Pandas DataFrame with a instant by instant description of the conditions, called *scene*.
    
    Each scene has the following attributes:
    
        year: Year of analysis. Can be 0 index or calendary year.
        day: Day of the year under analysis. From 0 (Jan 1st) to 365.
        dd: Number of simulated repeated days. See *dt*.
        hour: Hour of the day. Can be a fractional hour.
        dt: Delta of time for this scene, in hours or fraction.
        discount_rate: Discount rate for future costs.
        growth_rate: A coefficient that represents demand growth rate
        temperature: Temperature at the moment.
        solar_irradiance: Solar irradiance, in W/m^2, at the moment.
        wind_speed: Wind speed at the moment in m/s.
        
    Basic usage consists to specify simulation parameters using several methods and then to use
    the *build_scenes* method to return a DataFrame with the simulated scenes. An existant object that
    support dict interface can be used instead a DataFrame by setting the scenes member.
    """
    
    def __init__(self, years=1, subperiods=1, days_in_subperiods=365,  dt=1.0, discount_rate=1.0, growth_rate=1.0, 
                selected_days = None, scenes = None):
        self.years = years
        self.subperiods = subperiods
        self.days_in_subperiods = days_in_subperiods
        self.dt = dt
        self.discount_rate = discount_rate
        self.growth_rate = growth_rate
        self.selected_days = selected_days
        self.scenes = scenes
        
        ##m_s_base = [{'y': 0, 'd': 0, 'dd':1.0, 'h': 0.0, 'dt': 1.0, 'temp': 20.0, 'I':1000.0, 'wv': 10.0, 'eg': 1.0}]
        
    def build_scenes(self):
        raise Exception("Must Implement")
        return 