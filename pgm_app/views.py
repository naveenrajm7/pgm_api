from django.shortcuts import render
from django.http import Http404
from rest_framework.views import APIView
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.http import JsonResponse
from django.core import serializers
from django.conf import settings
import json

from pgmpy.factors.discrete import TabularCPD
from pgmpy.models import BayesianModel
# Create your views here.

@api_view(["POST"])
def describe(model_name):
    '''description: Describe the given bayesian model
    Parameters
        ----------
        model: pgmpy Bayesian Object
        returns: Input and Output random variables
    '''
    try:
        # print(type(model_name))
        # found = False
        # for key in model_list.keys():
        #     if key == model_name:
        #         model = model_list[key]
        #         found = True
        #
        # if not found:
        #     return JsonResponse("Model not found", safe=False)
        model = student_model
        # identifying root and leaf of model
        root = []
        for x in model.in_degree:
            if x[1] == 0:
                root.append(x[0])
        leaf = []
        for x in model.out_degree:
            if x[1] == 0:
                leaf.append(x[0])

        for i in root:
            for j in leaf:
                #to remove leaf nodes for which some of the root nodes have no influence
                if str(model.is_active_trail(i,j))=='False':
                    leaf.remove(j)

        return JsonResponse("Model has "+str(root)+" as root and "+str(leaf)+" as leaf", safe=False)
    except ValueError as e:
        return Response(e.args[0],status.HTTP_400_BAD_REQUEST)


# creating bayesian objects
difficulty_cpd = TabularCPD(variable='D',
                       variable_card=2,
                       values=[[.6, .4]])

intelligence_cpd = TabularCPD(variable='I',
                       variable_card=2,
                       values=[[.7, .3]])

sat_cpd = TabularCPD(variable='S',
                     variable_card=2,
                     values=[[.95, 0.2],
                             [.05, 0.8]],
                     evidence=['I'],
                     evidence_card=[2])

# grade
grade_cpd = TabularCPD(variable='G',
                         variable_card=3,
                         values=[[.3, .05, .9, .5 ],
                        [.4, .25, .08, .3],
                        [.3, .7, .02, .2]],
                         evidence=['I', 'D'],
                         evidence_card=[2, 2])

letter_cpd = TabularCPD(variable='L',
                     variable_card=2,
                     values=[[.1, 0.4, .99],
                             [.9, 0.6, .01]],
                     evidence=['G'],
                     evidence_card=[3])

# buildind model
student_model = BayesianModel([('D', 'G'),('I', 'G'), ('I', 'S'), ('G', 'L')])

# adding cpds
student_model.add_cpds(difficulty_cpd, intelligence_cpd, sat_cpd, grade_cpd, letter_cpd)


# model list , name-> object
model_list = { "student":student_model }
