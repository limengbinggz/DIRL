'''
Fit distinct models for Q function approximation for different actions
'''

# Import required libraries
import platform, sys, os, pickle, re
import numpy as np
# from collections import namedtuple
from joblib import Parallel, delayed
sys.path.append("C:/Users/test/Dropbox/tml/IHS/simu") # 引用模块的地址
import simu.compute_test_statistics_separateA as stat
# import simu.compute_test_statistics as stat
from itertools import product
from copy import copy
from random import sample
from scipy.spatial.distance import pdist

# importlib.reload(stat)
#%%
def split_train_test(n, fold = 5, random=True):
    '''
    split data into n-fold training and test data
    :param n: sample size of the original data
    :param fold: integer, number of folds
    :return: a list of nfold elements, each element is a list of indices
    '''
    if random:
        seq = np.random.permutation(range(n)).tolist()
        """Yield n number of sequential chunks from seq."""
        d, r = divmod(n, fold)
        for i in range(fold):
            si = (d + 1) * (i if i < r else r) + d * (0 if i < r else i - r)
            yield seq[si:si + (d + 1 if i < r else d)]
    else:
        seq = list(range(n))
        """Yield n number of sequential chunks from seq."""
        d, r = divmod(n, fold)
        for i in range(fold):
            si = (d + 1) * (i if i < r else r) + d * (0 if i < r else i - r)
            yield seq[si:si + (d + 1 if i < r else d)]
            
def gaussian_rbf_distance(x1, x2, bandwidth = 1.0):
    return np.exp(- bandwidth * np.sum((x1 - x2) ** 2))



