from .BaseGen import Generator, DiscreteGenerator

class WTGenerator(Generator):
    def __init__(self, name, ic_0_mu = 0.0, ic_1_mu = 0.0, oc_0_mu = 0.0, oc_1_mu = 0.0, cut_in = 3.0, v_rated = 15.0, cut_out = 25.0):
        super().__init__(name, ic_0_mu = ic_0_mu, ic_1_mu = ic_1_mu, oc_0_mu = oc_0_mu, oc_1_mu = oc_1_mu)
        
        self.cut_in = cut_in
        self.v_rated = v_rated
        self.cut_out = cut_out
        self['pa_pu'] = self.wind_output
    
    def wind_output(self, scene):
        res = 0.0
        if 'wind_speed' in scene:
            wv = scene['wind_speed']
            if 0.0 <= wv and wv < self.cut_in:
                res = 0.0
            elif self.cut_in <= wv and wv < self.v_rated:
                res = (wv**3 - self.cut_in**3)/(self.v_rated**3 - self.cut_in**3)
            elif self.v_rated <= wv and wv < self.cut_out:
                res = 1.0
            else:
                res = 0.0
        else:
            raise ValueError("Wind speed not defined")

        return res
        
        
class WTGeneratorDiscrete(DiscreteGenerator):

    def __init__(self, name, unit_size_mw = 0.25, unit_cost_mu = 1.0, ic_0_mu = 0.0, oc_0_mu = 0.0, oc_1_mu = 0.0, 
                 cut_in = 3.0, v_rated = 15.0, cut_out = 25.0):
        super().__init__(name, unit_size_mw = unit_size_mw, unit_cost_mu = unit_cost_mu, ic_0_mu = ic_0_mu, oc_0_mu = oc_0_mu, oc_1_mu = oc_1_mu)
        
        self.cut_in = cut_in
        self.v_rated = v_rated
        self.cut_out = cut_out
        self['pa_pu'] = self.wind_output
        
    def wind_output(self, scene):
        res = 0.0
        if 'wind_speed' in scene:
            wv = scene['wind_speed']
            if 0.0 <= wv and wv < self.cut_in:
                res = 0.0
            elif self.cut_in <= wv and wv < self.v_rated:
                res = (wv**3 - self.cut_in**3)/(self.v_rated**3 - self.cut_in**3)
            elif self.v_rated <= wv and wv < self.cut_out:
                res = 1.0
            else:
                res = 0.0
        else:
            raise ValueError("Wind speed not defined")

        return res