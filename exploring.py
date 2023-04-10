import os
import sys
from threading import Thread
import time
import part_list as pl

#global settings
DATA_DIR="~/data"

pre=[]
run=[]

SCRIPT_DIR="/scripts"
workloads={}
workloads['A'] = "fio"
workloads['B'] = "filebench-varmail"
workloads['C'] = "filebench-webproxy"
workloads['D'] = "filebench-fileserver"
workloads['E'] = "ycsb-a"
workloads['F'] = "ycsb-d"
workloads['G'] = "ycsb-f"
workloads['H'] = "vdbench-read"
workloads['I'] = "vdbench-write"
workloads['J'] = "vdbench-web"
workloads['K'] = "sysbench"

target_workload=[]
target_datasize = "4G"
target_time = "600"


def get_workloads_str():
    str = ""
    for ch in target_workload:
        str += ch
    return str

def set_data_set(size, time):
    global  target_datasize, target_time
    target_datasize = size
    target_time = str(time)
    print("set")
    print(target_datasize, target_time)
        
def set_workload():
    if len(target_workload) == 0:
        print("target workload is empty")
        return 
    
    print(target_datasize, target_time)
    for i in range(len(target_workload)):
        id = target_workload[i]
        pre.append("sudo bash "+ SCRIPT_DIR+"/"+workloads[id]+"_pre.sh "+target_datasize+ " " +target_time+ " " +str(i))
        run.append("sudo bash "+ SCRIPT_DIR+"/"+workloads[id]+"_run.sh "+target_datasize+ " " +target_time+ " " +str(i))

## send command to femu vm ##
def ssh_exec(command):
#    print( "[ DEBUG ]ssh:"+command )
    os.system('ssh -p 8080 femu@localhost "'+command+'"')
    time.sleep(0.1)

## load dataset ##
def prepare_task():
    print("preparing")
    
    threads=[]
    for p in pre:
        threads.append(Thread(target=ssh_exec, args=(p,)))
        
    for th in threads:
        th.start()
        
    start_time = time.time()    # for timeout
    for th in threads:
        if time.time - start_time > target_time + 200:
            break
        if th.is_alive() :
            continue
    # for th in threads:
    #     th.join()

## run workload ##
def run_task():
    print("run")
    
    threads=[]
    for r in run:
        threads.append(Thread(target=ssh_exec, args=(r,)))
        
    for th in threads:
        th.start()
        
    start_time = time.time()    # for timeout
    for th in threads:
        if time.time - start_time > target_time + 200:
            break
        if th.is_alive() :
            continue

## get data file ##
def copy_data_file(partitioning):
    partitioning=partitioning.rstrip()
    partitioning=partitioning.replace(" ", "_")
    cpu_data_file_name = DATA_DIR+"/"+get_workloads_str()+"_cpu_"+partitioning+".cpudata"
    os.system("touch " + cpu_data_file_name)
    os.system('ssh -p 8080 femu@localhost "sudo cat /pblk-cast_perf/cpu.data" > ' + cpu_data_file_name)
    
    cpu_data_file = open(cpu_data_file_name, 'r')
    # Fail to copy or test
    if cpu_data_file.read().count("\n") <= target_time*0.8 :
        os.system("rm " + cpu_data_file_name)
        cpu_data_file.close()
        return "retry"
    
    # Success
    print("copy", cpu_data_file_name) 
    for i in range(len(target_workload)):
        data_file_name = DATA_DIR+"/"+get_workloads_str()+"_"+partitioning+"_"+str(i)+".data"
        latency_file_name = DATA_DIR+"/"+get_workloads_str()+"_"+partitioning+"_"+str(i)+".latency"
        os.system("touch " + data_file_name)
        os.system("touch " + latency_file_name)
        os.system('ssh -p 8080 femu@localhost "sudo cat /pblk-cast_perf/mydev'+str(i)+'.data" > ' + data_file_name)
        os.system('ssh -p 8080 femu@localhost "sudo cat /sys/block/mydev'+str(i)+'/pblk/latency" > ' + latency_file_name)
        print("copy", data_file_name, latency_file_name)
        time.sleep(0.1)
        
    return "complete"

#### MAIN ####
def exploing(psl):
    
    for i in range(len(target_workload)):
        print("dev" + str(i) + " : " + workloads[target_workload[i]])
    
    set_workload()
    
    print(pre)
    print(run)
    
    for ps in psl:
        test = True
        while test:
            test = False
            print("case : " + ps)
            print("start FEMU VM")
            os.system("cd ~/femu/build-femu/ && ~/femu/build-femu/run-whitebox.sh -b&")
            time.sleep(120)

            #terminal correcting
            os.system("stty sane")

            #ssh test
            ssh_exec("echo FEMU VM connected")

            #docker close first
            ssh_exec("sudo docker rm \$(sudo docker ps -aq) -f")
            
            #mount
            ssh_exec("sudo /mount.sh "+ps)

            #prepare
            prepare_task()
            
            #active
            ssh_exec('sudo echo 1 | sudo tee /sys/block/mydev0/pblk/cast_active');

            #run
            run_task()

            #docker close
            ssh_exec("sudo docker rm \$(sudo docker ps -aq) -f")
            
            #inactive
            ssh_exec('sudo echo 0 | sudo tee /sys/block/mydev0/pblk/cast_active');
            
            #copy data
            if copy_data_file(ps) == "retry":
                test = True
            
            #unmount
            #time.sleep(10)
            # unmount_thr = Thread(target=ssh_exec, args=('sudo /unmount.sh',))
            # unmount_thr.start()
            # for _ in range(10) :
            #     if unmount_thr.is_alive() :
            #         time.sleep(1)
            #     else :
            #         break
            
            #shutdown 
            print("shutdown FEMU VM")
            ssh_exec("sudo shutdown now")

            time.sleep(30)

#### entry point ####
def main():
    full=False
    p = ""
    size = "4G"
    time = 1800
    step = 1
        
    if len(sys.argv) <= 1 :
        print("No workload specified")
        return
    
    #search arguments
    for i in range(1, len(sys.argv)):
        arg = sys.argv[i]
        if arg == "" :
            continue
        
        if arg in workloads.keys():   # Set Workload
            target_workload.append(arg)
        elif arg == "full" :            # full exploring
            full = True
        elif arg == "-size":
            i = i+1
            size = sys.argv[i]
            sys.argv[i]=""
        elif arg == "-time":
            i = i+1
            time = sys.argv[i]
            sys.argv[i]=""
        elif arg == "-step":
            i = i+1
            step = int(sys.argv[i])
            sys.argv[i]=""
        elif arg == "-case":            # Set custom case
            for part in range(i+1, i+len(target_workload)+1):
                p+=sys.argv[part]+" "
            p=p.rstrip()
        else:                           # invalid argument
            print(arg,"is not defined")
            break
    
    set_data_set(size, time)
    
    #custom case
    if p != "":
        if len(p.split(" ")) != len(target_workload):
            print("N does not match")
            print("target worklods :", len(target_workload), "partition set :", len(p))
            return
        print("test only [", p, "]" )
        exploing([p])
    else:
        exploing(pl.part_list(len(target_workload), step, full))
            
    print("Finish")   
    
#entry point(first call)
if __name__ == '__main__':
    main()