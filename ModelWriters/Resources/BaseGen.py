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
        return self['ic_0_mu'] + self['ic_1_mu']*self['pr_mw']

    def operating_cost(self, scene):
        """Returns initial cost in monetary units, in numeric form or as an expression of the decision variables
        scene is the scene index"""
        return self['oc_0_mu'] + self['oc_1_mu']*self.p_mw[scene]
    
