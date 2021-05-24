from .BaseGen import Generator, DiscreteGenerator


def wind_output(model_status={}):
    #modelo sencillo
    #devuelvr la fracción de la potencia entregada en función del tiempo
    #no toma en cuenta la radicación solar ni la temperatura
    res = 0.0
    if 'wv' in model_status:
        wv = model_status['wv']
        if 0.0 <= wv and wv < 3.0:
            res = 0.0
        elif 3.0 <= wv and wv < 15.0:
            res = (wv-3.0)/(15.0-3.0)
        elif 15.0 <= wv and wv < 25.0:
            res = 1.0
        else:
            res = 0.0
    else:
        raise ValueError("Wind Velocity not defined")
    
    return res

class WTGenerator(Generator):
    def __init__(self, name):
        super().__init__(name)
        
        self['pa_pu'] = wind_output
        
class WTGeneratorDiscrete(DiscreteGenerator):

    def __init__(self, name):
        super().__init__(name)
        
        self['pa_pu'] = wind_output
