import pyomo.environ as pe
import pandas as pd
import numpy as np

def network_precondition(net):
    """Auxiliary funtion that add extra columns in the net model,
    in order to maje useful for optimization model."""
    all_tables = ['bus', 'load','sgen', 'motor', 'asymmetric_load', 'asymmetric_sgen', 'storage',
                        'gen', 'switch', 'shunt','ext_grid', 'line', 'trafo', 'trafo3w', 'impedance',
                        'dcline', 'ward', 'xward', 'measurement', 'pwl_cost', 'poly_cost', 'controller']
        
    for t in all_tables:
        if not hasattr(net[t], 'model'):
            net[t]['model'] = None
    
    
class BaseModelWriter:
    
    def __init__(self, net = None, scenes = None):
        self.net = net
        self.scenes = scenes
        self.model = None
        self.results = None
        self.tables = []
        self.max_investement = None
        self.load_tables = ['load']
        
        if net:
            #self._add_extra_columns(self.net)
            network_precondition(net)
    """
    def _add_extra_columns(self, net):
        all_tables = ['bus', 'load','sgen', 'motor', 'asymmetric_load', 'asymmetric_sgen', 'storage',
                        'gen', 'switch', 'shunt','ext_grid', 'line', 'trafo', 'trafo3w', 'impedance',
                        'dcline', 'ward', 'xward', 'measurement', 'pwl_cost', 'poly_cost', 'controller']
        
        for t in all_tables: 
            net[t]['model'] = None
    """ 
    
    def create_model(self):
        self.model = pe.ConcreteModel()
        self.model.scenes = pe.Set(initialize = range(len(self.scenes)), doc = 'Scene Set')
        return self.model
    
    def additional_constraint(self, name, expression):
        """
        Adds a constraint of the simple (not  indexed) type.
        Arguments:
            name: unique name
            expression: a Pyomo expression (relation between Pyomo vars and operators)
        """
        constraint = pe.Constraint(expr = expression)
        setattr(self.model, name, constraint)
        setattr(self, name, constraint)
    
    def remove_if_has_constraint(self, name):
        if hasattr(self.model, name):
            delattr(self.model, name)
            return True
        return False
        
    def remove_constraint(self, name):
        if hasattr(self.model, name):
            delattr(self.model, name)
        else:
            raise Exception("Constraint not found")
            
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
            
    def total_suministred_energy(self):
        
        load_tables = [self.net.load]
        energy = 0.0
        
        for t in self.load_tables:
            table = self.net[t]
            for element in range(len(table)):
                m = table['model'][element] 
                if m and hasattr(m, 'p_mw'):
                    for s in self.model.scene_set:
                        scene = self.scenes.iloc[s]
                        energy += m.p_mw[s].value*scene['dt']*scene['dd']
                    
        return -energy
        
        
    def total_discounted_energy(self):
        
        load_tables = [self.net.load]
        energy = 0.0
        
        for t in self.load_tables:
            table = self.net[t]
            for element in range(len(table)):
                m = table['model'][element] 
                if m and hasattr(m, 'p_mw'):
                    for s in self.model.scene_set:
                        scene = self.scenes.iloc[s]
                        energy += m.p_mw[s].value*scene['dt']*scene['dd']*scene['discount']
                    
        return -energy

    def total_cost_function(self):
        
        return pe.value(model_writer.model.value)
    
    def npc(self):
        """
        NPC can be the objective function, in this case is more efficient
        to call total_cost_funtion. A true implementation is needed.
        """
        return pe.value(self.model.value)

    def npv(self):
        """
        NPV can be the objective function, in this case is more efficient
        to call total_cost_funtion. A true implementation is needed.
        """
        return pe.value(self.model.value)
    
    def lcoe(self):
        return self.npc()/self.total_discounted_energy()
    
    def lvoe(self):
        return self.npv()/self.total_discounted_energy()
    
    
        
