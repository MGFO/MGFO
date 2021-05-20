import pyomo.environ as pe
from .BaseResource import BaseResource

class ExtGrid(BaseResource):
    
    def __init__(self, name):
        super().__init__(name)
        self.decide_construction = False
        self.size = False
    
    def initialize_model(self, model, scenes):
        self.model = model
        self.scenes = scenes
        self.scene_iterator = range(len(scenes))

        #energia comprada a la red
        vn = self.name + '_p_mw'
        self.p_mw = pe.Var(self.scene_iterator, within = pe.NonNegativeReals)
        setattr(self.model, vn, self.p_mw)
        for e in self.scene_iterator:
            self.p_mw[e].setlb(0)
            self.p_mw[e].setub(self['pa_pu', self.scenes.iloc[e]]*self['pr_mw'])

        return
    
    def active_power(self, scene):
        """Returns active power in mw, as an expression of the decision variables.
        scene is the scene index"""
        return self.p_mw[scene]

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
        return self['oc_0_mu'] + self['oc_1_mu']*self.p_mw[scene]
    