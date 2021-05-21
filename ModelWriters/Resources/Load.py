import pyomo.environ as pe
from .BaseResource import BaseResource

class Load(BaseResource):
    
    def __init__(self, name):
        super().__init__(name)
        self.decide_construction = False
        self.size = False
        self.pr_mw = 0.1
        self.p_mw = 0.1
    
    def initialize_model(self, model, scenes):
        self.model = model
        self.scenes = scenes
        
        self.scene_iterator = range(len(self.scenes))
        #energia demandada a la red
        vn = self.name + '_p_mw'
        self.p_mw = pe.Var(self.scene_iterator, within = pe.Reals)
        setattr(self.model, vn, self.p_mw)
    
    def active_power(self, scene):
        """Returns active power in mw, in numeric form or as an expression of the decision variables.
        scene is the scene index. For loads, all available power is consumed. By convention, consumed power is negative."""
        #results are stored in a fixed var in order to preserve data, pyomo var is used for consistency
        if not self.p_mw[scene].fixed:
            p = -self.available_power(scene)
            self.p_mw[scene].value = p
            self.p_mw[scene].fixed = True
                
        return self.p_mw[scene].value

    def available_power(self, scene):
        """Returns available active power in mw, in numeric form.
        scene is the scene index"""
        return self['pa_pu', self.scenes.iloc[scene]]*self['pr_mw']

    def initial_cost(self):
        """Must return initial cost in monetary units, in numeric form or as an expression of the decision variables."""
        return self['ic_0_mu'] + self['ic_1_mu']*self['pr_mw']

    def operating_cost(self, scene):
        """Must return initial cost in monetary units, in numeric form or as an expression of the decision variables
        scene is the scene index"""
        return self['oc_0_mu'] + self['oc_1_mu']*self['p_mw', scene]
    