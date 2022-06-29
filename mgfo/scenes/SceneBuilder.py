import pandas as pd
import numpy as np
import math

from ..simulation import Economics
from ..simulation import Solar
from ..simulation import Wind


class SceneBuilder:
    """
    SceneBuilder class
    
    Based on description of the period of analysis for the target microgrid, SceneBuilder lets
    construct a Pandas DataFrame with a instant by instant description of the conditions, called *scene*.
    
    Each scene has the following attributes:
    
        year: Year of analysis. Can be 0 index or calendary year.
        day: Day of the year under analysis. From 0 (Jan 1st) to 365.
        dd: Number of simulated repeated days. See *dt*.
        hour: Hour of the day. Can be a fractional hour.
        dt: Delta of time for this scene, in hours or fraction.
        discount: Discount for future costs.
        growth: A coefficient that represents demand growth rate
        temperature: Temperature at the moment.
        solar_irradiance: Solar irradiance, in W/m^2, at the moment.
        wind_speed: Wind speed at the moment in m/s.
        
    Basic usage consists to specify simulation parameters using several methods and then to use
    the *build_scenes* method to return a DataFrame with the simulated scenes. An existant object that
    support dict interface can be used instead a DataFrame by setting the scenes member.
    
    Days can be specified in two ways:
        -Using a selectec collection of days, using the selected_days parameter with an array of days.
        In this case the dd parameter multiplies all daily-related quantities without change as given
        -Using the subperiods argument: n subperiods are extracted for the year, equally-spaced, of 
        *days_in_subperiods* days each. In this case, dd = 365/(subperiods*days_in_subperiods)
        First subperiod starts as given by *subperiod_start*
    """
    
    def __init__(self, years=1, subperiods=1, days_in_subperiods=365, subperiod_start=0, dd=None,  dt=None, discount_rate=0.0, growth_rate=0.0, 
                selected_days = None, selected_hours = None, scenes = None):
        self.years = years
        self.subperiods = subperiods
        self.subperiod_start = subperiod_start
        self.days_in_subperiods = days_in_subperiods
        self.discount_rate = discount_rate
        self.growth_rate = growth_rate
        self.selected_days = selected_days
        self.selected_hours = selected_hours
        self.scenes = scenes
        
        if selected_days and not dd:
            raise Exception("dd must be specified when using selected_days")

        if selected_hours and not dt:
            raise Exception("dt must be specified when using selected_days")
        
        if not dt:
            self.dt = 1.0
        else:
            self.dt = dt

        if not dd:
            self.dd = 1.0
        else:
            self.dd = dd
        
        self.additional_columns = {}
        
        self.add_standard_columns()
        
    def add_column(self, name, generator):
        self.additional_columns[name] = generator
    
    def add_standard_columns(self):
        dg = Economics.DeterministicGrowthSimulator(annual_rate = self.growth_rate)
        self.add_column('growth', dg)

        disc = Economics.PVSimulator(annual_rate = self.discount_rate)
        self.add_column('discount', disc)

        solar = Solar.SolarIrradianceSimulator()
        self.add_column('solar_irradiance', solar)
        
        wind = Wind.CorrelatedWeibull()
        self.add_column('wind_speed', wind)
        
    def build_scenes(self):
        """Escene building is made in two steps. First, the time part is resolved.
        In the second part, the data list with additional columns is iterated and the corresponding simulation
        functions are called in order to complete each scene"""
        column_list = {}

        if self.selected_hours:
            hours_array = self.selected_hours
            daily_registers = len(self.selected_hours)
        else:
            daily_registers = math.floor(24.0/self.dt)
            hours_array = [self.dt*i for i in range(daily_registers)]
        
        #We made an array for the selected days in the year, based on the user choices
        if self.selected_days:
            days = len(self.selected_days)
            days_array = self.selected_days
        else:
            day_number = self.subperiod_start
            subperiod_jump = math.floor(365/self.subperiods)
            days_array = []
            for s in range(self.subperiods):
                for sd in range(self.days_in_subperiods):
                    days_array.append(day_number)
                    day_number += 1
                day_number += (subperiod_jump - self.days_in_subperiods)
                
            days = len(days_array)
            self.dd = 365.0/days
            
        total_registers = self.years * days * daily_registers

        reg = 0
        #Accessing pandas data frames are painfully slow.
        #columns are stored in numpy arrays and later transferred to the data frame
        days = np.zeros(total_registers)
        hours = np.zeros(total_registers)
        years = np.zeros(total_registers)
        
        for y in range(self.years):
            for d in days_array:
                for h in hours_array:
                    days[reg] = d
                    hours[reg] = h
                    years[reg] = y 
                    reg += 1

        column_list['year'] = years
        column_list['day'] = days
        column_list['dd'] = np.ones(total_registers)*self.dd
        column_list['hour'] = hours
        column_list['dt'] = np.ones(total_registers)*self.dt
        
        #Auxiliary function
        def get_scene_from_cl(cl, i):
            res = {}
            for k in cl:
                res[k] = cl[k][i]
            return res
        
        for col in self.additional_columns:
            values = np.zeros(total_registers)
            simulator = self.additional_columns[col].simulate
            for i in range(total_registers):
                values[i] = simulator(get_scene_from_cl(column_list, i))
            column_list[col] = values
        
        scenes =  pd.DataFrame(column_list)
        self.scenes = scenes
        
        return scenes