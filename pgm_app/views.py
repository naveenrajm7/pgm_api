from django.shortcuts import render
from django.http import Http404

from rest_framework.views import APIView
from rest_framework.decorators import api_view
from rest_framework.decorators import parser_classes
from rest_framework.decorators import renderer_classes
from rest_framework.parsers import JSONParser
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer
from rest_framework import status

from django.http import JsonResponse
from django.core import serializers
from django.conf import settings
import json

from pgmpy.factors.discrete import TabularCPD
from pgmpy.models import BayesianModel
from pgmpy.factors import factor_product
from pgmpy.inference.base import Inference

from networkx.readwrite import json_graph

import itertools

# Create your views here.

@api_view(['POST'])
@parser_classes((JSONParser,))
def example_view(request, format=None):
    """
    A view that can accept POST requests with JSON content.
    """

    return Response({'received data': request.data.get('model'), 'param': request.data.get('observe')+request.data.get('state')})


@api_view(["GET"])
@renderer_classes((JSONRenderer,))
def list(request, format = None):
    '''description: List all available models
    Parameters
        ----------
        Nil
    '''
    return_list = model_list.keys()
    content = { 'models' : return_list }
    return Response(content)


@api_view(["POST"])
@renderer_classes((JSONRenderer,))
def get_json(request):
    ''' description: json format of given bayesian model
    Parameters
        ----------
        model: pgmpy Bayesian Object
        returns: json
    '''
    try:
        found = False
        for key in model_list.keys():
            if key == request.data.get('model'):
                model = model_list[key]
                key1=key
                found = True

        if not found:
            return JsonResponse("Model not found", safe=False)

        json_content = json_graph.node_link_data(model)
        return Response(json_content)

    except ValueError as e:
        return Response(e.args[0],status.HTTP_400_BAD_REQUEST)
        