def train_test(States_input, Rewards_input, Actions_input, test_index, num_basis = 0, bandwidth = 1.0,
          qmodel='polynomial', gamma=0.95, model=None, max_iter=300, tol=1e-4, metric = 'ls'):

    # n_actions = len(np.unique(Actions_input))
    #%% training
    # extract training data
    # test_index.sort()
    # print('test_index, ',test_index)
    # print('States_input[0].shape[1], ',States_input[0].shape[1])
    if type(States_input) is not list:
    # if States.shape[0] >4:
        States_train = np.delete(States_input, (test_index), axis=0)
        Rewards_train = np.delete(Rewards_input, (test_index), axis=0)
        Actions_train = np.delete(Actions_input, (test_index), axis=0)
        a_unique = np.unique(Actions_train)
        q = stat.q_learning(States_train, Rewards_train, Actions_train, qmodel, num_basis, gamma, num_basis, bandwidth)
        del States_train, Rewards_train, Actions_train
    elif  States_input[0].shape[1] > 1:
        # States_train_current = States[0]
        # States_train_next = States[1]
        States_train_current = np.delete(States_input[0], (test_index), axis=1)
        # States_train_current = States_train_current[:, :-1 or None, :]
        States_train_next = np.delete(States_input[1], (test_index), axis=1)
        # States_train_next = States_train_next[:, 1:, :]
        Rewards_train = np.delete(Rewards_input, (test_index), axis=1)
        Actions_train = np.delete(Actions_input, (test_index), axis=1)
        a_unique = np.unique(Actions_train)
        q = stat.q_learning(States_train_current, Rewards_train, Actions_train, qmodel, num_basis, gamma, num_basis, bandwidth, States_next=States_train_next)
        del States_train_current, States_train_next, Rewards_train, Actions_train
    # print(Actions.shape)
    else:
        # States_train_current = States[0]
        # States_train_next = States[1]
        States_train_current = np.delete(States_input[0], (test_index), axis=0)
        # States_train_current = States_train_current[:, :-1 or None, :]
        States_train_next = np.delete(States_input[1], (test_index), axis=0)
        # States_train_next = States_train_next[:, 1:, :]
        Rewards_train = np.delete(Rewards_input, (test_index), axis=0)
        Actions_train = np.delete(Actions_input, (test_index), axis=0)
        a_unique = np.unique(Actions_train)
        q = stat.q_learning(States_train_current, Rewards_train, Actions_train, qmodel, num_basis, gamma, num_basis, bandwidth, States_next=States_train_next)
        del States_train_current, States_train_next, Rewards_train, Actions_train

    q_function_list = q.fit(model, max_iter, tol).q_function_list

    # %% testing
    if type(States_input) is not list:
    # if States.shape[0] >1:
        States_test = States_input[test_index, :, :]
        Rewards_test = Rewards_input[test_index, :]
        Actions_test = Actions_input[test_index, :]
        q1 = stat.q_learning(States_test, Rewards_test, Actions_test,
                              qmodel, num_basis, gamma, num_basis, bandwidth)
    elif States_input[0].shape[1] > 1:
        States_test_current = States_input[0][:,test_index, :]
        States_test_next = States_input[1][:,test_index, :]
        Rewards_test = Rewards_input[:,test_index]
        Actions_test = Actions_input[:,test_index]
        q1 = stat.q_learning(States_test_current, Rewards_test, Actions_test,
                              qmodel, num_basis, gamma, num_basis, bandwidth, States_next =States_test_next)

    else:
        States_test_current = States_input[0][test_index, :, :]
        States_test_next = States_input[1][test_index,:, :]
        Rewards_test = Rewards_input[test_index, :]
        Actions_test = Actions_input[test_index, :]
        q1 = stat.q_learning(States_test_current, Rewards_test, Actions_test,
                              qmodel, num_basis, gamma, num_basis, bandwidth, States_next =States_test_next)

    # predict the Q value for the next time and find out the maximum Q values for each episode
    Q_max = np.ones(shape=q1.Rewards_vec.shape) * (-999)
    for a in a_unique:
        # print(a)
        a = int(a)
        # predict the Q value for the next time and find out the maximum Q values for each episode
        Q_max = np.maximum(q_function_list[a].predict(q1.States1[0]), Q_max)
    # Q_max = np.asarray([model.predict(q1.States1_action0),
    #                     model.predict(q1.States1_action1)]).max(0)

    # temporal difference error
    # n_actions = len(np.unique(q1.Actions))
    predicted_q_current = np.zeros(shape=q1.Rewards_vec.shape)
    # print('q1.action_indices',q1.action_indices)
    # print('q1.States0',q1.States0)
    # print(n_actions)
    for a in np.unique(q1.Actions):
        # print("q1.action_indices[",a,"] =",q1.action_indices[a])
        # print("q_function_list[",a,"] =",q_function_list[a])
        # print("q1.States0[",a,"] =",q1.States0[a])
        # a_q1=np.where(np.unique(q1.Actions) == a)[0].item()
        # print('q1.States0[int(',a,')]',q1.States0[int(a)].shape, 'q1.States0[int(a)]',q1.States0[int(a)].shape)
        # print('q_function_list[int(a)]', q_function_list[int(a)])
        # if len(q1.States0[int(a)] )>0:
        if a in a_unique:
            predicted_q_current[q1.action_indices[int(a)]] = q_function_list[int(a)].predict(q1.States0[int(a)])
    tde = Rewards_test.flatten() + gamma * Q_max - predicted_q_current
    if metric == 'kerneldist':
        def distance_function_state(x1,x2):
            return gaussian_rbf_distance(x1, x2, bandwidth)
        def distance_function_action(x1,x2):
            return abs(x1 - x2)
        def tde_product(x1, x2):
            return x1 * x2
        if type(States_input) is not list:
        # if States.shape[0] >1:
            States_stack = States_input[test_index, :-1, :].transpose(2, 0, 1).reshape(States_input.shape[2], -1).T
        # else:
        elif States_input[0].shape[1] > 1:
            States_stack = States_input[0][:,test_index, :].reshape((-1,1))#.transpose(2, 0, 1).reshape(States.shape[2], -1).T
        else:
            States_stack = States_input[0][test_index,:, :].reshape((-1,1))
        # print('Actions.shape', Actions.shape)
        # Actions_vec = Actions[test_index, :].flatten()
        Actions_vec = Actions_test.flatten()
        K_states = pdist(States_stack, metric=distance_function_state)
        K_actions = pdist(Actions_vec.reshape(-1, 1), metric=distance_function_action)
        tdes = pdist(tde.reshape(-1, 1), metric=tde_product)
        K_total = np.sum((1.0 + K_actions + K_states + K_actions * K_states) * tdes)
        K_total /= (tde.shape[0] * (tde.shape[0] - 1) / 2)

    elif metric == 'ls':
        # compute TD target
        # get the mse of the least square loss in the last iteration
        K_total = np.mean(tde ** 2)
