import math
import random

from .BaseSimulator import BaseSimulator as BS

class SolarIrradianceSimulator(BS):
    """
    summer_sunrise_advance is the advancement of sunrise time in summer
    """
    
    def __init__(self, max_irradiation = 1000.0, summer_sunrise_advance = 1.1, cloudy_days = 0.15, post_random_up = 0.03, post_random_down = 0.03):
        super().__init__(model = 'solar_plus_clouds', 
                         post_random_up = post_random_up, post_random_down = post_random_down)     
    
        self.base_value = max_irradiation
        self.models['solar_plus_clouds'] = self.model_solar_plus_clouds
        self.summer_sunrise_advance = summer_sunrise_advance
        self.cloudy_days = cloudy_days
        #cloud status perseverance
        self.current_day = None
        self.current_day_cloudy = False
        self.current_day_cloud_density = 1.0
    
    def model_solar_plus_clouds(self, scene):
        
        d = scene['day']
        h = scene['hour']
        if self.current_day != d:
            self.current_day = d
            if random.uniform(0,1) < self.cloudy_days:
                self.current_day_cloudy = True
                self.current_day_cloud_density = random.uniform(0.2, 0.6)
            else:
                self.current_day_cloudy = False
                self.current_day_cloud_density = 1.0
        
        radiation = self.base_value

        variation = 0.75 - 0.25*math.cos((d + 10.0)/365.0*2*math.pi)  

        sunrise = 7.0 + self.summer_sunrise_advance*math.cos((d + 10.0)/365.0*2*math.pi)    #es una aproximacion, no basada en modelos matematicos
        sunset = 19.0 - self.summer_sunrise_advance*math.cos((d + 10.0)/365.0*2*math.pi)

        tempo = 0.0
        
        if sunrise <= h  and h <= sunset:
            tempo = math.sin((h-sunrise)/(sunset-sunrise)*math.pi)

        return radiation*variation*self.current_day_cloud_density*tempo
    
class MonthlySolarIrradianceSimulator(BS):

    
    def __init__(self, latitude = -34.6037, longitude = -58.3814, post_random_up = 0.1, post_random_down = 0.1,
                monthly_average_irradiation = None):
        super().__init__(model = 'solar_monthly', 
                         post_random_up = post_random_up, post_random_down = post_random_down)     
    
        self.base_value = 1000.0
        self.latitude = latitude
        self.longitude = longitude
        self.models['solar_monthly'] = self.model_solar_monthly
        self.monthly_average_irradiation = monthly_average_irradiation
        #cloud status perseverance
        self.current_day = None
        self.current_day_opacity = 1.0
        self.monthly_coefficients = [0.75 for i in range(12)]
        
        
        if monthly_average_irradiation:
            self.set_monthly_coefficients(monthly_average_irradiation)
    
    def calculate_sunrise_sunset(self, lat, long, day = 355, sunrise = True, text = False):
        zenith = 90.83333333333333
        D2R = math.pi / 180
        R2D = 180 / math.pi

        #convert the longitude to hour value and calculate an approximate time
        lnHour = long / 15.0
        if sunrise:
            t = day + ((6 - lnHour) / 24.0)
        else:
            t = day + ((18 - lnHour) / 24.0)

        #calculate the Sun's mean anomaly
        M = (0.9856 * t) - 3.289;

        #calculate the Sun's true longitude
        L = M + (1.916 * math.sin(M * D2R)) + (0.020 * math.sin(2 * M * D2R)) + 282.634;
        if L > 360:
            L = L - 360
        elif L < 0:
            L = L + 360

        #calculate the Sun's right ascension
        RA = R2D * math.atan(0.91764 * math.tan(L * D2R));
        if RA > 360:
            RA = RA - 360
        elif RA < 0:
            RA = RA + 360

        #right ascension value needs to be in the same qua
        Lquadrant = (math.floor(L / (90))) * 90
        RAquadrant = (math.floor(RA / 90)) * 90
        RA = RA + (Lquadrant - RAquadrant)

        #right ascension value needs to be converted into hours
        RA = RA / 15

        #calculate the Sun's declination
        sinDec = 0.39782 * math.sin(L * D2R)
        cosDec = math.cos(math.asin(sinDec))

        #calculate the Sun's local hour angle
        cosH = (math.cos(zenith * D2R) - (sinDec * math.sin(lat * D2R))) / (cosDec * math.cos(lat * D2R))
        if sunrise:
            H = 360 - R2D * math.acos(cosH)
        else:
            H = R2D * math.acos(cosH)
        H = H / 15

        #calculate local mean time of rising/setting
        T = H + RA - (0.06571 * t) - 6.622

        #adjust back to UTC
        UT = T - lnHour
        if UT > 24:
            UT = UT - 24
        elif UT < 0:
            UT = UT + 24

        #convert UT value to local time zone of latitude/longitude
        offset = (int)(long / 15.0)   # estimate utc correction
        localT = UT + offset  # -5 for baltimore

        if text:
            h = math.floor(localT)
            frac = localT - h
            m = math.floor(frac*60)
            res = "{0}:{1}".format(h, m)
        else:
            res = localT

        return res

    
    def set_monthly_coefficients(self, monthly_average_irradiation):
        """Calculates the coefficients for solar radiation so the synthetized coincides
        with the monthly average for the site."""
        #mid month days:
        mid_month_days = [15 + math.floor(365.0/12.0*i)  for i in range(12)]
        self.model_a = 0.2   #minimmum solar radiation possible.
        self.model_c = []    #mode of triangular distribution
        self.model_b = 1.0   #max. solar radiation possible.
        
        for i in range(12):
                init = math.ceil(self.calculate_sunrise_sunset(self.latitude, self.longitude, day = mid_month_days[i]))
                endt = math.floor(self.calculate_sunrise_sunset(self.latitude, self.longitude, day = mid_month_days[i], sunrise = False))
                irradiation = 0.0
                
                for h in range(init, endt):
                    irradiation += self.base_value * math.sin((h - init)/(endt - init)*math.pi)
                
                self.monthly_coefficients[i] = monthly_average_irradiation[i] / irradiation
                
                self.model_c.append( 3*self.monthly_coefficients[i] - self.model_a - self.model_b)

    def simulate_day_coefficient(self, day):
        """A triangular pdf is used here"""
        
        month = math.floor(day/366*12)
        res = 1.500
        while res > 1.100:
            res =random.triangular(self.model_a, self.model_b, self.model_c[month])
        
        return res
    
    def model_solar_monthly(self, scene):
        
        d = scene['day']
        h = scene['hour']
        if self.current_day != d:
            self.current_day = d
            self.current_day_opacity = self.simulate_day_coefficient(d)
        
        sunrise = math.ceil(self.calculate_sunrise_sunset(self.latitude, self.longitude, day = d))
        sunset = math.floor(self.calculate_sunrise_sunset(self.latitude, self.longitude, day = d, sunrise = False))
        
        if sunrise <= h  and h <= sunset:
            tempo = math.sin((h-sunrise)/(sunset-sunrise)*math.pi)
        else:
            tempo = 0.0
        
        radiation = self.base_value

        return radiation*self.current_day_opacity*tempo