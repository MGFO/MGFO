from .BaseGen import Generator, DiscreteGenerator


class PVGenerator(Generator):
    
    def __init__(self, name, ic_0_mu = 0.0, ic_1_mu = 0.0, oc_0_mu = 0.0, oc_1_mu = 0.0, degradation = 5e-3):
        super().__init__(name, ic_0_mu = ic_0_mu, ic_1_mu = ic_1_mu, oc_0_mu = oc_0_mu, oc_1_mu = oc_1_mu)
        
        self.degradation = degradation
        self['pa_pu'] = self.solar_output
        
    def solar_output(self, model_status):
        #modelo sencillo
        #usando los datos de radiacion solar entregada por el modelo
        #considero el valor normal 1000 W/m2
        res = 0.0
        degradation = 1 - self.degradation*model_status['year']
        if 'solar_irradiance' in model_status:
            I = model_status['solar_irradiance']
            if 0.0 <= I and I < 1300:
                res = I / 1000.0 * degradation
            else:
                raise ValueError("Solar radiation outside model range")
        else:
            raise ValueError("Solar radiation not defined")
        return res
        
class PVGeneratorDiscrete(DiscreteGenerator):
    
    def solar_output(self, model_status):
        #modelo sencillo
        #usando los datos de radiacion solar entregada por el modelo
        #considero el valor normal 1000 W/m2
        res = 0.0
        if 'I' in model_status:
            I = model_status['I']
            if 0.0 <= I and I < 1300:
                res = I / 1000.0
            else:
                raise ValueError("Solar radiation outside model range")
        else:
            raise ValueError("Solar radiation not defined")
        return res
    
    def __init__(self, name, unit_size_mw = 0.25, unit_cost_mu = 1.0, oc_0_mu = 0.0, oc_1_mu = 0.0, degradation = 5e-3):
        super().__init__(name, unit_size_mw = unit_size_mw, unit_cost_mu = unit_cost_mu, oc_0_mu = oc_0_mu, oc_1_mu = oc_1_mu)
        
        self.degradation = degradation
        self['pa_pu'] = self.solar_output
        
    def solar_output(self, model_status):
        #modelo sencillo
        #usando los datos de radiacion solar entregada por el modelo
        #considero el valor normal 1000 W/m2
        res = 0.0
        degradation = 1 - self.degradation*model_status['year']
        if 'solar_irradiance' in model_status:
            I = model_status['solar_irradiance']
            if 0.0 <= I and I < 1200:
                res = I / 1000.0 * degradation
            else:
                raise ValueError("Solar radiation outside model range")
        else:
            raise ValueError("Solar radiation not defined")
        return res
