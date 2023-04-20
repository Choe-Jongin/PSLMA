import os
import sys
from threading import Thread
import time
import part_list as pl

#######################################################################
#  TEMPORARY  #  TEMPORARY  #  TEMPORARY  #  TEMPORARY  #  TEMPORARY  #
#######################################################################
#  TEMPORARY  #  TEMPORARY  #  TEMPORARY  #  TEMPORARY  #  TEMPORARY  #
#######################################################################
#  TEMPORARY  #  TEMPORARY  #  TEMPORARY  #  TEMPORARY  #  TEMPORARY  #
#######################################################################
#  TEMPORARY  #  TEMPORARY  #  TEMPORARY  #  TEMPORARY  #  TEMPORARY  #
#######################################################################
#  TEMPORARY  #  TEMPORARY  #  TEMPORARY  #  TEMPORARY  #  TEMPORARY  #
#######################################################################

#global settings
DATA_DIR="~/data"
PSLMA_DIR="~/PSLMA"
REMOTE_ID_IP="femu@166.104.246.86"

## send command to host server ##
def ssh_exec_to_host(command):
#    print( "[ DEBUG ]ssh:"+command )
    os.system('ssh ' + REMOTE_ID_IP + ' "'+command+'"')
    time.sleep(0.1)

## get data file ##
def copy_data_file(partitioning):
    global DATA_DIR
    if DATA_DIR[0] == '~':
        DATA_DIR = os.path.expanduser('~')+DATA_DIR[1:]

    partitioning=partitioning.rstrip()
    partitioning=partitioning.replace(" ", "_")
    cpu_data_file_name = DATA_DIR+"/"+get_workloads_str()+"_cpu_"+partitioning+".cpudata"
    os.system("touch " + cpu_data_file_name)
    os.system('ssh -p 8080 ' + REMOTE_ID_IP + ' "sudo cat /pblk-cast_perf/cpu.data" > ' + cpu_data_file_name)
    
    cpu_data_file = open(cpu_data_file_name, 'r')
    # Fail to copy or test
    if cpu_data_file.read().count("\n") <= int(target_time)*0.8 :
        os.system("rm " + cpu_data_file_name)
        cpu_data_file.close()
        return "retry"
    
    # Success
    print("copy", cpu_data_file_name) 
    for i in range(len(target_workload)):
        data_file_name    = DATA_DIR+"/"+get_workloads_str()+"_"+partitioning+"_"+str(i)+".data"
        latency_file_name = DATA_DIR+"/"+get_workloads_str()+"_"+partitioning+"_"+str(i)+".latency"
        os.system("touch " + data_file_name)
        os.system("touch " + latency_file_name)
        os.system('ssh -p 8080 ' + REMOTE_ID_IP + ' "sudo cat /pblk-cast_perf/mydev'+str(i)+'.data" > ' + data_file_name)
        os.system('ssh -p 8080 ' + REMOTE_ID_IP + ' "sudo cat /sys/block/mydev'+str(i)+'/pblk/latency" > ' + latency_file_name)
        print("copy", data_file_name, latency_file_name)
        time.sleep(0.1)
        
    return "complete"

#### MAIN ####
def exploing(psl):
    
    for ps in psl:
        ssh_exec_to_host("python3 "+PSLMA_DIR+"/exploring.py" + " -size "+size+ " -time "+time+ " -step "+step + " -case " + ps)
        time.sleep(1)

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