import pyomo.environ as pe
from .BaseResource import BaseResource

class Generator(BaseResource):
        
    def initialize_model(self, model, scenes):
        self.model = model
        self.scenes = scenes
        self.scene_iterator = range(len(scenes))
        self.M = 1e3
        
        #to create generator
        vn = self.name + '_create'
        self.create = pe.Var(within = pe.Binary)
        setattr(self.model, vn, self.create)
        
        #sizing d.v.        
        vn = self.name + '_pr_mw'
        self.pr_mw = pe.Var(within = pe.NonNegativeReals)
        setattr(self.model, vn, self.pr_mw)        
        
        #generated energy
        vn = self.name + '_p_mw'
        self.p_mw = pe.Var(self.scene_iterator, within = pe.NonNegativeReals)
        setattr(self.model, vn, self.p_mw)

        #no optimo porque crea todas las v.d. por más que algunas no sean necesarias.
        cn = self.name + '_p_constraint'
        self.p_mw_constraint = pe.Constraint(self.scene_iterator, rule = (lambda m, s: self.p_mw[s] <= self.pr_mw * self['pa_pu', self.scenes.iloc[s]] ))
        setattr(self.model, cn, self.p_mw_constraint)
        
        cn = self.name + '_p_M_constraint'        
        self.create_constraint = pe.Constraint(expr = self.pr_mw <= self.create*self.M)
        setattr(self.model, cn, self.create_constraint)
        return
        
    
    def active_power(self, scene):
        """Returns active power in mw, as an expression of the decision variables.
        scene is the scene index"""
        return self['p_mw', scene]

    def available_power(self, scene):
        """Returns available active power in mw, in numeric form.
        scene is the scene index"""
        return self['pa_pu', self.scenes.iloc[scene]]*self['pr_mw']

    def initial_cost(self):
        """Returns initial cost in monetary units, in numeric form or as an expression of the decision variables."""
        return self['ic_0_mu']*self['create'] + self['ic_1_mu']*self['pr_mw']

    def operating_cost(self, scene):
        """Returns initial cost in monetary units, in numeric form or as an expression of the decision variables
        scene is the scene index"""
        return self['oc_0_mu'] + self['oc_1_mu']*self.p_mw[scene]
    

class DiscreteGenerator(Generator):
    """A generator that is sizeable in steps of the unit_size_mw.
    Initial cost has 3 components: a fixed cost, a "per unit" cost and a 
    rated power-dependent cost""" 
    
    def __init__(self, name):
        super().__init__(name)
        
        self.unit_size_mw = 0.25
        self.unit_cost_mu = 1.0
    
    def initialize_model(self, model, scenes):
        self.model = model
        self.scenes = scenes
        self.scene_iterator = range(len(scenes))
        self.M = 1e3
        
        #to create generator
        vn = self.name + '_create'
        self.create = pe.Var(within = pe.Binary)
        setattr(self.model, vn, self.create)

        #units to create        
        vn = self.name + '_units'
        self.units = pe.Var(within = pe.NonNegativeIntegers)
        setattr(self.model, vn, self.units)        

        #sizing d.v.        
        vn = self.name + '_pr_mw'
        self.pr_mw = pe.Var(within = pe.NonNegativeReals)
        setattr(self.model, vn, self.pr_mw)        
        
        #generated energy
        vn = self.name + '_p_mw'
        self.p_mw = pe.Var(self.scene_iterator, within = pe.NonNegativeReals)
        setattr(self.model, vn, self.p_mw)

        #no optimo porque crea todas las v.d. por más que algunas no sean necesarias.
        cn = self.name + '_p_constraint'
        self.p_mw_constraint = pe.Constraint(self.scene_iterator, rule = (lambda m, s: self.p_mw[s] <= self.pr_mw * self['pa_pu', self.scenes.iloc[s]] ))
        setattr(self.model, cn, self.p_mw_constraint)
        
        
        cn = self.name + '_units_constraint'        
        self.create_units_constraint = pe.Constraint(expr = self.units <= self.create*self.M)
        setattr(self.model, cn, self.create_units_constraint)

        cn = self.name + 'pr_units_constraint'        
        self.pr_units_constraint = pe.Constraint(expr = self.pr_mw == self.units*self.unit_size_mw)
        setattr(self.model, cn, self.pr_units_constraint)
        
        return
    
    def initial_cost(self):
            """Returns initial cost in monetary units, in numeric form or as an expression of the decision variables."""
            return self['ic_0_mu']*self['create'] + self['ic_1_mu']*self['pr_mw'] + self['unit_cost_mu']*self['units']