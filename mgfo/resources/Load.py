import pyomo.environ as pe
from .BaseResource import BaseResource
from ..Simulation import Demand
import numpy as np

class Load(BaseResource):
    
    def __init__(self, name, pr_mw = 0.050, pa_pu = None):
        super().__init__(name)
        self.decide_construction = False
        self.size = False
        self.pr_mw = pr_mw
        self.p_mw = pr_mw
        
        if pa_pu:
            self.pa_pu = pa_pu
        else:
            self.pa_pu = Demand.DemandSimulator()
    
    def initialize_model(self, model, scenes):
        self.model = model
        self.scenes = scenes
        
        ##self.scene_iterator = range(len(self.scenes))
        self.scene_iterator = self.model.scene_set
        #energia demandada a la red
        vn = self.name + '_p_mw'
        self.p_mw = pe.Var(self.scene_iterator, within = pe.Reals)
        setattr(self.model, vn, self.p_mw)
        #this var will be reported
        self.report_attrs[vn] = self.p_mw

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
        return self['oc_0_mu'] + self['oc_1_mu', self.scenes.iloc[scene]]*self['p_mw', scene]
    