@api_view(["POST"])
def describe(request):
    '''description: Describe the given bayesian model
    Parameters
        ----------
        model: pgmpy Bayesian Object
        returns: Input and Output random variables
    '''
    try:
        found = False
        for key in model_list.keys():
            if key == request.data.get('model'):
                model = model_list[key]
                key1=key
                found = True

        if not found:
            return JsonResponse("Model not found", safe=False)



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
        Root=[]
        Leaf=[]
        m=globals()[key1]
        for r in root:
            for r1 in m:
                if r==r1:
                    Root.append(m[r])
        for l in leaf:
            for l1 in m:
                if l==l1:
                    Leaf.append(m[l])
        if len(Leaf)>1:
            op="the Leaves"
        else:
            op="the  Leaf"
        if len(Root)>1:
            op1="the Roots"
        else:
            op1="the Root"


        s=""
        last=" states,"
        rlen=len(root)
        for r,r1 in zip(root,Root):

            length=model.get_cardinality(r)
            if rlen!=1:
                if rlen==2:
                    last=" states"
                s+=str(r1)+" has "+ str(length) +last
            else:
                s+=first+str(r1)+" has "+ str(length) +last
            rlen=rlen-1
            if rlen==1:
                first=" and "
                last=" states."

        s2=""
        last2=" states,"
        leaflen=len(leaf)
        for l,l1 in zip(leaf,Leaf):

            length2=model.get_cardinality(l)
            if leaflen==1:
                last2=" states"
                first=""
            if leaflen!=1:
                if leaflen==2:
                    last2=" states"
                s2+=str(l1)+" has "+ str(length2) +last2
            else:
                s2+=first+str(l1)+" has "+ str(length2) +last2
            leaflen=leaflen-1
            if leaflen==1:
                first=" and "
                last=" states."


        return JsonResponse("The "+key1 +" model "  " has "+str(Root).strip('[]')+" as " +op1+ " and "+str(Leaf).strip('[]')+" as "+op+". " +s+s2, safe=False)
    except ValueError as e:
        return Response(e.args[0],status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
def explain(request):
    '''description: Explain the given bayesian model
    Parameters
        ----------
        model: pgmpy Bayesian Object
        returns: All possible states of final random variable
    '''
    # to be done
    pass


@api_view(["POST"])
def infer(request):
    '''description: query the given bayesian model
    Parameters
        ----------
        model: pgmpy Bayesian Object
        returns: result of the given query
    '''
    class SimpleInference(Inference):
        ''' custom inference'''
        def query(self, var, evidence):
            # self.factors is a dict of the form of {node: [factors_involving_node]}
            factors_list = set(itertools.chain(*self.factors.values()))
            product = factor_product(*factors_list)
            reduced_prod = product.reduce(evidence, inplace=False)
            reduced_prod.normalize()
            var_to_marg = set(self.model.nodes()) - set(var) - set([state[0] for state in evidence])
            marg_prod = reduced_prod.marginalize(var_to_marg, inplace=False)
            return marg_prod

    found = False
    for key in model_list.keys():
        if key == request.data.get('model'):
            model = model_list[key]
            found = True

    if not found:
        return JsonResponse("Model not found", safe=False)

    res = request.data.get('res')
    observe = request.data.get('observe')
    state = request.data.get('state')

    # infer object ,
    infer = SimpleInference(model)
    # working for only one evidence
    result = infer.query(var=res, evidence=[(observe[0], state[0])]).values[1]

    return JsonResponse(request.data.get('model') +"'s "+str(res)+" probabitlity is "+convert_to_num(result), safe=False)

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


gas_cpd = TabularCPD(variable='G',
                     variable_card=2,
                     values=[[.2, 0.01],
                             [.8, 0.99]],
                     evidence=['F'],
                     evidence_card=[2])

fraud_cpd = TabularCPD(variable='F',
                       variable_card=2,
                       values=[[.1, .9]])

jewelery_cpd = TabularCPD(variable='J',
                         variable_card=2,
                         values=[[.2, .95, .05, .95, .04, .95, .02, .95, .02, .95, .1, .95],
                        [.8, .05, .95, .05, .96, .05, .98, .05, .98, .05, .9, .05]],
                         evidence=['A', 'S', 'F'],
                         evidence_card=[3, 2, 2])

age_cpd = TabularCPD(variable='A',
                    variable_card=3,
                    values=[[0.25, 0.40, 0.35]])

sex_cpd = TabularCPD(variable='S',
                    variable_card=2,
                    values=[[0.5, 0.5]])

fraud_model = BayesianModel([('F', 'J'),('F', 'G'), ('A', 'J'), ('S', 'J')])
fraud_model.add_cpds(jewelery_cpd, fraud_cpd, age_cpd, sex_cpd, gas_cpd)


credit_rating_cpd = TabularCPD(variable='CR', variable_card=4,
                values=[[0.85, 0.04, 0.12, 0.02, 0.13, 0.01],
                        [0.1, 0.07, 0.65, 0.07, 0.2, 0.04],
                        [0.04, 0.75, 0.15, 0.25, 0.45, 0.25],
                        [0.01, 0.14, 0.08, 0.66, 0.22, 0.7]],
                evidence=['OL', 'PH'], evidence_card=[3, 2])

interest_rate_cpd = TabularCPD(variable='IR', variable_card=3,
                values=[[0.01, 0.05, 0.12, 0.02, 0.05, 0.15, 0.3, 0.4, 0.55, 0.57, 0.83, 0.94],
                        [0.09, 0.7, 0.7, 0.23, 0.4, 0.45, 0.6, 0.55, 0.4, 0.4, 0.15, 0.05],
                        [0.9, 0.25, 0.18, 0.75, 0.55, 0.4, 0.1, 0.05, 0.05, 0.03, 0.02, 0.01]],
                evidence=['CR', 'IL'], evidence_card=[4, 3])

Outstanding_loan_cpd = TabularCPD(variable='OL', variable_card=3, values=[[0.15, 0.55, 0.3]])

Payment_history_cpd = TabularCPD(variable='PH', variable_card=2, values=[[0.8, 0.2]])

Income_level_cpd = TabularCPD(variable='IL', variable_card=3, values=[[0.1, 0.6, 0.3]])

credit_approval_model = BayesianModel([('OL', 'CR'),
                             ('PH', 'CR'),
                             ('IL', 'IR'),
                             ('CR', 'IR')])

credit_approval_model.add_cpds(credit_rating_cpd, interest_rate_cpd, Outstanding_loan_cpd, Payment_history_cpd, Income_level_cpd)

# model list , name-> object
model_list = { "student":student_model, "fraud":fraud_model, "credit":credit_approval_model}

student={"L":"Letter","D":"Difficulty","G":"Grade","I":"Intelligence","S":"SAT Scores"}

fraud={"F":"Fraud","J":"Jewellery","A":"Age","S":"Sex"}

credit={"OL":"Outstanding Loan","PH":"Payment History","IL":"Income level","IR":"Interest Rate"}

def convert_to_num(probabitlity_value):
    if probabitlity_value <= .3:
        return "Low"
    elif probabitlity_value > .3 and probabitlity_value <= .7:
        return "Medium"
    else:
        return "High"