#%%
    return K_total


#%% cross validation for kernel regression method
def train_test_kernel(States, Rewards, Actions, test_index, sampled_time_points, num_basis = 1, bandwidth = 1.0,
          qmodel='polynomial', gamma=0.95, model=None, max_iter=300, tol=1e-4, metric = 'ls'):

    n_actions = len(np.unique(Actions))
    #%% training
    # extract training data
    States_train = np.delete(States, (test_index), axis=0)
    Rewards_train = np.delete(Rewards, (test_index), axis=0)
    Actions_train = np.delete(Actions, (test_index), axis=0)
    q = stat.q_learning(States_train[:,sampled_time_points,:], Rewards_train[:,sampled_time_points[:-1]], Actions_train[:,sampled_time_points[:-1]],
                        qmodel, num_basis, gamma, num_basis, bandwidth, n_actions)
    N = States_train.shape[0]
    q.States1 = q.create_design_matrix(States = States_train[:,sampled_time_points+1,:],
                                       Actions= np.zeros((N, len(sampled_time_points)-1), dtype='int32'), type='current')
    del States_train, Rewards_train, Actions_train
    # gc.collect()
    qfit = q.fit(model, max_iter, tol)

    # %% testing
    States_test = States[test_index, :, :]
    Rewards_test = Rewards[test_index, :]
    Actions_test = Actions[test_index, :]
    q1 = stat.q_learning(States_test[:, sampled_time_points, :], Rewards_test[:, sampled_time_points[:-1]], Actions_test[:, sampled_time_points[:-1]],
                         qmodel, num_basis, gamma, num_basis, bandwidth, n_actions)
    N = len(test_index)
    q1.States1 = q.create_design_matrix(States = States_test[:, sampled_time_points+1,:],
                                        Actions= np.zeros((N, len(sampled_time_points)-1), dtype='int32'), type='current')
    Q_max = np.ones(shape=q1.Rewards_vec.shape) * (-999)
    for a in range(n_actions):
        # predict the Q value for the next time and find out the maximum Q values for each episode
        Q_max = np.maximum(q.q_function_list[a].predict(q1.States1[0]), Q_max)

    # temporal difference error
    predicted_q_current = np.zeros(shape=q1.Rewards_vec.shape)
    for a in range(n_actions):
        predicted_q_current[q1.action_indices[a]] = q.q_function_list[a].predict(q1.States0[a])
    tde = Rewards_test[:, sampled_time_points[:-1]].flatten() + gamma * Q_max - predicted_q_current

    if metric == 'kerneldist':
        def distance_function_state(x1,x2):
            return gaussian_rbf_distance(x1, x2, bandwidth)
        def distance_function_action(x1,x2):
            return abs(x1 - x2)
        def tde_product(x1, x2):
            return x1 * x2
        States_stack = States_test[:, sampled_time_points[:-1], :].transpose(2, 0, 1).reshape(States.shape[2], -1).T
        Actions_vec = Actions_test[:, sampled_time_points[:-1]].flatten()
        K_states = pdist(States_stack, metric=distance_function_state)
        K_actions = pdist(Actions_vec.reshape(-1, 1), metric=distance_function_action)
        tdes = pdist(tde.reshape(-1, 1), metric=tde_product)
        K_total = np.sum((1.0 + K_actions + K_states + K_actions * K_states) * tdes)
        K_total /= (tde.shape[0] * (tde.shape[0] - 1) / 2)

    elif metric == 'ls':
        # compute TD target
        # get the mse of the least square loss in the last iteration
        K_total = np.mean(tde ** 2)

    return K_total

    # # compute TD target
    # loss = np.mean((Rewards_test[:, sampled_time_points[:-1]].flatten() + gamma * Q_max - model.predict(q1.States0)) ** 2)
    #
    # return loss

