import random
import math

class BaseSimulator:
    """
    Base simulator class. Defines an interface for all simulators (Wind, Solar, Temperature, Demand, Prices, etc.)
    Defines several models for simulation, for example, constant, time-linear, exponential, piecewise, etc.
    """
    
    def __init__(self, model='constant', base_value = 1.0, post_random_up=0.2, post_random_down=0.2, post_random_model='uniform',
                a_yearly = 1.0, a_monthly = 1.0, a_hourly = 1.0, a_daily = 1.0, piecewise_hours = [ 7.0, 12.0, 16.0, 20.0, 24.0],
                piecewise_values = [0.15, 0.25, 0.40, 0.60, 1.0 ]):
        self.model = model
        self.post_random_up = post_random_up
        self.post_random_down = post_random_down
        self.post_random_model = post_random_model
        self.base_value = base_value 
        self.a_yearly = a_yearly
        self.a_monthly = a_monthly
        self.a_hourly = a_hourly
        self.a_daily = a_daily
        
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
    
    def select_piecewise(self, hour, domain, values):
        v = values[0]
        for i in range(len(domain)):
            if hour < domain[i]:
                v = values[i]
                break
        return v
        
    def model_piecewise(self, scene):
        h = scene['hour']
        return self.select_piecewise(h, self.piecewise_hours, self.piecewise_values)

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
        
class DailyInterpolator(BaseSimulator):
    
    def __init__(self, base_value = 1.0, post_random_up=0.2, post_random_down=0.2, post_random_model='uniform'):
        super().__init__()
        
        self.model = 'daily_interpolation'
        self.models['daily_interpolation'] = self.model_daily_interpolation
        
        self.post_random_up = post_random_up
        self.post_random_down = post_random_down
        self.post_random_model = post_random_model
        self.base_value = base_value 

        self.data_days = {}   #key is the day of the data, value must be a dict hours: [], values: []
        
    def add_day(self, day, hours, values):
        """
        add_day
        Adds a new day as data, for example, 81st day of the year
        with an hourly data specified as 12 2-hour steps, with 12 values.
        Days must be ordered!!!
        """
        
        self.data_days[day] = {'hours': hours, 'values': values}
        
    def model_daily_interpolation(self, scene):
        
        day = scene['day']
        hour = scene['hour']
        
        ds = [k for k in self.data_days.keys()]
        
        l = len(ds)
        
        if l == 0:
            raise Exception("No data")
        elif l == 1:
            #no interpolation possible, defaults to piecewise
            domain = self.data_days[ds[0]]['hours']
            values = self.data_days[ds[0]]['values']
            return self.select_piecewise(hour, domain, values)
        else:
            #we must extend the array of days in order to simplify the search for 
            #the correct interval
            ds.insert(0, ds[-1] - 365)
            ds.append(ds[1] + 365)  #the old fist now is the 1st            
            
            #print(ds)
            
            #We must find the next day in the domain 
            found = False
            i = 0
            
            while (not found) and i <= l:   #the unusual = is because data was added 
                prev_day = ds[i]
                next_day = ds[i+1]
                                
                if prev_day <= day and day <= next_day:
                    found = True
                else:
                    i += 1

            if not found:
                raise Exception("Day not found in interval")
                
            #print("Prev Day: {0} Next_day: {1}".format(prev_day, next_day))
            if prev_day < 0:
                prev_day_data = self.data_days[prev_day + 365]
            else:
                prev_day_data = self.data_days[prev_day]
            prev_day_value = self.select_piecewise(hour, prev_day_data['hours'], prev_day_data['values'])
            
            if next_day > 365:
                next_day_data = self.data_days[next_day - 365]
            else:
                next_day_data = self.data_days[next_day]
            next_day_value = self.select_piecewise(hour, next_day_data['hours'], next_day_data['values'])
            
            #finally, the interpolation:
            
            return prev_day_value + (next_day_value - prev_day_value)/(next_day - prev_day)*(day - prev_day)
