import random
import math

class BaseSimulator:
    """
    Base simulator class. Defines an interface for all simulators (Wind, Solar, Temperature, Demand, Prices, etc.)
    Defines several models for simulation, for example, constant, time-linear, exponential, piecewise, etc.
    """
    
    def __init__(self, model='constant', post_random_up=0.2, post_random_down=0.2, post_random_model='uniform'):
        self.model = model
        self.post_random_up = post_random_up
        self.post_random_down = post_random_down
        self.post_random_model = post_random_model
        self.base_value = 1.0
        self.a_yearly = 1.0
        self.a_monthly = 1.0
        self.a_hourly = 1.0
        self.a_daily = 1.0
        
        #value is the fraction up to the same-index hour.
        self.piecewise_hours =  [ 7.0, 12.0, 16.0, 20.0, 24.0]
        self.piecewise_values = [0.15, 0.25, 0.40, 0.60, 1.0 ]
        
        self.models = {}
        self.init_models()
    
    def init_models(self):
        self.models['constant'] = self.model_constant
        self.models['linear'] = self.model_linear
        self.models['piecewise'] = self.model_piecewise
        self.models['exponential'] = self.model_exponential
        
    
    def model_constant(self, scene):
        return self.base_value
        
    def model_linear(self, scene):
        #if there is a key error, an Exception will be raised. This is intentional.
        month = math.floor(scene['day']/30)
        month = 11 if month > 12 else month
        return self.base_value + self.a_hourly*scene['hour'] + self.a_daily*scene['day'] + self.a_monthly*month + self.a_yearly*scene['year']
    
    def model_piecewise(self, scene):
        h = scene['hour']
        v = self.piecewise_values[0]
        for i in range(len(self.piecewise_hours)):
            if h < self.piecewise_hours[i]:
                v = self.piecewise_values[i]
                break
        return v
    
    def model_exponential(self, scene):
        return math.exp(self.model_linear(scene))
        
    def post_value_random(self):
        if self.post_random_model == 'none' or self.post_random_model == None or self.post_random_model == False:
            return 1.0
        elif self.post_random_model == 'uniform':
            return random.uniform(1.0 - self.post_random_down, 1.0 + self.post_random_up)
        elif self.post_random_model == 'gauss':
            return random.gauss(1 + 0.5*self.post_random_up -0.5*self.post_random_down, 0.5*(self.post_random_up+self.post_random_down))
        else:
            raise Exception("Post random model {0} not supported".format(self.post_random_model))
        
    def simulate(self, scene):
        """
        Returns a simulated value for the current scene.
        The simulated value can be function of other scene's values, for example, demand can be function
        of the temperature.
        
        Independent of the simulated value, a random step is applied in order to simplify simulations.
        """
        if self.model in self.models:
            val = self.models[self.model](scene)
        else:
            raise Exception("Model {0} not supported".format(self.model))
        
        return val*self.post_value_random()
        
