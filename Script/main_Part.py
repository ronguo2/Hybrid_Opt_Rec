"""

Objective function: Passenger time cost + passenger fare
Constraint: Non-negative agency revenue
Designing iterative algorithms to derive four types of passenger ratios, elastic demand, and cost components
Enumeration method to find the optimal solution

decision variable：
x2:FareFlex_f2
H1: HeadwayFixed_H1
H2: HeadwayFlex_H2
"""
from cmath import log
from math import fabs
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import para    # set parameters
import funs
import time


def ini_total_area_demand():
    """
        set the intial travel demand
        use the base demand as the intial value
    """

    fare = np.array(np.arange(2, 20.1, 0.1))
    H1 = np.array(np.arange(0.01, 1.01, 0.01))
    H2 = np.array(np.arange(0.01, 1.01, 0.01))
    potential_total_demand = np.array(np.arange(20, 201, 20))


    H2_len = len(H2)
    H1_len = len(H1)
    x2_len = len(fare)
    demand = np.repeat(potential_total_demand, H1_len * x2_len * H2_len)

    return demand
    pass

def ini_passenger_demand(demand):
    """
        set the intial passengers demand
        evenly distributed the demand to each type of passngers
    """
    IniPassenger_1 = 0.25*demand
    IniPassenger_2 = 0.25*demand
    IniPassenger_3 = 0.25*demand
    IniPassenger_4 = 0.25*demand
    FlexPassen = IniPassenger_2+IniPassenger_3+IniPassenger_4
    pas_type_flow = np.stack([IniPassenger_1, IniPassenger_2, IniPassenger_3, IniPassenger_4, FlexPassen], axis=1)

    return pas_type_flow
    pass

def cal_utility(H1,H2, fare ,FlexPassen):
    """
        given the headway, fare and demand
        compute the cost element for each type of passengers
    """

    DistFixed_d1 = 2 * para.AreaLength_D / H1
    DistFlex_d2 = 2.5 * para.AreaLength_D / H2 + 4 * para.AreaLength_D * para.AreaSide_s ** 2 * FlexPassen/ 3

    WalkDist_l1 = para.AreaSide_s * 2
    WalkDist_l2 = WalkDist_l1 / 2

    WalkTime_A1 = WalkDist_l1 / para.WalkSpeed_vw
    WalkTime_A2 = WalkDist_l2 / para.WalkSpeed_vw

    WaitTime_W1 = H1 / 2
    WaitTime_W2 = H2 / 2 + H1 / 2
    WaitTime_W4 = H2 + H1 / 2

    radio = DistFlex_d2 / (2 * para.AreaLength_D / H2)

    TraDistFixed_r1 = 0.34 * para.AreaLength_D
    TraDistFlex_r2 = radio * WalkDist_l2

    TravTime_T1 = TraDistFixed_r1 / para.VehSpeed_v
    TravTime_T2 = (TraDistFixed_r1 + TraDistFlex_r2) / para.VehSpeed_v
    TravTime_T4 = (TraDistFixed_r1 + TraDistFlex_r2 * 2) / para.VehSpeed_v

    # logit model
    Utility_1 = (para.wA * WalkTime_A1 + para.wW * WaitTime_W1 + para.wT * TravTime_T1) * para.value_time + para.wf * para.FareFixed_f1
    Utility_2 = (para.wA * WalkTime_A2 + para.wW * WaitTime_W2 + para.wT * TravTime_T2) * para.value_time + para.wf *fare
    Utility_3 = Utility_2
    Utility_4 = (para.wW * WaitTime_W4 + para.wT * TravTime_T4) * para.value_time + para.wf * (fare + para.FareFixed_f1)

    Choice_1 = np.exp(- para.thet * Utility_1)
    Choice_2 = np.exp(- para.thet * Utility_2)
    Choice_3 = Choice_2
    Choice_4 = np.exp(- para.thet * Utility_4)

    TotalChoice = Choice_1 + Choice_2 + Choice_3 + Choice_4


    PassengerType_p1 = Choice_1 / TotalChoice
    PassengerType_p2 = Choice_2 / TotalChoice
    PassengerType_p3 = Choice_3 / TotalChoice
    PassengerType_p4 = Choice_4 / TotalChoice

    # expected user cost
    WalkTime_A = WalkTime_A1 * PassengerType_p1 + WalkTime_A2 * PassengerType_p2 * 2
    WaitTime_W = WaitTime_W1 * PassengerType_p1 + WaitTime_W2 * PassengerType_p2 * 2 + WaitTime_W4 * PassengerType_p4
    TravelTime_T = TravTime_T1 * PassengerType_p1 + TravTime_T2 * PassengerType_p2 * 2 + TravTime_T4 * PassengerType_p4
    SingleFare = para.FareFixed_f1 * (PassengerType_p1 + PassengerType_p4) + fare * (PassengerType_p2 * 2 + PassengerType_p4)

    AverageUtility = (para.wA *WalkTime_A + para.wW * WaitTime_W +  para.wT *TravelTime_T) +para.wf *SingleFare/para.value_time

    TraDistFixed_r1 = np.repeat(TraDistFixed_r1, len(fare))

    travel_utility=np.stack([Choice_1, Choice_2, Choice_3, Choice_4,
                             AverageUtility,TotalChoice,
                             WalkTime_A,WaitTime_W,TravelTime_T,
                             PassengerType_p1,PassengerType_p2,PassengerType_p3,PassengerType_p4,
                             DistFixed_d1,DistFlex_d2,TraDistFixed_r1,TraDistFlex_r2,SingleFare,
                             Utility_1,Utility_2,Utility_3,Utility_4], axis=1)

    return travel_utility

