import pyomo.environ as pe
#import itertools
#import pandas as pd
#import numpy as np

class BaseModelWriter:
    
    def __init__(self, net = None, scenes = None):
        self.net = net
        self.scenes = scenes
        self.model = None
        self.results = None
        self.report_attrs = ['p_mw', 'soc_mwh']

        
    def create_model(self):
        self.model = pe.ConcreteModel()
        return self.model
        

