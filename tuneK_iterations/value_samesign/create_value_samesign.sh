#!/bin/bash
cd /home/huly0209_gmail_com/heterRL/tuneK_iterations/value_samesign

Ns=(100)
T_new=250 
cov=0.25
nthread=8
cp_detect_interval=25
is_tune_parallel=0
is_cp_parallel=1
run=true
# 1: type 2: N, 3: T_new, 4: setting, 5: nthread, 6:cov, 7: cp_detect_interval, 8: is_tune_parallel, 9: is_cp_parallel, 10: effect_size
write_slurm() {
    echo "#!/bin/bash
#SBATCH --job-name=va_$1_$4_cp$7
#SBATCH --time=100:00:00
#SBATCH --mail-type=END,FAIL,BEGIN
#SBATCH --mem=3g
#SBATCH --cpus-per-task=$5
#SBATCH --array=0-19
#SBATCH -o ./reports/%x_%A_%a.out 

cd /home/huly0209_gmail_com/heterRL/tuneK_iterations/value_samesign

python3 run_value_samesign.py \$SLURM_ARRAY_TASK_ID $1 $2 $3 $4 $5 $6 $7 $8 $9 ${10}
" > value_$1_N$2_T$3_set$4_cov$6_cpinterv$7_${10}.slurm
if ${run}
then
    sbatch value_$1_N$2_T$3_set$4_cov$6_cpinterv$7_${10}.slurm
fi
}


for N in "${Ns[@]}"; do
    for type in "proposed" "only_clusters"; do # "only_cp"  "overall" "oracle" ; do  
        for setting in "pwconst2" "smooth"; do # 
            for effect_size in "strong"; do
                 write_slurm ${type} ${N} ${T_new} ${setting} ${nthread} ${cov} ${cp_detect_interval} ${is_tune_parallel} ${is_cp_parallel} ${effect_size}
             done
         done
    done
done
	

