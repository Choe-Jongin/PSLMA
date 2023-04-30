import os
import sys
import multiprocessing
import time

import part_list as pl
from cast_data_file import DataFile

#global settings
DATA_DIR="~/data"
FEMU_ID_IP="-p 8080 femu@166.104.246.86"
REMOTE_ID_IP="jongin@166.104.246.86"

SCRIPT_DIR="/scripts"
workloads={}
workloads['M1'] = "fio"

workloads['R1'] = "vdbench-read"
workloads['R2'] = "vdbench-web"
workloads['R3'] = "ycsb-a"
workloads['R4'] = "ycsb-d"
workloads['R5'] = "ycsb-f"
workloads['R6'] = "filebench-webproxy"

workloads['W1'] = "sysbench"
workloads['W2'] = "filebench-fileserver"
workloads['W3'] = "filebench-varmail"
workloads['W4'] = "vdbench-write"

pre=[]
run=[]

target_workload=[]
target_datasize = "4G"
target_time = "300"

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
    print("SIZE :", target_datasize, "TIME :", target_time)
        
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
    # print( "[ DEBUG ]ssh:"+command )
    ssh_command = 'ssh ' + FEMU_ID_IP + ' "'+command+'"'
    print( "[ DEBUG ]"+ssh_command)
    os.system(ssh_command)
    time.sleep(0.1)

## send command to host server ##
def ssh_exec_to_host(command):
#    print( "[ DEBUG ]ssh:"+command )
    os.system('ssh ' + REMOTE_ID_IP + ' "'+command+'"')
    time.sleep(0.1)

## load dataset ##
def prepare_task():
    print("[preparing]")
    
    threads=[]
    for p in pre:
        threads.append(multiprocessing.Process(target=ssh_exec, args=(p + "&",)))
        
    for th in threads:
        th.start()

    start_time = time.time()
    for th in threads:
        th.join(int(target_time) - (time.time() - start_time) + 100)
        if th.is_alive():
            print("TIME OUT")
    
## run workload ##
def run_task():
    print("****************************************************************")
    print("[run]")
    time.sleep(1)
    
    threads=[]
    for r in run:
        threads.append(multiprocessing.Process(target=ssh_exec, args=(r + "&",)))
        
    for th in threads:
        th.start()
        
    start_time = time.time()
    for th in threads:
        th.join(int(target_time) - (time.time() - start_time) + 100)
        if th.is_alive():
            print("TIME OUT")

## get data file ##
def copy_data_file(partitioning):
    global DATA_DIR
    scenario_data_dir = DATA_DIR + "/data_" + get_workloads_str()
    if scenario_data_dir[0] == '~':
        scenario_data_dir = os.path.expanduser('~')+scenario_data_dir[1:]
    
    if (os.path.isdir(scenario_data_dir) == False):
        os.system("mkdir " + scenario_data_dir)

    partitioning=partitioning.rstrip()
    partitioning=partitioning.replace(" ", "_")
    cpu_data_file_name = scenario_data_dir+"/"+get_workloads_str()+"_cpu_"+partitioning+".cpudata"
    os.system("touch " + cpu_data_file_name)
    os.system('ssh ' + FEMU_ID_IP + ' "sudo cat /pblk-cast_perf/cpu.data" > ' + cpu_data_file_name)
    
    cpu_data_file = open(cpu_data_file_name, 'r')
    # Fail to copy or test
    if cpu_data_file.read().count("\n") <= int(target_time)*0.9 :
        os.system("rm " + cpu_data_file_name)
        cpu_data_file.close()
        print("invalid cpu_data_file")
        return "retry"
    
    # copy each data files
    print("copy", cpu_data_file_name) 
    for i in range(len(target_workload)):
        data_file_name    =  scenario_data_dir+"/"+get_workloads_str()+"_"+partitioning+"_"+str(i)+".data"
        latency_file_name =  scenario_data_dir+"/"+get_workloads_str()+"_"+partitioning+"_"+str(i)+".latency"
        os.system("touch " + data_file_name)
        os.system("touch " + latency_file_name)
        os.system('ssh ' + FEMU_ID_IP + ' "sudo cat /pblk-cast_perf/mydev'+str(i)+'.data" > ' + data_file_name)
        os.system('ssh ' + FEMU_ID_IP + ' "sudo cat /sys/block/mydev'+str(i)+'/pblk/latency" > ' + latency_file_name)
        print("copy", data_file_name, latency_file_name)
        time.sleep(0.1)
        
        # File Validation Check
        data_file = DataFile(data_file_name)        
        if data_file.last_none_zero_line <= int(target_time)*0.9:
            os.system("rm " + cpu_data_file_name)
            os.system("rm " +  scenario_data_dir+"/"+get_workloads_str()+"_"+partitioning+"_*.data")
            os.system("rm " +  scenario_data_dir+"/"+get_workloads_str()+"_"+partitioning+"_*.latency")
            print("invalid file :", data_file_name)
            return "retry"
        
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
            print("\033[01m\033[31mAllocation("+str(psl.index(ps)+1) + "/" + str(len(psl))+") : " + ps, "\033[0m")
            print("start FEMU VM")
            time.sleep(3)
            
            femu_thread = multiprocessing.Process(target=ssh_exec_to_host, args=("cd ~/femu/build-femu/ && ~/femu/build-femu/run-whitebox.sh -b",))
            femu_thread.start()
            
            for i in range(100):
                time.sleep(1)
                print("\rwait..." +str(100-i)+"   ",end="")
            print("")
            
            #terminal correcting
            os.system("stty sane")

            #ssh test
            ssh_exec("echo FEMU VM connected")

            #docker close first
            ssh_exec("sudo docker rm \$(sudo docker ps -aq) -f")
            
            #mount
            ssh_exec("sudo /mount.sh "+ps)

            #prepare
            try:
                prepare_task()
            except KeyboardInterrupt:
                print("exit prepare")
            
            #active
            ssh_exec('sudo echo 1 | sudo tee /sys/block/mydev0/pblk/cast_active');

            #run
            try:
                run_task()
            except KeyboardInterrupt:
                print("exit run")

            #docker close
            ssh_exec("sudo docker rm \$(sudo docker ps -aq) -f")
            
            #inactive
            ssh_exec('sudo echo 0 | sudo tee /sys/block/mydev0/pblk/cast_active');
            
            #copy data
            if copy_data_file(ps) == "retry":
                print(ps, "Fail...")
                print("\033[01m\033[31mretry\033[0m")
                test = True
            
            #unmount
            #time.sleep(10)
            # unmount_thr = multiprocessing.Process(target=ssh_exec, args=('sudo /unmount.sh',))
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
        elif arg == "full" or arg == "-full":            # full exploring
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
            i = i+len(target_workload)
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