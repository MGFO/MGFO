import math
import random

def solar_irradiance_seasoned_randomized(d, h):
    #simula las horas de sol, la intensidad y los dias multiplos de 5 esta nublado, con un 20% de la radiacion
    #a todo esto se le aplica una aleatoriedad del 80 al 100%
    #los coeficientes son aproximados para Buenos Aires
    radiacion = 1000.0
    
    estacionalidad = 0.75 + 0.25*math.cos((d + 10.0)/365.0*2*math.pi)  
    
    if d % 5 == 0 :
        nubosidad = 0.2
    else:
        nubosidad = 1.0
        
    aleatoriedad = random.uniform(0.8, 1.0)
    
    salida = 7.0 - 1.1*math.cos((d + 10.0)/365.0*2*math.pi)    #es una aproximacion, no basada en modelos matematicos
    puesta = 19.0 + 1.1*math.cos((d + 10.0)/365.0*2*math.pi)
    
    temporalidad = 0.0
    if salida <= h and h <= puesta:
        temporalidad = math.sin((h-salida)/(puesta-salida)*math.pi)
        
    return radiacion*estacionalidad*nubosidad*aleatoriedad*temporalidad