#!/usr/bin/phtyon3

import os
from threading import Thread
import time
import part_list as pl

#global settings
DATA_DIR="/home/femu/data"
N=3

pre=[]
run=[]

pre+=("bash /script/test_ready.sh 0")
pre+=("bash /script/test_ready.sh 1")
pre+=("bash /script/test_ready.sh 2")

pre+=("bash /script/test_run.sh 0 1 "+str(10))
pre+=("bash /script/test_run.sh 0 2 "+str(10))
pre+=("bash /script/test_run.sh 0 3 "+str(10))

## send command to femu vm ##
def ssh_exec(command):
    os.system("ssh -p 8080 femu@localhost "+command)

## load dataset ##
def prepare_tast():
    threads=[]
    print("preparing")
    for p in pre:
        th = Thread(target=ssh_exec, args=(p+"&"))
        th.start()
        threads.append(th)
        
    #join
    for th in threads:
        th.join()

## run workload ##
def run_task():
    threads=[]
    print("run")
    for r in run:
        th = Thread(target=ssh_exec, args=(r+"&"))
        th.start()
        threads.append(th)

    #join
    for th in threads:
        th.join()

## get data file ##
def copy_data_file(partitioning):
    partitioning=partitioning.replace(" ", "_")

    for i in range(N):
        os.system("touch "+DATA_DIR+"/wl_"+partitioning+str(i)+".txt")
        ssh_exec("sudo cat /pblk-cast_perf/mydev"+str(i)+".data > "+DATA_DIR+"/wl_"+partitioning+str(i)+".txt")

#### MAIN ####
def exploing(full = False):
    
    psl = pl.part_list(N, full)
    for ps in psl:

        print("start FEMU VM")
#        os.system("cd /home/femu/femu/build-femu/")
#        os.system("sudo /home/femu/femu/build-femu/run-whitebox.sh -b&")
#        time.sleep(120)

        #terminal correcting
        os.system("stty sane")

        #ssh test
        ssh_exec("echo FEMU VM connected")

        #mount
        ssh_exec("sudo /mount.sh "+ps)

        #prepare
        prepare_tast()

        #run
        run_task()

        #copy data
        copy_data_file(ps)

        ssh_exec("sudo docker rm \$(sudo docker ps -aq) -f")

        #unmount
        ssh_exec("sudo /unmount.sh")

        #shutdown 
        print("shutdown FEMU VM")
        ssh_exec("sudo shutdown now")

#        time.sleep(60)
    
exploing()
print("Finish")
