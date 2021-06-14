import pyomo.environ as pe
from .BaseGen import Generator

class Storage(Generator):
    
    def __init__(self, name):
        super().__init__(name)
        
        #an attribute for energy storage is added
        self.er_mwh = 0.0
        
        #Round-Trip efficiency:
        self.eta_bb = 0.8
        
        #hourly self-discharge:
        self.sigma = 0.05/24
        
    def initialize_model(self, model, scenes):
        self.model = model
        self.scenes = scenes
        self.scene_iterator = range(len(scenes))
        self.M = 1e3
        
        #to create storage
        vn = self.name + '_create'
        self.create = pe.Var(within = pe.Binary)
        setattr(self.model, vn, self.create)
        
        #pr sizing d.v.        
        vn = self.name + '_pr_mw'
        self.pr_mw = pe.Var(within = pe.NonNegativeReals)
        setattr(self.model, vn, self.pr_mw)        

        #er sizing d.v.        
        vn = self.name + '_er_mwh'
        self.er_mwh = pe.Var(within = pe.NonNegativeReals)
        setattr(self.model, vn, self.er_mwh)

        #generated energy
        vn = self.name + '_p_mw'
        self.p_mw = pe.Var(self.scene_iterator, within = pe.Reals)
        setattr(self.model, vn, self.p_mw)
        #this var will be reported
        self.report_attrs[vn] = self.p_mw

        #stored energy
        vn = self.name + '_soc_mwh'
        self.soc_mwh = pe.Var(self.scene_iterator, within = pe.NonNegativeReals)
        setattr(self.model, vn, self.soc_mwh)
        #this var will be reported
        self.report_attrs[vn] = self.soc_mwh

        #power rating constraint
        cn = self.name + '_p_constraint_pr'
        self.p_mw_constraint_pr = pe.Constraint(self.scene_iterator, rule = (lambda m, s: self.p_mw[s] <= self.pr_mw*self['pa_pu', s] ))
        setattr(self.model, cn, self.p_mw_constraint_pr)

        #charging power less that power rating
        cn = self.name + '_p_constraint_charge'
        self.p_mw_constraint_charge = pe.Constraint(self.scene_iterator, rule = (lambda m, s: -self.pr_mw*self['pa_pu', s] <= self.p_mw[s]))
        setattr(self.model, cn, self.p_mw_constraint_charge)

        #available energy constraint
        cn = self.name + '_p_constraint_soc'
        self.p_mw_constraint_soc = pe.Constraint(self.scene_iterator, rule = (lambda m, s: self.p_mw[s] <= self.soc_mwh[s]/self.scenes['dt'][s]))
        setattr(self.model, cn, self.p_mw_constraint_soc)

        #oc update on each scene
        storage_energy_expression = (lambda m, s: self.soc_mwh[s] == self.soc_mwh[s-1]*(1-self.sigma) - self.p_mw[s]*self.scenes['dt'][s]*self.eta_bb
                                           if s>0 else self.soc_mwh[s] == 0 )
        
        cn = self.name + '_soc_constraint'
        self.soc_constraint = pe.Constraint(self.scene_iterator, rule = storage_energy_expression)
        setattr(self.model, cn, self.soc_constraint)
        
        #upper limit on soc
        cn = self.name + '_soc_constraint_er'
        self.soc_constraint_er = pe.Constraint(self.scene_iterator, rule = (lambda m,s: self.soc_mwh[s] <= self.er_mwh))
        setattr(self.model, cn, self.soc_constraint_er)
        
        
        #Big M for power rating
        cn = self.name + '_p_M_constraint'        
        self.create_constraint_pr = pe.Constraint(expr = self.pr_mw <= self.create*self.M)
        setattr(self.model, cn, self.create_constraint_pr)

        #Big M for capacity
        cn = self.name + '_e_M_constraint'        
        self.create_constraint_er = pe.Constraint(expr = self.er_mwh <= self.create*self.M)
        setattr(self.model, cn, self.create_constraint_er)
    
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
        return self['ic_0_mu']*self['create'] + self['ic_1_mu']*self['pr_mw'] + self['ic_1_mu_cap']*self['er_mwh']

    def operating_cost(self, scene):
        """Returns initial cost in monetary units, in numeric form or as an expression of the decision variables
        scene is the scene index"""
        return self['oc_0_mu'] + self['oc_1_mu']*self.p_mw[scene]
