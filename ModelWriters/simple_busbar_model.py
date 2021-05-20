import pyomo.environ as pe
import itertools
import pandas as pd
import numpy as np

class BaseModelWriter:
    
    def __init__(self, net = None, scenes = None):
        self.net = net
        self.scenes = scenes
        self.model = None
        self.results = None
        
        self.M = 1e3
    
    def _element_get_value(self, value, scene, default = None):
        v = value
        if v is None:
            if default is not None:
                return default
            else:
                raise Exception("Not default value for {0}".format(value))
        elif callable(v) is True:
            return v(scene)
        elif hasattr(v, "__getitem__") is True:
            #this is for numpy that always implement __getitem__ method, but not len:
            if hasattr(v, "__len__") is False:
                return v
            else:
                #true list
                raise Exception("Not supported yet")
        else:
            #if it is not callable nor subscriptable, return whatever:
            return v
        
    def create_model(self):
        self.model = pe.ConcreteModel()
        return self.model
        

        
class SimpleModelWriter(BaseModelWriter):
    
    def _initialize_ext_grids(self):
        scene_iterator = range(len(self.scenes))

        #energia comprada a la red
        self.model.p_mw_Ext = pe.Var(itertools.product(range(len(self.net.ext_grid)), scene_iterator), within = pe.NonNegativeReals)
        for v in itertools.product(range(len(self.net.ext_grid)), scene_iterator):
            self.model.p_mw_Ext[v].setlb(0)
            self.model.p_mw_Ext[v].setub(self._element_get_value(self.net.ext_grid.iloc[v[0]]['pa_pu'], 
                                                                 self.scenes.iloc[v[1]]) * self.net.ext_grid.iloc[v[0]]['pr_mw'])
        return
    
    def _initialize_loads(self):
        scene_iterator = range(len(self.scenes))

        #consumos:
        self.model.p_mw_Load = pe.Var(itertools.product(range(len(self.net.load)), scene_iterator), within = pe.NonNegativeReals)
        for v in itertools.product(range(len(self.net.load)), scene_iterator):
            self.model.p_mw_Load[v].value = self._element_get_value(self.net.load.iloc[v[0]]['pa_pu'], 
                                                                    self.scenes.iloc[v[1]]) * self.net.load.iloc[v[0]]['pr_mw'] 
            self.model.p_mw_Load[v].fixed = True
        return
        
    def _initialize_sgens(self):
        scene_iterator = range(len(self.scenes))

        #generadores
        self.model.create_SGen = pe.Var(range(len(self.net.sgen)), within = pe.Binary)
        self.model.pr_mw_SGen = pe.Var(range(len(self.net.sgen)), within = pe.NonNegativeReals)
        self.model.p_mw_SGen = pe.Var(itertools.product(range(len(self.net.sgen)), scene_iterator), within = pe.NonNegativeReals)
        for v in itertools.product(range(len(self.net.sgen)), scene_iterator):
            if self.net.sgen['sizeable'][v[0]]:
                opt_var_create = self.model.create_SGen[v[0]]
                opt_var_rating = self.model.pr_mw_SGen[v[0]]
            else:
                opt_var_create = 1
                opt_var_rating = 1.0
                raise Exception("Not implemented yet")
        #no optimo porque crea todas las v.d. por más que algunas no sean necesarias.
        self.model.p_mw_SGen_constraint = pe.Constraint(itertools.product(range(len(self.net.sgen)), scene_iterator), 
                                               rule = (lambda m, g, s: self.model.p_mw_SGen[(g,s)] <= 
                                                        self.model.pr_mw_SGen[g]*self._element_get_value(self.net.sgen.iloc[g]['pa_pu'], 
                                                                                                         self.scenes.iloc[s]) ))
        self.model.create_SGen_constraint = pe.Constraint(range(len(self.net.sgen)), 
                                                rule = (lambda m, g: self.model.pr_mw_SGen[g] <= self.model.create_SGen[g]*self.M))

    def _initialize_storage(self):
        scene_iterator = range(len(self.scenes))

        #storage
        self.model.create_Storage = pe.Var(range(len(self.net.storage)), within = pe.Binary)
        self.model.pr_mw_Storage = pe.Var(range(len(self.net.storage)), within = pe.NonNegativeReals)
        self.model.er_mwh_Storage = pe.Var(range(len(self.net.storage)), within = pe.NonNegativeReals)
        self.model.p_mw_Storage = pe.Var(itertools.product(range(len(self.net.storage)), scene_iterator), within = pe.Reals)
        self.model.soc_mwh_Storage = pe.Var(itertools.product(range(len(self.net.storage)), scene_iterator), within = pe.NonNegativeReals)
        
        #power less that rating*availability
        self.model.p_mw_Storage_constraint_a = pe.Constraint(itertools.product(range(len(self.net.storage)), scene_iterator), 
                                               rule = (lambda m, g, s: m.p_mw_Storage[(g,s)] <= 
                                                        m.pr_mw_Storage[g]*self._element_get_value(self.net.storage.iloc[g]['pa_pu'], 
                                                                                                         self.scenes.iloc[s]) ))
        #power less that stored power
        self.model.p_mw_Storage_constraint_b = pe.Constraint(itertools.product(range(len(self.net.storage)), scene_iterator), 
                                               rule = (lambda m, g, s: m.p_mw_Storage[(g,s)] <= 
                                                        m.soc_mwh_Storage[(g,s)]/self.scenes.iloc[s]['dt']) )
        #charging less that rated power
        self.model.p_mw_Storage_constraint_c = pe.Constraint(itertools.product(range(len(self.net.storage)), scene_iterator), 
                                               rule = (lambda m, g, s: m.p_mw_Storage[(g,s)] >= 
                                                        -m.pr_mw_Storage[g]*self._element_get_value(self.net.storage.iloc[g]['pa_pu'], 
                                                                                                         self.scenes.iloc[s]) ))        
        def _storage_energy_constraint(m, g, s):
            if s==0:
                return pe.Constraint.Skip
            else:
                return self.model.soc_mwh_Storage[(g,s)] == m.soc_mwh_Storage[(g,s-1)]*(1-self.net.storage['sigma'][g]) \
                                                            - m.p_mw_Storage[(g,s)]*self.scenes['dt'][s]*self.net.storage['eta_bb'][g]
        
        #soc update on each scene
        self.model.soc_mwh_Storage_constraint_a = pe.Constraint(itertools.product(range(len(self.net.storage)), scene_iterator), 
                                               rule = _storage_energy_constraint)
        #upper limit on soc
        self.model.soc_mwh_Storage_constraint_b = pe.Constraint(itertools.product(range(len(self.net.storage)), scene_iterator), 
                                               rule = (lambda m, g, s: m.soc_mwh_Storage[(g,s)] <= m.er_mwh_Storage[g]))

        
        #Big M for power rating
        self.model.create_Storage_constraint_a = pe.Constraint(range(len(self.net.storage)), 
                                                rule = (lambda m, g: self.model.pr_mw_Storage[g] <= self.model.create_Storage[g]*self.M))

        #Big M for capacity
        self.model.create_Storage_constraint_b = pe.Constraint(range(len(self.net.storage)), 
                                                rule = (lambda m, g: self.model.er_mwh_Storage[g] <= self.model.create_Storage[g]*self.M))

        
    def _power_balance_expression(self, scene_index): #scene is the scene index
        ##Test what happend with some network without a type, for example, no ext grid.
        #return the power balance for the selected scene:

        #Ext Grid:
        pt_mw_ext_grid = sum(self.model.p_mw_Ext[element, scene_index] for element in range(len(self.net.ext_grid)))

        #Loads:
        pt_mw_load = sum(self.model.p_mw_Load[element, scene_index] for element in range(len(self.net.load)))

        #Gens:
        pt_mw_sgen = sum(self.model.p_mw_SGen[element, scene_index] for element in range(len(self.net.sgen)))

        #Storage:
        pt_mw_storage = sum(self.model.p_mw_Storage[element, scene_index] for element in range(len(self.net.storage)))

        return pt_mw_ext_grid + pt_mw_sgen + pt_mw_storage - pt_mw_load

    def _power_balance_constraint(self):
        #power balance constraint
        scene_iterator = range(len(self.scenes))
        self.model.power_balance_constraint = pe.Constraint(scene_iterator, 
                                    rule = (lambda m, s:  self._power_balance_expression(s) == 0))        

    def _initial_cost_expression(self):
        ic_ext_grid = sum(self.net.ext_grid['ic_0_mu'][element] + self.net.ext_grid['ic_1_mu'][element]*self.net.ext_grid['pr_mw'][element] 
                            for element in range(len(self.net.ext_grid)))
        ic_load = sum(self.net.load['ic_0_mu'][element] + self.net.load['ic_1_mu'][element]*self.net.load['pr_mw'][element] 
                            for element in range(len(self.net.load)))
        ic_sgen = sum(self.net.sgen['ic_0_mu'][element]*self.model.create_SGen[element] + self.net.sgen['ic_1_mu'][element]*self.model.pr_mw_SGen[element] 
                            for element in range(len(self.net.sgen)))
        ic_storage = sum(self.net.storage['ic_0_mu'][element]*self.model.create_Storage[element] 
                         + self.net.storage['ic_1_mu'][element]*self.model.pr_mw_Storage[element] 
                         + self.net.storage['ic_1_mu_cap'][element]*self.model.er_mwh_Storage[element] 
                            for element in range(len(self.net.storage)))

        return ic_ext_grid + ic_load + ic_sgen + ic_storage
    
    def _hourly_operational_cost_expression(self, scene_index):
        ## generalizar este codigo
        oc_ext_grid = sum(self.net.ext_grid['oc_0_mu'][element] + 
                          self._element_get_value(self.net.ext_grid['oc_1_mu'][element],
                                self.scenes.iloc[scene_index])*self.model.p_mw_Ext[(element, scene_index)] 
                                for element in range(len(self.net.ext_grid)))
        oc_load = sum(self.net.load['oc_0_mu'][element] + 
                        self._element_get_value(self.net.load['oc_1_mu'][element], 
                                self.scenes.iloc[scene_index])*self.model.p_mw_Load[(element,scene_index)] 
                                for element in range(len(self.net.load)))
        oc_sgen = sum(self.net.sgen['oc_0_mu'][element] + 
                        self._element_get_value(self.net.sgen['oc_1_mu'][element], 
                                self.scenes.iloc[scene_index])*self.model.p_mw_SGen[(element,scene_index)] 
                                for element in range(len(self.net.sgen)))
        oc_sgen = sum(self.net.sgen['oc_0_mu'][element] + 
                        self._element_get_value(self.net.sgen['oc_1_mu'][element], 
                                self.scenes.iloc[scene_index])*self.model.p_mw_SGen[(element,scene_index)] 
                                for element in range(len(self.net.sgen)))
        oc_storage = sum(self.net.storage['oc_0_mu'][element] + 
                        self._element_get_value(self.net.storage['oc_1_mu'][element], 
                                self.scenes.iloc[scene_index])*self.model.p_mw_Storage[(element,scene_index)] 
                                for element in range(len(self.net.storage)))
        
        return oc_ext_grid + oc_load + oc_sgen + oc_storage
    
    def _operational_cost_expression(self):
        scene_iterator = range(len(self.scenes))
        
        op_cost = sum(self._hourly_operational_cost_expression(e)*self.scenes['dt'][e] for e in scene_iterator)
        return op_cost
    
    def _objective_function(self):
        self.model.value = pe.Objective( expr = self._initial_cost_expression() + self._operational_cost_expression(), sense = pe.minimize )
        return self.model.value
    
    def initialize_model(self):
        self.model = pe.ConcreteModel()

        self._initialize_ext_grids()
        self._initialize_loads()        
        self._initialize_sgens()
        self._initialize_storage()
    
        return self.model
    
    def create_model(self):
        if not self.model:
            self.initialize_model()
        
        #power balance constraint
        self._power_balance_constraint()
        
        self._objective_function()
        
        return self.model
        
    def backconfigure_network(self):
        """
        Modifies network tables based on results of the optimization.
        Works only on sgen's.
        
        Returns:
            A reference to the network description.
        """
        #for gen in self.model.create_SGen
        for g in self.model.create_SGen:
            if self.model.create_SGen[g].value:
                self.net.sgen['in_service'][g] = True
                self.net.sgen['max_p_mw'][g] = self.model.pr_mw_SGen[g].value
                self.net.sgen['max_q_mvar'][g] = 0.5*self.model.pr_mw_SGen[g].value  #default value
                self.net.sgen['pr_mw'][g] = self.model.pr_mw_SGen[g].value
            else:
                self.net.sgen['in_service'][g] = False
                self.net.sgen['max_p_mw'][g] = 0.0
                self.net.sgen['max_q_mvar'][g] = 0.0
                self.net.sgen['pr_mw'][g] = 0.0
        
        for g in self.model.create_Storage:
            if self.model.create_Storage[g].value:
                self.net.storage['in_service'][g] = True
                #self.net.storage['max_p_mw'][g] = self.model.pr_mw_Storage[g].value
                #self.net.storage['max_q_mvar'][g] = 0.25*self.model.pr_mw_Storage[g].value  #default value
                self.net.storage['pr_mw'][g] = self.model.pr_mw_Storage[g].value
                self.net.storage['max_e_mwh'][g] = self.model.er_mwh_Storage[g].value
            else:
                self.net.storage['in_service'][g] = False
                #self.net.storage['max_p_mw'][g] = 0.0
                #self.net.storage['max_q_mvar'][g] = 0.0
                self.net.storage['pr_mw'][g] = 0.0
                self.net.storage['max_e_mwh'][g] = 0.0
    
    def get_scenes_results(self):
        """
        Returns a new Pandas DataFrame with the simulation results based on the
        optimization results. Sizeable elements not selected aren't included.
        """

        #A list of columns will be created:
        columns = {}
        col_refs = {}
        
        table = self.net.ext_grid
        for element in range(len(table)):
            if not table['name'][element] == '':
                name = table['name'][element]
            else:
                name = 'EXT[{0}]'.format(element)
            columns[name] = 0.0
            col_refs[name] = {'set': self.model.p_mw_Ext, 'main_index': element}

        table = self.net.load
        for element in range(len(table)):
            if not table['name'][element] == '':
                name = table['name'][element]
            else:
                name = 'LOAD[{0}]'.format(element)
            columns[name] = 0.0
            col_refs[name] = {'set': self.model.p_mw_Load, 'main_index': element}

        table = self.net.sgen
        for element in range(len(table)):
            if self.model.create_SGen[element]:
                if not table['name'][element] == '':
                    name = table['name'][element]
                else:
                    name = 'LOAD[{0}]'.format(element)
                columns[name] = 0.0
                col_refs[name] = {'set': self.model.p_mw_SGen, 'main_index': element}

        table = self.net.storage
        for element in range(len(table)):
            if self.model.create_Storage[element]:
                if not table['name'][element] == '':
                    name1 = table['name'][element]
                    name2 = 'E_' + table['name'][element]                     
                else:
                    name1 = 'P_STORAGE[{0}]'.format(element)
                    name1 = 'E_STORAGE[{0}]'.format(element)
                columns[name1] = 0.0
                col_refs[name1] = {'set': self.model.p_mw_Storage, 'main_index': element}
                columns[name2] = 0.0
                col_refs[name2] = {'set': self.model.soc_mwh_Storage, 'main_index': element}

                
        #Extracción de resultados en forma de Pandas Dataframe
        self.results =  pd.DataFrame([columns], index = range(len(self.scenes)))
        
        for name in columns:
            res = np.zeros(len(self.scenes))
            for i in range(len(self.scenes)):
                res[i] = col_refs[name]['set'][(col_refs[name]['main_index'], i)].value
            
            self.results[name] = res
            
            
        return self.results