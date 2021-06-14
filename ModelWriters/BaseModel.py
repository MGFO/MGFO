import pyomo.environ as pe
import pandas as pd
import numpy as np

class BaseModelWriter:
    
    def __init__(self, net = None, scenes = None):
        self.net = net
        self.scenes = scenes
        self.model = None
        self.results = None
        self.tables = []

        
    def create_model(self):
        self.model = pe.ConcreteModel()
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
                            if hasattr(table, 'max_p_mw'): table['max_p_mw'][element] = getattr(self.model, m.name + '_pr_mw').value 
                            if hasattr(table, 'max_q_mvar'): table['max_q_mvar'][element] = 0.5*getattr(self.model, m.name + '_pr_mw').value 
                            if hasattr(table, 'max_e_mwh'): table['max_e_mwh'][element] = getattr(self.model, m.name + '_er_mwh').value
                        else:
                            table['in_service'][element] = False
                            if hasattr(table, 'max_p_mw'): table['max_p_mw'][element] = 0.0 
                            if hasattr(table, 'max_q_mvar'): table['max_q_mvar'][element] = 0.0 
                            if hasattr(table, 'max_e_mwh'): table['max_e_mwh'][element] = 0.0 
    
    def get_scenes_results(self):
        """
        Returns a new Pandas DataFrame with the simulation results based on the
        optimization results.
        """
        #Extracción de resultados en forma de Pandas Dataframe
        self.results =  pd.DataFrame([], index = range(len(self.scenes)))

        for table in self.tables:
            for element in range(len(table)):
                m = table['model'][element] 
                if m and hasattr(m, 'get_scenes_results'):               
                    m.get_scenes_results(self.results)
                    
        return self.results