def update_pass_demand(utility, demand):
    """
        update passenger type demand based on updated utility
    """
    UpdatePassenger_1 = utility[:,0] / utility[:,5]*demand
    UpdatePassenger_2 = utility[:,1] / utility[:,5]*demand
    UpdatePassenger_3 = utility[:,2] / utility[:,5]*demand
    UpdatePassenger_4 = utility[:,3] / utility[:,5]*demand
    FlexPassen = UpdatePassenger_2+UpdatePassenger_3+UpdatePassenger_4

    update_pass_demand=np.stack([UpdatePassenger_1, UpdatePassenger_2,
                                 UpdatePassenger_3, UpdatePassenger_4,FlexPassen], axis=1)

    return update_pass_demand

def compute_MSA_map_y1(x0 ,H1,H2 ,fare,demand):
    """
        x0 is the pass type demand for current iteration
        y1 is the pass type demand updated
    """
    utility = cal_utility(H1, H2, fare, x0)
    y1 = update_pass_demand(utility,demand)[:,-1]

    return y1

def check_MSA_convergence(X0 ,Y1):
    """
        compute the convergence for the msa
    """
    gap = np.max(np.abs(Y1 - X0))

    return gap

def route_choice_equlibrium_MSA(demand ,H1,H2,fare,MSA_data):
    """
        under one demand setting, use MSA to compute the convergence of the route flow
    """
    max_msa_iter = 100
    x0 = ini_passenger_demand(demand)[:,-1]

    for iter in range(1, max_msa_iter):
        y1 = compute_MSA_map_y1(x0,H1,H2,fare,demand)
        MSA_data.append([iter, check_MSA_convergence(x0, y1)])
        # print('MSA_gap: ',check_MSA_convergence(x0, y1))
        if check_MSA_convergence(x0, y1) < 1:
            break
        else:
            x0 = x0+ ( 1 /iter ) *(y1 -x0)

    utility = cal_utility(H1,H2 ,fare ,x0)

    return utility

def elastic_demand_fun(utility, demand):
    """
        given utility compute the update demand
    """
    update_pass_demand = demand - para.psi * (-1 / para.thet) * (np.log(utility[:, 5]))

    return update_pass_demand

def update_elastic_demand(current_elastic_demand,demand, H1,H2, fare,MSA_data):
    """
        update elastic demand
    """
    utility = route_choice_equlibrium_MSA(current_elastic_demand ,H1,H2 ,fare,MSA_data)

    return (elastic_demand_fun(utility, demand))

def compute_elastic_demand_gap(last_demand, update_demand,H1, H2, fare):
    """
        the gap is defined by the difference between the two iterations
    """
    gap = np.max(np.abs(update_demand - last_demand))

    return gap
def elastic_demand_Iteration(H1,H2, fare, demand,MSA_data):
    """
        iterative procedure for the elastic demand
    """
    ElasIteration_data = []

    iter = 0
    max_iter =50
    target_gap = 0.001
    x0 = ini_total_area_demand()
    y1 = update_elastic_demand(x0,demand,H1,H2, fare,MSA_data)
    gap = compute_elastic_demand_gap(x0, y1,H1, H2, fare)

    while gap > target_gap and iter < max_iter:
        x0 = y1
        y1 = update_elastic_demand(x0,demand, H1,H2, fare,MSA_data)
        gap = compute_elastic_demand_gap(x0, y1,H1, H2, fare)
        iter = iter + 1
        ElasIteration_data.append([iter, gap])

    final_demand = update_elastic_demand(y1,demand,H1,H2, fare,MSA_data)
    final_utility = route_choice_equlibrium_MSA(final_demand, H1,H2, fare,MSA_data)

    # after convergence return the final demand and uitlity
    return final_demand,final_utility
    pass


def evaluate_main(H1,H2, fare, potential_total_demand):
    """
        evaluate one enumerate setting
        the demand input is potential demand
    """

    MSA_data = []
    final_demand,final_utility = elastic_demand_Iteration(H1,H2, fare, potential_total_demand,MSA_data)

    # The four types of ridership ratios and the corresponding cost components are derived

    # Then, Calculate fleet size, user cost, agencycost, and agency revenue.


    return # Output the values

def Test_lamda(_Test_Save_Folder_Name: str):

    #
    fare = np.array(np.arange(2, 20.1, 0.1))
    H1 = np.array(np.arange(0.01, 1.01, 0.01))
    H2 = np.array(np.arange(0.01, 1.01, 0.01))
    potential_total_demand = np.array(np.arange(20, 201,20))

    H2_len = len(H2)
    H1_len = len(H1)
    x2_len = len(fare)
    Passenger_len = len(potential_total_demand)

    H2 = np.tile(H2, H1_len * x2_len * Passenger_len)
    H1 = np.tile(H1, x2_len * Passenger_len)
    H1 = np.repeat(H1, H2_len)
    fare = np.tile(fare, Passenger_len)
    fare = np.repeat(fare, H2_len * H1_len)


    ans = evaluate_main(H1,H2, fare, potential_total_demand)

#   Finally the enumeration method is used to filter the optimal values of the optimization model

