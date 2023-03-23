#!/usr/bin/phtyon3

import os
import sys
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
        data_file_name = DATA_DIR+"/wl_"+partitioning+str(i)+".data"
        latency_file_name = DATA_DIR+"/wl_"+partitioning+str(i)+".latency"
        os.system("touch " + data_file_name)
        os.system("touch " + latency_file_name)
        os.system('ssh -p 8080 femu@localhost "sudo cat /pblk-cast_perf/mydev'+str(i)+'.data" > ' + data_file_name)
        os.system('ssh -p 8080 femu@localhost "sudo cat /sys/block/mydev'+str(i)+'/pblk/latency" > ' + latency_file_name)
        time.sleep(0.1)

#### MAIN ####
def exploing(psl):
    
    for ps in psl:
        print("case : " + ps)
        print("start FEMU VM")
        os.system("cd /home/femu/femu/build-femu/ && /home/femu/femu/build-femu/run-whitebox.sh -b&")
        time.sleep(100)

        #terminal correcting
        os.system("stty sane")

        #ssh test
        ssh_exec("echo FEMU VM connected")

        #mount
        ssh_exec("sudo /mount.sh "+ps)

        #prepare
        prepare_tast()
        
        #active
        ssh_exec('sudo echo 1 | sudo tee /sys/block/mydev0/pblk/cast_active');

        #run
        run_task()

        #copy data
        copy_data_file(ps)

        #docker close
        ssh_exec("sudo docker rm \$(sudo docker ps -aq) -f")
        
        #inactive
        ssh_exec('sudo echo 0 | sudo tee /sys/block/mydev0/pblk/cast_active');

        #unmount
        unmount_thr = Thread(target=ssh_exec, args=('sudo /unmount.sh',))
        unmount_thr.start()
        for _ in range(10) :
            if unmount_thr.is_alive() :
                time.sleep(1)
            else :
                break
        
        #shutdown 
        print("shutdown FEMU VM")
        ssh_exec("sudo shutdown now")

        time.sleep(30)

#### entry point ####

#entry point(first call)
if __name__ == '__main__':
    if len(sys.argv) <= 2 :
        exploing(pl.part_list(N, False))
    elif sys.argv[1] == "full" :
        exploing(pl.part_list(N, True))
    else:
        p = ""
        for i in sys.argv[1:]:
            p+=i+" "
        exploing([p])
        
    print("Finish")