def select_model_cv(States, Rewards, Actions, param_grid, bandwidth = None,
                    qmodel='polynomial', gamma=0.95, model=None, max_iter=300, tol=1e-4,
                    nfold = 2, num_threads = 3,
                    metric = 'ls', num_basis = 1, verbose=False,
                    kernel_regression=False, sampled_time_points=None):
    if len(States.shape) == 2:
        States = States.reshape((1, States.shape[0], -1))
    # print('Actions.shape', Actions.shape)
    # if  Actions.shape[1]  == 1:
    #     Actions = Actions.reshape((1,-1))
    #     # print('Actions.shape', Actions.shape)
    # if Rewards.shape[1] == 1:
    #     Rewards = Rewards.reshape((1,-1))
    if States.shape[0] > 4: # split on N
        N = States.shape[0]
        test_indices = list(split_train_test(N, nfold))
        States_input=States
        Actions_input =Actions
        Rewards_input = Rewards
    elif Rewards.shape[1] > nfold * 2: # split on T
        print('cv 2')
        T = Rewards.shape[1]
        test_indices = list(split_train_test(T, nfold))
        States_current = States[:,:-1,:].copy()
        States_next = States[:,1:,:].copy()
        States_input=[States_current, States_next]
        Actions_input =Actions
        Rewards_input = Rewards
    else: # split on NT
        print('cv 3')
        States_current_stack = States[:, :-1 or None, :].transpose(2, 0, 1).reshape(States.shape[2], -1).T.reshape((-1, 1, 1))
        States_next_stack = States[:, 1:, :].transpose(2, 0, 1).reshape(States.shape[2], -1).T.reshape((-1, 1, 1))
        Actions_stack = (Actions.flatten()).reshape([-1, 1])
        Rewards_stack = (Rewards.flatten()).reshape([-1, 1])
        NT = Actions_stack.shape[0]
        if NT > nfold*2:
            test_indices = list(split_train_test(NT, nfold))
            States_input=[States_current_stack, States_next_stack]
            Actions_input = Actions_stack
            Rewards_input = Rewards_stack
        else:
            nfold = int(NT/2)
            test_indices = list(split_train_test(NT, nfold))
            States_input=[States_current_stack, States_next_stack]
            print('States_current_stack.shape',States_current_stack.shape)
            Actions_input = Actions_stack
            Rewards_input = Rewards_stack
    # print('Actions.shape', Actions.shape)
        # test_index=test_indices[fold]
    # if N > 50:
    #     num_threads = 1
    # # else:
    # #     num_threads = 5
    # print('test_index =', test_indices[0])

    # expand parameter grid to a list of dictionaries
    def iter_param(param_grid):
        # Always sort the keys of a dictionary, for reproducibility
        items = sorted(param_grid.items())
        if not items:
            yield {}
        else:
            keys, values = zip(*items)
            for v in product(*values):
                params = dict(zip(keys, v))
                yield params

    fit_param_list = list(iter_param(param_grid))
    basemodel = copy(model)
    test_error_list = []
    min_test_error = 1e10
    selected_model = copy(model)
    best_param = fit_param_list[0]
    if (metric == 'kerneldist') and (bandwidth is None):
        if N > 100:  # if sample size is too large
            sample_subject_index = np.random.choice(N, 100, replace=False)
        else:
            sample_subject_index = np.arange(N)
        ### compute bandwidth
        # compute pairwise distance between states for the first piece
        pw_dist = pdist(States[sample_subject_index, :, :].transpose(2, 0, 1).reshape(States.shape[2], -1).T,
                        metric='euclidean')
        bandwidth = 1.0 / np.nanmedian(np.where(pw_dist > 0, pw_dist, np.nan))
        # use the median of the minimum of distances as bandwidth
        # rbf_bw = np.median(np.where(pw_dist > 0, pw_dist, np.inf).min(axis=0))
        if verbose:
            print("Bandwidth chosen: {:.5f}".format(bandwidth))
        del pw_dist

    for fit_param in fit_param_list:
        model = copy(basemodel.set_params(**fit_param))

        # def run_one(fold):
        #     return train_test(States, Rewards, Actions, test_index=test_indices[fold], num_basis=num_basis, bandwidth=bandwidth,
        #                       qmodel=qmodel, gamma=gamma, model=model, max_iter=max_iter, tol=tol, metric=metric)

        if not kernel_regression: # regular FQI
            # print("regular")
            def run_one(fold):
                return train_test(States_input, Rewards_input, Actions_input, test_index=test_indices[fold], num_basis=num_basis, bandwidth=1,
                           qmodel=qmodel, gamma=gamma, model=model, max_iter=max_iter, tol=tol, metric=metric)
        else:
            # print("kernel")
            def run_one(fold):
                return train_test_kernel(States_input, Rewards_input, Actions_input, test_indices[fold], sampled_time_points, num_basis=num_basis, bandwidth=bandwidth,
                           qmodel=qmodel, gamma=gamma, model=model, max_iter=max_iter, tol=tol, metric=metric)
            
        # parallel jobs
        test_errors = Parallel(n_jobs=num_threads, prefer = 'threads')(delayed(run_one)(fold) for fold in range(nfold))
        # print(test_errors)
        # test_errors = []
        # for fold in range(nfold):
        #     print(fold)
        #     test_errors.append(run_one(fold))
        test_error = np.mean(test_errors)
        if verbose:
            print(fit_param)
            print(test_error)

        test_error_list.append(test_error)

        # get the mse of the least square loss in the last iteration
        if test_error < min_test_error:
            min_test_error = test_error
            selected_model = copy(model)
            best_param = fit_param

    out = {'fit_param_list': fit_param_list,
           'test_error_list': test_error_list,
           'best_model': selected_model,
           'best_param': best_param}

    return out


