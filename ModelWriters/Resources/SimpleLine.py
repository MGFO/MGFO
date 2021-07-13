from .BaseResource import BaseResource
import pyomo.environ as pe
import itertools
import pandas as pd
import numpy as np

class SimpleLine(BaseResource):
    """SimpleLine is a class intented to model transmission lines, basically in a radially environment.
    All generic attributes are implemented. Must be remembered that if a coefficient is 0, all vars multiplied
    by this coefficient are automatically ignored.
    p_r attribute defines power losses, ignored in SimpleLine
    pa_pu is the available power in the line, usually 1, but can be 0 i.e. to simulate a fault
    ir_ka is the current rating, useful for capacity constraints
    max_i_pu is the maximum admisible current in per unit
    pf_mw is the power flow in the line"""
    
    def __init__(self, busbar_from='', busbar_to=''):
        
        name = str(busbar_from) + '_' + str(busbar_to)
        super().__init__(name)
        
        self.pa_pu = 1.0
        
        #current rating
        self.ir_ka = 1.0
        #maximum tolerable current in per unit
        self.max_i_pu = 1.5

        #line voltage rating
        self.vn_kv = 1.0
        
        #bus index
        self.from_bus = 0
        self.to_bus = 0
        
        self.decide_construction = False   #model must decide if construct or not 
        self.size = False   #model must decide optimal sizing  of the element
        
        self.soft_limit_coefficient = None
        
        self.M = 1e3
    
    def __str__(self):
        return 'Line: ' + self.name
        
    def initialize_model(self, model, scenes):
        self.model = model
        self.scenes = scenes
        
        self.scene_iterator = range(len(scenes))

        #power flow
        vn = self.name + '_pf_mw'
        self.pf_mw = pe.Var(self.scene_iterator, within = pe.Reals)
        setattr(self.model, vn, self.pf_mw)
        #this var will be reported
        self.report_attrs[vn] = self.pf_mw
        #power transmission limits:
        for s in self.scene_iterator:
            self.pf_mw[s].setlb(- self.pr_mw * self.max_i_pu * self['pa_pu', self.scenes.iloc[s]])
            self.pf_mw[s].setub(- self.pf_mw[s].lb)
        
        if not self.soft_limit_coefficient is None:
            #total excess power
            self.excess_power_mw = pe.Var(self.scene_iterator, within = pe.NonNegativeReals)
            vn = self.name + '_ep_mw'
            setattr(self.model, vn, self.excess_power_mw)
            #this var will be reported
            self.report_attrs[vn] = self.excess_power_mw
            #Excess power by positive pf
            self.excess_power_p = pe.Var(self.scene_iterator, within = pe.NonNegativeReals)
            vn = self.name + '_epp_mw'
            setattr(self.model, vn, self.excess_power_p)
            #Excess power by negative pf
            self.excess_power_n = pe.Var(self.scene_iterator, within = pe.NonNegativeReals)
            vn = self.name + '_epn_mw'
            setattr(self.model, vn, self.excess_power_n)
            #Base power, positive pf
            self.base_power_p = pe.Var(self.scene_iterator, within = pe.NonNegativeReals)
            vn = self.name + '_bpp_mw'
            setattr(self.model, vn, self.base_power_p)
            #Base power, negative pf
            self.base_power_n = pe.Var(self.scene_iterator, within = pe.NonNegativeReals)
            vn = self.name + '_bpn_mw'
            setattr(self.model, vn, self.base_power_n)
            #y-constraints:
            self.y1 = pe.Var(self.scene_iterator, within = pe.Binary)
            vn = self.name + '_y1'
            setattr(self.model, vn, self.y1)
            self.y2 = pe.Var(self.scene_iterator, within = pe.Binary)
            vn = self.name + '_y2'
            setattr(self.model, vn, self.y2)
                
            #after vars declaration, model:
            vn = self.name + '_c1'
            constraint = pe.Constraint(self.scene_iterator, rule = (lambda m, scene: self.excess_power_mw[scene] == 
                                                               self.excess_power_p[scene] + self.excess_power_n[scene])) 
            setattr(self.model, vn, constraint)

            vn = self.name + '_c2'
            constraint = pe.Constraint(self.scene_iterator, rule = (lambda m, scene: self.excess_power_p[scene] <= 
                                                               self.M*self.y1[scene])) 
            setattr(self.model, vn, constraint)

            vn = self.name + '_c3'
            constraint = pe.Constraint(self.scene_iterator, rule = (lambda m, scene: self.base_power_p[scene] <= 
                                                               self.M*(1-self.y1[scene]))) 
            setattr(self.model, vn, constraint)

            vn = self.name + '_c4'
            constraint = pe.Constraint(self.scene_iterator, rule = (lambda m, scene: self.excess_power_n[scene] <= 
                                                               self.M*self.y2[scene])) 
            setattr(self.model, vn, constraint)

            vn = self.name + '_c5'
            constraint = pe.Constraint(self.scene_iterator, rule = (lambda m, scene: self.base_power_n[scene] <= 
                                                               self.M*(1-self.y2[scene]))) 
            setattr(self.model, vn, constraint)

            vn = self.name + '_c6'
            constraint = pe.Constraint(self.scene_iterator, rule = (lambda m, scene: self.pf_mw[scene] - self.pr_mw == 
                                                                       self.excess_power_p[scene] - self.base_power_p[scene]))
            setattr(self.model, vn, constraint)

            vn = self.name + '_c7'
            constraint = pe.Constraint(self.scene_iterator, rule = (lambda m, scene: -self.pf_mw[scene] - self.pr_mw == 
                                                                       self.excess_power_n[scene] - self.base_power_n[scene]))
            setattr(self.model, vn, constraint)

        #active power: power losses are not contemplated in this model
        self.p_mw = 0.0

    def get_scenes_results(self, data_frame, include_inactive = False):
        """Add simulation results to the data frame, assumed same lenght as the scene collection.
        Parameters:
            data_frame: Pandas data frame.
            include_inactive: If true, result from not selected resources are included.
        Returns:
            data_frame"""
        for attr in self.report_attrs:
            res = np.zeros(len(self.scenes))
            for i in range(len(self.scenes)):
                res[i] = self.report_attrs[attr][i].value
            data_frame[attr] = res            
        return data_frame
    
    def active_power(self, scene):
        """Active power is limited to the power losses. That is to avoid double accounting of the 
        power transmited in the network power balance"""
        return self['p_mw', scene]

    def transmited_power(self, scene):
        """Power transmited, positive when flows from "from" to "to" in the net.line table """
        return self['pf_mw'][scene]
    
    def available_power(self, scene):
        """Returns available capacity in mw (mva), in numeric form.
        scene is the scene index"""
        return self['pa_pu', self.scenes.iloc[scene]]*self['pr_mw']

    def initial_cost(self):
        """Returns initial cost in monetary units, in numeric form or as an expression of the decision variables."""
        return self['ic_0_mu'] + self['ic_1_mu']*self['pr_mw']

    def operating_cost(self, scene):
        """Returns initial cost in monetary units, in numeric form or as an expression of the decision variables
        scene is the scene index"""
        if not self.soft_limit_coefficient is None:
            excess_penalty = self['excess_power_mw', scene]*self.soft_limit_coefficient
        else:
            excess_penalty = 0.0
            
        return self['oc_0_mu'] + self['oc_1_mu']*self['pf_mw', scene] + excess_penalty
