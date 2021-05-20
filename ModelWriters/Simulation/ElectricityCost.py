
def fixed_scalonated_electricity_cost(model_status={}):
    #modelo sencillo con dos precios, uno entre 0 a 18 y otro de 18 a 24
    res = 0.0
    sx = 1e-6
    if 'h' in model_status:
        h = model_status['h']
        if 0.0 <= h and h < 18.0:
            res = 3600.0*sx
        elif 18 <= h and h < 24.0:
            res = 5400.0*sx
        else:
            raise ValueError("Hour outside model range")
    else:
        raise ValueError("Hour not defined")
    
    return res

#test:
#m_s = {'y': 0, 'd': 180, 'h': 14.0, 'dt': 1.0, 'temp': 12.0, 'wv': 10.0, 'eg': 1.0}

#oc_1_ext_grid(m_s)

#25 hs: error
#m_s['h'] = 25
#oc_1_ext_grid(m_s)