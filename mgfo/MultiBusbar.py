from .SimpleBusbar import SimpleModelWriter
from .Resources.SimpleLine import SimpleLine

import pyomo.environ as pe
import itertools
import pandas as pd
import numpy as np

from warnings import warn

class MultiBusbarModelWriter(SimpleModelWriter):
    
    def __init__(self, net = None, scenes = None, overload_cost = None, overload_hours =  None, max_i_pu = 1.5):
        super().__init__(net = net, scenes = scenes)
        
        self.overload_cost = overload_cost
        self.overload_hours = overload_hours
        self.max_i_pu = max_i_pu
    
    
    def add_power_lines(self):
        """Attaches a SimpleLine optimization model for each unmodeled line"""
        
        #'model' attribute may not be present:
        if not hasattr(self.net.line, 'model'):
            self.net.line['model'] = None
            
        for e in range(len(self.net.line)):
            
            if not self.net.line.model[e]:
                m = SimpleLine('', '', overload_hours = self.overload_hours, overload_cost = self.overload_cost, max_i_pu = self.max_i_pu)
                m.from_bus = self.net.line.from_bus[e]
                m.to_bus = self.net.line.to_bus[e]
                                
                f = self.net.bus.name[m.from_bus]
                f = str(m.from_bus) if not f else f
                t = self.net.bus.name[m.to_bus]
                t = str(m.to_bus) if not t else t
                
                name ='L ' + f + '_' + t
                m.name = name
                
                m.ir_ka = self.net.line.max_i_ka[e]
                m.vn_kv = self.net.bus.vn_kv[m.from_bus]
                
                m.pr_mw = 1.73205080 * m.ir_ka * m.vn_kv
                                
                self.net.line.model[e] = m
    
    def bus_power_balance_expression(self, b_index: int, scene: int):
        power = 0.0
        for table in self.tables:
            if hasattr(table, 'bus') and hasattr(table, 'model'):
                for element in range(len(table)):
                    if table.bus[element] == b_index and table.model[element]:
                        power += table.model[element].active_power(scene)
            if hasattr(table, 'from_bus') and hasattr(table, 'to_bus') and hasattr(table, 'model'):
                #power lines
                for element in range(len(table)):
                    #departing line rest power
                    if table.from_bus[element] == b_index and table.model[element]:
                        power += table.model[element].transmited_power(scene)
                    #arriving line discounts power
                    if table.to_bus[element] == b_index and table.model[element]:
                        power -= table.model[element].transmited_power(scene)
        return power
    
    def busbars_balance_constraints(self):
        """For each busbar a constraint is added to balance power"""
        #scene_iterator = range(len(self.scenes))        
        #bus_iterator = range(len(self.net.bus))
        self.model.bus_set = pe.Set(initialize = range(len(self.net.bus)))
   
        self.model.busbar_power_balance_constraint = pe.Constraint(self.model.bus_set, self.model.scene_set, 
                                    rule = (lambda m, bus, scene:  self.bus_power_balance_expression(bus, scene) == 0))    
        
    def create_model(self):
        if not self.net:
            raise Exception("Network not provided")
        
        if self.scenes is None:
            raise Exception("Scenes not provided")
        
        #involved tables are append. All code uses the tables array as reference
        model_tables = [self.net.ext_grid, self.net.load, self.net.sgen, self.net.storage, self.net.line]

        for t in model_tables:
            self.tables.append(t)

        if not self.model:
            self.model = pe.ConcreteModel()
        
        self.model.scenes = self.scenes
        self.model.scene_set = pe.Set(initialize = range(len(self.scenes)), doc = 'Scenes')
        
        #add models for unmodeled lines
        self.add_power_lines()
        
        self.initialize_submodels()
        
        #self.power_balance_constraint()
        
        self.busbars_balance_constraints()
        
        self.objective_function()
        
        return self.model
    