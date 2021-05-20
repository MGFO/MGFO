

def scalonated_seasoned_randomized_demand(model_status={}):
    #modelo sencillo en forma de escalones
    #devuelvr la fracción de la carga empleada
    #se considera que la carga tiene una variabilidad aleatoria de un 20% y es mayor en verano e invierno en un 30%
    #la variabilidad total puede ser 1.3*1.2=1.56 verano-invierno o 0.7*0.8 = 0.56 otoño-primavera, 
    res = 0.0
    if 'h' in model_status:
        h = model_status['h']
        if 0.0 <= h and h < 6.0:
            res = 0.2
        elif 6.0 <= h and h < 8.0:
            res = 0.4
        elif 8.0 <= h and h < 18.0:
            res = 0.5
        elif 18.0 <= h and h < 22.0:
            res = 1.0
        elif 22.0 <= h and h < 24.0:
            res = 0.3            
        else:
            raise ValueError("Hour outside model range")
    else:
        raise ValueError("Hour not defined")
    
    #estacionalidad
    if 'd' in model_status:
        d = model_status['d']
        #se asume que el día de mayor consumo es el inicio del verano y del invierno (21/12 y 21/07), por eso sumo 10 días el dia 0
        #divido por 180 porque hay dos picos en el año y paso a radianes
        estacionalidad = 1 + 0.3*math.cos((d + 10.0)/180.0*2*math.pi)  
    else:
        raise ValueError("Day not defined")
    res = res * estacionalidad
    
    #Aleatoriedad:
    res = res*random.uniform(0.8, 1.2)
    return res