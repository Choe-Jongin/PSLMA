import sys
import os
import part_list as pl
from cast_workload import Workload
from cast_data_file import DataFile

class Analyzer(object):
    
    ssd = 64
    ch = 16
    ch_size = ssd//ch
    step = ch_size
    
    def __init__(self, dir, names = [], s_time = -1, e_time = -1, step = 1):
        self.N = len(names)
        self.names = names
        self.full = pl.part_list(self.N, step, True)
        self.workloads = []
        self.all_datafiles = {}
        self.total_read_file = 0
        self.total_read_failed = 0
        self.read_fail_scenarios = []
        self.s_time, self.e_time = s_time, e_time
            
        #set workload name
        for i in range(self.N):
            self.workloads.append(Workload(names[i]))
        
        #read file by workload
        self.all_file_read(dir)
                
        #sort by size
        for workload in self.workloads:
            workload.sort()
            
        #calculate total
        for workload in self.workloads:
            workload.reduce()
            print(workload.data.keys())
        
        self.print_analysis()
    
    def all_file_read(self, dir):
        #read file by workload
        files = os.listdir(dir)
        files.sort()
        for file in files:
            if file[0] == '.':                  # Exclude hidden files 
                continue
            if file[-5:] != '.data':            # Exclude no data files 
                continue
            filename = dir+"/"+file
            
            self.total_read_file += 1
            print("read", filename, end = "")
    
            parse = file
            parse = parse[(parse.find('_')+1):] # eliminate scenario name
            parse = parse.replace('.data', '')  # eliminate extension
            parse = parse.replace('.txt', '')   # eliminate extension
            parsed = parse.split('_')           # split size by partitions
            
            index = int(parsed[self.N])              # get device(part) name
            size  = int(parsed[index])          # get partition size  ex) index = 2 -> 3_3_[10]
            even  = self.is_even_partition(self.N, parsed)
                
            new_datafile = DataFile(filename)
            result = new_datafile.set_period(s_time, e_time)
            if result == "ok":
                self.workloads[index].add_data(size, new_datafile, even)
                self.all_datafiles[parse.replace('_', ' ')] = new_datafile
            else :
                self.total_read_failed += 1
                self.read_fail_scenarios.append(parse[:-2].replace('_', ' '))   # eliminate device(part) name
            print(" \tresult :", result)

        self.read_fail_scenarios = list(set(self.read_fail_scenarios) ) # eliminate duplicates
        self.read_fail_scenarios.sort()                                 # sort by partitions
        
        # Reporting 
        print("total read :", self.total_read_file)
        print("total read failed :", self.total_read_failed)
        print("total fail scenario :", len(self.read_fail_scenarios))
        if len(self.read_fail_scenarios) > 0 :
            print("----Fail Scenario List-----")
            for scenario in self.read_fail_scenarios:
                print(scenario)
            print("----------- END -----------")
    
    
    def print_col(self, caption, width):
        str_len = len(caption)
        print(" "+caption, end ='')
        [print(" "*(width-len(name)),name, sep="", end = "") for name in self.names]
        print("  ", end = "")
        
    # show result
    def print_analysis(self):
        
        print("-"*80)
        self.print_by_workload("Average Throughput/s", lambda x : round(x.avg.throughput))
        self.print_by_workload("Flash Write per day", lambda x : round(x.avg.w_sum*86400/1000**3))
        self.print_by_workload("Average WAF"        , lambda x : round(x.avg.waf*100))
        self.print_by_workload("Average write/s"    , lambda x : round(x.avg.write))
        self.print_by_workload("Average read/s"     , lambda x : round(x.avg.read))
        
        ########################################################################
        print(" "*(self.N*3+5), end ='')
        self.print_col("MByte/s", 8)
        self.print_col("Weighted", 8)
        self.print_col("TBW/day", 6)
        self.print_col("read", 7)
        self.print_col("write", 7)
        # print("MByte/s", end ='')
        # [print("%8s"%(name), end = "") for name in names]
        # print(" | Weighted", end ='')
        # [print("%8s"%(name), end = "") for name in names]
        # print(" | TBW/day", end ='')
        # [print("%6s"%(name), end = "") for name in names]
        # print(" |   read", end ='')
        # [print("%7s"%(name), end = "") for name in names]
        # print(" |  write", end ='')
        # [print("%7s"%(name), end = "") for name in names]
        
        print()
        
        for ps_str in self.full:
            target_value1 = 0
            target_value2 = 0
            target_value3 = 0
            target_value4 = 0
            target_value5 = 0

            tasks={}
            for dev in range(self.N):
                parse = ps_str+" "+str(dev)
                if parse in self.all_datafiles.keys():
                    tasks[dev] = self.all_datafiles[parse]
            for i in tasks.keys():
                target_value1 += tasks[i].avg.throughput//1000
                target_value2 += (tasks[i].avg.throughput/self.workloads[i].even_data.avg.throughput)
                target_value3 += tasks[i].avg.w_sum
                target_value4 += tasks[i].avg.read
                target_value5 += tasks[i].avg.write
            
            if len(tasks.keys()) < self.N:
                continue
                
            print("[", end = "")
            [print("%3d"%(int(p)), end = "") for p in ps_str.strip().split(' ')]
            print(" ] ", end = '')
            
            #Throughput
            print("%9s" % format(int(target_value1), ',') if target_value1 != 0 else "%9s"%'-', end = '')
            for i in range(self.N):
                print("%8s" % (format(tasks[i].avg.throughput//1000, ',') if i in tasks.keys() else '-'), end = '')

            #Weighted
            print(" |", end = '')
            print("%9.2f" % (target_value2) if target_value2 != 0 else "%9s"%'-' , end = '')
            for i in range(self.N):
                data = 0
                if i in tasks.keys():
                    if self.workloads[i].even_data.avg.throughput > 0 :
                        data = round((tasks[i].avg.throughput/self.workloads[i].even_data.avg.throughput), 2)
                print("%8s" % (format(data, ',') if i in tasks.keys() else '-'), end = '')
            
            #TBW
            print(" |", end = '')
            target_value3 = round(target_value3*86400/1000/1000/1000,1)
            print("%8s" % format(target_value3, ',') if target_value3 != 0 else "%8s"%'-', end = '')
            for i in range(self.N):
                print("%6s" % (format(round(tasks[i].avg.w_sum*86400/1000/1000/1000,1), ',')) if i in tasks.keys() else "%6s"%'-', end = '')
            
            #Read
            print(" |", end = '')    
            print("%7s" % format(int(target_value4//1000), ',') if target_value1 != 0 else "%7s"%'-', end = '')
            for i in range(self.N):
                print("%7s" % (format(tasks[i].avg.read//1000, ',') if i in tasks.keys() else '-'), end = '')
                
            #Write
            print(" |", end = '')
            print("%7s" % format(int(target_value5//1000), ',') if target_value1 != 0 else "%7s"%'-', end = '')
            for i in range(self.N):
                print("%7s" % (format(tasks[i].avg.write//1000, ',') if i in tasks.keys() else '-'), end = '')
            
            print()

    def print_by_workload(self, title, field_func):
        # get all sizes
        sizes = []
        for wl in self.workloads:
            sizes = sizes + list(wl.data.keys())
        sizes = list(set(sizes))
        sizes.sort()
        
        print("[" , title, "]")
        print("  workload", end = "")
        for size in sizes:
            print("%10d"%(size), end = "")
        print()
        
        for workload in self.workloads:
            print("%10s"%(workload.name), end = "")
            for size in sizes:
                data_file = workload.get_data(size)
                if data_file == "-":
                    print('%10s' % (data_file), end = "")
                else :
                    data = field_func(data_file)
                    print('%10s' % format(data, ','), end = "")
            print()     
        print()
        
    def print_by_case(self, title, field_func):
        pass

    #### utils ####            
    def is_even_partition(self, N, partitions):
        if N == 2 and partitions[:2] == ["8", "8"]:
            return True
        elif N == 3 and partitions[:3] == ["5", "5", "6"]:
            return True
        elif N == 4 and partitions[:4] == ["4", "4", "4", "4"]:
            return True
        elif N == 5 and partitions[:5] == ["3", "3", "3", "3", "4"]:
            return True
        elif N == 6 and partitions[:6] == ["2", "2", "3", "3", "3", "3"]:
            return True
        return False
        

def get_workload_name_from_dir(dir):
    dir = os.path.basename(dir)
    if len(dir) < 6:
        return []
    ret = []
    #version 1 : DATA_ABCD
    if not dir[6].isdigit():
        for wl in dir[5:]:
            ret.append(wl)
    else :
        for i in range(0, len(dir[5:]), 2):
            ret.append(dir[5+i] + dir[5+i+1])
    return ret

if __name__ == '__main__':
    
    workload_names = []
    dir = "data"
    s_time = -1
    e_time = -1
    step = 1
    
    if len(sys.argv) == 1 :
        pass
    elif len(sys.argv) == 2 :
        dir = sys.argv[1]
        names = get_workload_name_from_dir(dir)         #### duplicate
        if names != []:
            workload_names = names
    elif len(sys.argv) >= 3 :
        for i in range(1, len(sys.argv)):
            if sys.argv[i] == "-p" :
                dir = sys.argv[i+1]                     #### duplicate
                names = get_workload_name_from_dir(dir)
                if names != []:
                    workload_names = names
                
            if sys.argv[i] == "-N" :
                N = int(sys.argv[i+1])
                for i in range(1, N+1):
                    workload_names.append("P"+ascii(i))
                    
            if sys.argv[i] == "-n" or sys.argv[i] == "-name" :                
                workload_names = []
                for wl in sys.argv[i+1:]:
                    if wl[0] == '-':
                        break
                    workload_names.append(wl)
                    
            if sys.argv[i] == "-s" :      
                s_time = int(sys.argv[i+1])
            if sys.argv[i] == "-e" :      
                e_time = int(sys.argv[i+1])
            if sys.argv[i] == "-step" :      
                step = int(sys.argv[i+1])
                
    #make Analyzer
    analyzer = Analyzer(dir, workload_names, s_time, e_time, step)
