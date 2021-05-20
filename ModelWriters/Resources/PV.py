from .BaseGen import Generator

class PVGenerator(Generator):
    
    def solar_output(model_status={}):
        #modelo sencillo
        #usando los datos de radiacion solar entregada por el modelo
        #considero el valor normal 1000 W/m2
        res = 0.0
        if 'I' in model_status:
            I = model_status['I']
            if 0.0 <= I and I < 1200:
                res = I / 1000.0
            else:
                raise ValueError("Solar radiation outside model range")
        else:
            raise ValueError("Solar radiation not defined")
        return res
    
    def __init__(self, name):
        super().__init__(name)
        
        self['pa_pu'] = self.solar_output
        