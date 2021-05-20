import pyomo.environ as pe
import itertools
import pandas as pd
import numpy as np

class BaseResource:
    
    def __init__(self, name):
        #self.net = None
        self.scenes = None
        self.model = None
        self.name = name
        
        self.ic_0_mu = 0.0
        self.ic_1_mu = 0.0

        self.oc_0_mu = 0.0
        self.oc_1_mu = 0.0
        
        self.pa_pu = 1.0
        self.pr_pu = 1.0
        
        self.decide_construction = True   #model must decide if construct or not 
        self.size = True   #model must decide optimal sizing  of the element

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
    
    def __getitem__(self, key):
        """__getitem__ work as a convenient method to simulate dictionary behaviour.
        If 2 or mode keys are given, arguments are unpacked and passed to _element_get_value, 
        so a "evaluated" value is obtained"""
        ##TODO: Document better the pair __getitem__ + _get_element_value
        #Error AttributeError will raise by getattr if it fails
        if isinstance(key, str):
            return getattr(self, key)
        elif hasattr(key, '__getitem__') and len(key) >= 2:
            attr = getattr(self, key[0])
            scene = key[1]
            default = None
            if len(key) > 2:
                default = key[2]    
            return self._element_get_value(attr, scene, default)
        else:
            raise AttributeError
            
    def __setitem__(self, key, value):
        setattr(self, key, value)
    
    def __str__(self):
        return "Resource: {0}".format(self.name)
    
    def initialize_model(self, model, scenes):
        self.model = model
        self.scenes = scenes
        
        raise Exception("Must implement")

    def active_power(self, scene):
        """Must return active power in mw, in numeric form or as an expression of the decision variables.
        scene is the scene index"""
        raise Exception("Must implement")

    def available_power(self, scene):
        """Must return available active power in mw, in numeric form or as an expression of the decision variables.
        scene is the scene index"""
        raise Exception("Must implement")

    def initial_cost(self):
        """Must return initial cost in monetary units, in numeric form or as an expression of the decision variables."""
        raise Exception("Must implement")

    def operating_cost(self, scene):
        """Must return initial cost in monetary units, in numeric form or as an expression of the decision variables
        scene is the scene index"""
        raise Exception("Must implement")

