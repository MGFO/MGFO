import math
import random

from .BaseSimulator import BaseSimulator as BS

class DeterministicGrowthSimulator(BS):
    """
    class DeterministicGrowthSimulator
    Strictly not a simulator, but shares the same interface.
    Simulates exponential growth, where growth rates can be expressed at daily, monthly and annual values
    in per unit. An arbitrary base value can be used also.
    Post-randomization is disabled by default, but can be enabled using the *post_random_model* attribute.
    """
    def __init__(self, base = 1.0, annual_rate = 0.1, monthly_rate = 0.0, daily_rate = 0.0):
        """
        Inits a new Net Present Value simulator class.
        Given a future time, expressed in years and days, returns the present value ratio.
        Values are stored as logarithmic representations.
        """
        
        super().__init__(model='exponential', post_random_model='none')
        self.base_value = math.log(base)
        self.a_yearly = math.log(1+annual_rate) + 12*math.log(1+monthly_rate) + 365*math.log(1+daily_rate)
        self.a_monthly = math.log(1+monthly_rate)
        self.a_daily = math.log(1+daily_rate)
        self.a_hourly = 0.0

    @property
    def base(self):
        return math.exp(self.base_value)
    
    @base.setter
    def base(self, value):
        self.base_value = math.log(1+value)
        
    @base.deleter
    def base(self):
        raise Exception("Deletion not supported")

    @property
    def annual_rate(self):
        return math.exp(self.a_yearly)-1
    
    @annual_rate.setter
    def annual_rate(self, value):
        self.a_yearly = math.log(1+value)
        
    @annual_rate.deleter
    def annual_rate(self):
        raise Exception("Deletion not supported")

    @property
    def monthly_rate(self):
        return math.exp(self.a_monthly)-1
    
    @monthly_rate.setter
    def monthly_rate(self, value):
        """
        Monthly rate setter. 
        Be careful that also updates the annual rate.
        """
        self.a_monthly = math.log(1+value)
        self.a_yearly += 12*self.a_monthly
        
    @monthly_rate.deleter
    def monthly_rate(self):
        raise Exception("Deletion not supported")

    @property
    def daily_rate(self):
        return math.exp(self.a_daily)-1
    
    @daily_rate.setter
    def daily_rate(self, value):
        """
        Daily rate setter. 
        Be careful that also updates the annual rate.
        """
        self.a_daily = math.log(1+value)
        self.a_yearly += 365*self.a_daily
        
    @daily_rate.deleter
    def daily_rate(self):
        raise Exception("Deletion not supported")
    

class PVSimulator(DeterministicGrowthSimulator):
    """
    class PVSimulator
    Calculates the present value of a thing respect a time in the future.
    The base value is interpreted as that value.
    Derived from DeterministicGrowthSimulator
    """

    def simulate(self, scene):
        """
        Uses the simulate offered by the base class, then decreases the base instead of increase
        """
        val = super().simulate(scene)
        base = math.exp(self.base_value)
        rate = val/base
        return base/rate


class ElectricityCostSimulator(BS):
    """
    An piecewise-based model for electricity prices.
    A model based in peak, valley and rest zones is used, deterministic.
    By default, 23-6 are valley hours, 6-18 are rest hours and 18-23 are peak hours.
    This can be changed by the use of the *piecewise_hours* member.
    """
    def __init__(self, peak_value=0.20e3, valley_value=0.12e3, rest_value=0.16e3):
        super().__init__(model='piecewise', post_random_model='none')
        self.piecewise_hours = [6.0, 18.0, 23.0, 24.01]
        self.piecewise_values = [valley_value, rest_value, peak_value, valley_value]
