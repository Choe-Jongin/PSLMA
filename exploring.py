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

pre.append("bash /script/test_pre.sh 0")
pre.append("bash /script/test_pre.sh 1")
pre.append("bash /script/test_pre.sh 2")

run.append("bash /script/test_run.sh 0 1 "+str(20))
run.append("bash /script/test_run.sh 1 1 "+str(20))
run.append("bash /script/test_run.sh 2 1 "+str(20))

## send command to femu vm ##
def ssh_exec(command):
#    print( "[ DEBUG ]ssh:"+command )
    os.system('ssh -p 8080 femu@localhost "'+command+'"')

## load dataset ##
def prepare_tast():
    print("preparing")
    
    threads=[]
    for p in pre:
        threads.append(Thread(target=ssh_exec, args=(p+"&",)))
        
    for th in threads:
        th.start()
        
    for th in threads:
        th.join()

## run workload ##
def run_task():
    print("run")
    
    threads=[]
    for r in run:
        threads.append(Thread(target=ssh_exec, args=(r+"&",)))
        
    for th in threads:
        th.start()
        
    for th in threads:
        th.join()

## get data file ##
def copy_data_file(partitioning):
    partitioning=partitioning.replace(" ", "_")

    for i in range(N):
        data_file_name = DATA_DIR+"/wl_"+partitioning+str(i)+".txt"
        os.system("touch " + data_file_name)
        os.system("ssh -p 8080 femu@localhost sudo cat /pblk-cast_perf/mydev"+str(i)+".data" > data_file_name)

#### MAIN ####
def exploing(full = False):
    
    psl = pl.part_list(N, full)
    for ps in psl:
        print("case : " + ps)
        print("start FEMU VM")
        os.system("cd /home/femu/femu/build-femu/ && /home/femu/femu/build-femu/run-whitebox.sh -b&")
        time.sleep(60)

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

        time.sleep(30)
    
exploing()
print("Finish")
