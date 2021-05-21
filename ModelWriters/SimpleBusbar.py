from .BaseModel import BaseModelWriter
import pyomo.environ as pe
import itertools
import pandas as pd
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


    def initial_cost_expression(self):
        c = 0.0
        for table in self.tables:
            ct = 0.0
            for element in range(len(table)):
                if table['model'][element]:
                    ct += table['model'][element].initial_cost()
            c += ct
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
        
        op_cost = sum(self.hourly_operational_cost_expression(e)*self.scenes['dt'][e] for e in scene_iterator)
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
            
        self.tables = [self.net.ext_grid, self.net.load, self.net.sgen, self.net.storage]

        if not self.model:
            self.model = pe.ConcreteModel()
        
        self.initialize_submodels()
        
        #power balance constraint
        self.power_balance_constraint()
        
        self.objective_function()
        
        return self.model
        
    def backconfigure_network(self):
        """
        Modifies network tables based on results of the optimization.
        Works only on sgen's.
        
        Returns:
            A reference to the network description.
        """
        for table in self.tables:
            for element in range(len(table)):
                m = table['model'][element] 
                if m:
                    if m.decide_construction:
                        vn = m.name + '_create'
                        var = getattr(self.model, vn).value
                        if var:
                            table['in_service'][element] = True
                            table['max_p_mw'][element] = getattr(self.model, m.name + '_pr_mw').value
                            table['max_q_mvar'][element] = 0.5*getattr(self.model, m.name + '_pr_mw').value  #default value
                        else:
                            table['in_service'][element] = False
                            table['max_p_mw'][element] = 0.0
                            table['max_q_mvar'][element] = 0.0
    
    def get_scenes_results(self):
        """
        Returns a new Pandas DataFrame with the simulation results based on the
        optimization results. Sizeable elements not selected aren't included.
        """
        
        #Extracción de resultados en forma de Pandas Dataframe
        self.results =  pd.DataFrame([], index = range(len(self.scenes)))

        for table in self.tables:
            for element in range(len(table)):
                m = table['model'][element] 
                if m:
                    if m.decide_construction:
                        vn = m.name + '_create'
                        var = getattr(self.model, vn).value
                        if not var:
                            continue
                    for attr in self.report_attrs:
                        if hasattr(m, attr):
                            col_name = m.name + '_' + attr
                            res = np.zeros(len(self.scenes))
                            for i in range(len(self.scenes)):
                                v = m[attr, i]
                                #if the attr is a data frame
                                if hasattr(v, 'value'):
                                    v = v.value
                                res[i] = v
                            self.results[col_name] = res            
            
        return self.results