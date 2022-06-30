import platform, sys, os, re, pickle
import tensorflow as tf
import numpy as np
os.chdir("C:/Users/test/Dropbox/tml/IHS/simu")
sys.path.append("C:/Users/test/Dropbox/tml/IHS/simu") 
from joblib import Parallel, delayed
M = 1
method_list = ['oracle_clusterings']
signal_factor_list = [0.5]
train_episodes = 1
test_size_factor = 1
for signal_factor in signal_factor_list:
  for method in method_list:
      for seed in range(M):
          arg_pass = str(seed) + ' '+ str(signal_factor)+ ' '+ method + ' ' + str(train_episodes) +' ' + str(test_size_factor)
          runfile('simu/dqn_offline.py',args=arg_pass)
#%%
from joblib import Parallel, delayed
import multiprocessing
num_threads=multiprocessing.cpu_count()

method_list = ['oracle']
M = 2
signal_factor_list = [1]
train_episodes = 20
test_size_factor = 1
def run_one(seed, signal_factor, method):    
    !python simu/dqn_offline.py $seed $signal_factor $method $train_episodes $test_size_factor
    return
Parallel(n_jobs=num_threads, prefer = 'threads')(delayed(run_one)(seed,signal_factor, method) for seed in range(5,20) for signal_factor in signal_factor_list for method in method_list)