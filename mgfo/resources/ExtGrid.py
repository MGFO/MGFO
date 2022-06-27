import pyomo.environ as pe
from .BaseResource import BaseResource
from ..Simulation import Economics

import numpy as np

class ExtGrid(BaseResource):
    
    def __init__(self, name, peak_value=200e-6, valley_value=120e-6, rest_value=160e-6,
                 oc_1_mu = None, pr_mw = 1.0, hours = [6.0, 18.0, 23.0, 24.0] ):
        super().__init__(name, oc_1_mu = oc_1_mu, pr_mw = pr_mw)
        self.decide_construction = False
        self.size = False
        
        if oc_1_mu is None:
            self.oc_1_mu = Economics.ElectricityCostSimulator(peak_value = peak_value, valley_value = valley_value, rest_value = rest_value, 
                                                              piecewise_hours = hours)
    
    def initialize_model(self, model, scenes):
        self.model = model
        self.scenes = scenes

        #energia comprada a la red
        vn = self.name + '_p_mw'
        self.p_mw = pe.Var(model.scene_set, within = pe.NonNegativeReals)
        setattr(self.model, vn, self.p_mw)
        for e in self.model.scene_set:
            self.p_mw[e].setlb(0)
            self.p_mw[e].setub(self['pa_pu', self.scenes.iloc[e]]*self['pr_mw'])
        #this var will be reported
        self.report_attrs[vn] = self.p_mw

        return

    def get_scenes_results(self, data_frame, include_inactive = False):
        """Add simulation results to the data frame, assumed same lenght as the scene collection.
        Parameters:
            data_frame: Pandas data frame.
        Returns:
            data_frame"""
        for attr in self.report_attrs:
            res = np.zeros(len(self.scenes))
            for i in range(len(self.scenes)):
                res[i] = self.report_attrs[attr][i].value
            data_frame[attr] = res            
        return data_frame
    
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
        return self['oc_0_mu'] + self['oc_1_mu', self.scenes.iloc[scene]]*self.p_mw[scene]
    