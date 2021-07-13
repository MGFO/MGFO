from .BaseModel import BaseModelWriter
import pyomo.environ as pe
import itertools
import numpy as np

class SimpleModelWriter(BaseModelWriter):
    
    def power_balance_expression(self, scene_index): #scene is the scene index
        ##Test what happend with some network without a type, for example, no ext grid.
        #return the power balance for the selected scene:
        pb = 0.0
        for table in self.tables:
            pt = 0.0
            for element in range(len(table)):
                if table['model'][element]:
                    pt += table['model'][element].active_power(scene_index)
            pb += pt
        return pb

    def power_balance_constraint(self):
        #power balance constraint
        scene_iterator = range(len(self.scenes))
        self.model.power_balance_constraint = pe.Constraint(scene_iterator, 
                                    rule = (lambda m, s:  self.power_balance_expression(s) == 0))        

    def investement_constraint(self):
        if not self.max_investement is None:
            self.model.max_investement_constraint = pe.Constraint(expr = self.initial_cost_expression() <= self.max_investement)
        
    def initial_cost_expression(self):
        c = 0.0
        for table in self.tables:
            ct = 0.0
            for element in range(len(table)):
                if table['model'][element]:
                    ct += table['model'][element].initial_cost()
                if isinstance(ct, np.float64):
                    ct = float(ct)
            try:
                c += ct
            except Exception:
                raise Exception("c: {0} ct:{1}".format(c.__class__, ct.__class__))
        return c



    def hourly_operational_cost_expression(self, scene_index):
        ## generalizar este codigo
        c = 0.0
        for table in self.tables:
            ct = 0.0
            for element in range(len(table)):
                if table['model'][element]:
                    ct += table['model'][element].operating_cost(scene_index)
            c += ct
        return c
    
    def operational_cost_expression(self):
        scene_iterator = range(len(self.scenes))
        
        op_cost = sum(self.hourly_operational_cost_expression(e)*self.scenes['dt'][e]*self.scenes['dd'][e]*self.scenes['discount'][e] for e in scene_iterator)
        return op_cost
    
    def objective_function(self):
        self.model.value = pe.Objective( expr = self.initial_cost_expression() + self.operational_cost_expression(), sense = pe.minimize )
        return self.model.value

    def initialize_submodels(self):

        for table in self.tables:
            for element in range(len(table)):
                if table['model'][element]:
                    table['model'][element].initialize_model(self.model, self.scenes)
    
        return self.model
    
    def create_model(self):
        if not self.net:
            raise Exception("Network not provided")
        
        if self.scenes is None:
            raise Exception("Scenes not provided")
        
        #involved tables are append. All code uses the tables array as reference
        model_tables = [self.net.ext_grid, self.net.load, self.net.sgen, self.net.storage]

        for t in model_tables:
            self.tables.append(t)

        if not self.model:
            self.model = pe.ConcreteModel()
        
        self.initialize_submodels()
        
        #power balance constraint
        self.power_balance_constraint()
        
        #max investement constraint:
        self.investement_constraint()
        
        self.objective_function()
        
        return self.model
        