def fitted_Q_evaluation(qlearn_env, Q0=None, max_iter = 200, random_policy=False, agnostic_policy=None):
    Rewards_vec = qlearn_env.Rewards_vec

    if random_policy:
        opt_action = np.random.binomial(1, 0.25, qlearn_env.N*qlearn_env.T).reshape(qlearn_env.N, qlearn_env.T)
        opt_action = opt_action.astype(int)
    else:
        if agnostic_policy is None:
            # opt_action = qlearn_env.optimal().opt_action.reshape(qlearn_env.N, qlearn_env.T)
            next_States = np.zeros(shape = qlearn_env.States.shape)
            next_States[:,:-1,:] = qlearn_env.States[:,1:,:]
            opt_action = qlearn_env.predict(next_States).opt_action.reshape(qlearn_env.N, qlearn_env.T)
            # opt_value0 = qlearn_env.predict(next_States).opt_reward.reshape(qlearn_env.N, qlearn_env.T)
            # opt_value1 = qlearn_env.predict(next_States).opt_reward.reshape(qlearn_env.N, qlearn_env.T)
        else:
            opt_action = np.repeat(agnostic_policy, qlearn_env.N*qlearn_env.T).reshape(qlearn_env.N, qlearn_env.T)
    # print(opt_action[0:5])
    test_design_matrix_next = qlearn_env.create_design_matrix(qlearn_env.States, opt_action, type='next',
                                                              pseudo_actions=None)
    actions = np.unique(opt_action).tolist()

    # create a list of indices to indicate which action is taken
    action_indices = [None for a in range(qlearn_env.n_actions)]
    for a in actions:
        action_indices[a] = np.where(opt_action.flatten() == a)[0]
    # action_indices = [np.where(opt_action.flatten() == a)[0] for a in actions]
    del opt_action
    # randomly initialize Q for FQE
    if Q0 is None:
        Q = copy(qlearn_env.q_function_list)
        # for a in actions:
        #     Q[a].fit(qlearn_env.States0[a], np.zeros(shape=(len(qlearn_env.action_indices[a],))))
    else:
        Q = Q0
        # initialize
        Q.fit(qlearn_env.States0, np.zeros(Rewards_vec.shape))

    Q_old = np.ones(shape=Rewards_vec.shape) * (-999)
    for a in actions:
        Q_old[action_indices[a]] = Q[a].predict(test_design_matrix_next[a])
    # Q_old = Q.predict(test_design_matrix[0])
    Q_new = copy(Q_old)
    for m in range(max_iter):
        Z = Rewards_vec + qlearn_env.gamma * Q_old
        for a in actions:
            Q[a].fit(qlearn_env.States0[a], Z[qlearn_env.action_indices[a]])
            Q_new[action_indices[a]] = Q[a].predict(test_design_matrix_next[a])
        # print(np.mean((Q_new - Q_old) ** 2))
        if (np.mean((Q_new - Q_old)**2) < 1e-7):
            break
        Q_old = copy(Q_new)
        # Q.fit(qlearn_env.States0, Z)
        # Q_new = Q.predict(test_design_matrix)
        # if (np.mean((Q_new - Q_old)**2) < 1e-7):
        #     break
        # Q_old = copy(Q_new)
    # print(m)
    return Q_new

