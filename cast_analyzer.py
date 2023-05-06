import sys
import os
import part_list as pl
from utils import str_w
from cast_workload import Workload
from cast_data_file import DataFile
from cast_latency_file import Latency_file

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
        
        #calculate
        for workload in self.workloads:
            workload.distribute_even()
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
                
            new_data_file       = DataFile(filename)
            
            result = new_data_file.set_period(s_time, e_time)
            if result == "ok":
                self.workloads[index].add_data(size, new_data_file, even)
                self.all_datafiles[parse.replace('_', ' ')] = new_data_file
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
        
    # show result
    def print_analysis(self):
        self.header_widths = {}
        self.row_widths = {}
        self.func_dict = {}
        self.sum_of_values = {}
        
        print("-"*80)
        # avg by each size for workload
        self.print_by_workload("Average Throughput/s", lambda x : round(x.avg.throughput))
        self.print_by_workload("Weighted", lambda x : round(x.avg.throughput/x.even_data_file.avg.throughput,2))
        self.print_by_workload("METRIC3", lambda x : round(x.avg.throughput/x.avg.w_sum,2))
        self.print_by_workload("Average WAF"        , lambda x : round(x.avg.waf*100))
        self.print_by_workload("avg latnecy"     , lambda x : round(x.latency_buckets.get_avg()))
        self.print_by_workload("10% latnecy"     , lambda x : round(x.latency_buckets.get_n_percent(0.1)))
        self.print_by_workload("30% latnecy"     , lambda x : round(x.latency_buckets.get_n_percent(0.3)))
        self.print_by_workload("50% latnecy"     , lambda x : round(x.latency_buckets.get_n_percent(0.5)))
        self.print_by_workload("90% latnecy"     , lambda x : round(x.latency_buckets.get_n_percent(0.9)))
        self.print_by_workload("99% latnecy"     , lambda x : round(x.latency_buckets.get_n_percent(0.99)))
        self.print_by_workload("99.9% latnecy"     , lambda x : round(x.latency_buckets.get_n_percent(0.999)))
        self.print_by_workload("99.99% latnecy"     , lambda x : round(x.latency_buckets.get_n_percent(0.9999)))
        print("[Detail]")
        self.print_by_workload("Average write/s"    , lambda x : round(x.avg.write))
        self.print_by_workload("Average read/s"     , lambda x : round(x.avg.read))
        
        # print header 
        print(" "*(self.N*3+4), end ='')
        self.register_col_header("1.MByte/s",  8, lambda x : x.avg.throughput//1000)
        self.register_col_header("2.Weighted", 8, lambda x : x.avg.throughput/x.even_data_file.avg.throughput)
        # self.register_col_header("TBW/day",  6, lambda x : x.avg.w_sum*86400/1000**3)
        self.register_col_header("3.metric3",  6, lambda x : x.avg.throughput/x.avg.w_sum)
        self.register_col_header("4.avg lat",  7, lambda x : round(x.latency_buckets.get_avg()))
        self.register_col_header("  read",   6, lambda x : x.avg.read//1000)
        self.register_col_header(" write",   6, lambda x : x.avg.write//1000)
        print()
        
        # print valid partition
        self.print_cols(True)       
        # print invalid partition
        print("\033[31m", end="")
        self.print_cols(False)     
        print("\033[0m", end="")

    def print_cols(self, only_valid = True):
        for ps_str in self.full:
            # init
            for header in self.sum_of_values.keys():
                self.sum_of_values[header] = 0

            # get all device(partition)
            tasks={}
            for dev in range(self.N):                           # all dev(partition num)
                datafile = ps_str+" "+str(dev)                  # partition + dev ex) 3_3_10 -> 3_3_10_0 ~ 3_3_10_2
                if datafile in self.all_datafiles.keys():       # 3_3_10_0 in self.all_datafiles ??
                    tasks[dev] = self.all_datafiles[datafile]   # task[0] = 3_3_10_0.data ~ task[2] = 3_3_10_2.data 
                    
            for task in tasks.values():
                for value in self.sum_of_values.keys():
                    self.sum_of_values[value] += self.func_dict[value](task)
            
            if only_valid and len(tasks.keys()) < self.N:
                continue
            if not only_valid and len(tasks.keys()) >= self.N:
                continue
            
            print("[", end = "")
            [print("%3d"%(int(p)), end = "") for p in ps_str.strip().split(' ')]
            print(" ] ", end = '')
            
            self.print_by_case(tasks, "1.MByte/s")
            self.print_by_case(tasks, "2.Weighted", round_point=2)
            self.print_by_case(tasks, "3.metric3", round_point=2)
            self.print_by_case(tasks, "4.avg lat", avg = True)
            self.print_by_case(tasks, "  read")
            self.print_by_case(tasks, " write")
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

    def register_col_header(self, header, width, func):
        self.header_widths[header]  = len(header)
        self.row_widths[header]     = width
        self.func_dict[header]      = func
        self.sum_of_values[header]  = 0
        
        print(header, end ='')
        [print(str_w(name, width), sep="", end = "") for name in self.names]
        print(" | ", end = "")
        
    def print_by_case(self, tasks, value, round_point = 0, avg = False):
        width_total = self.header_widths[value]
        width_each  = self.row_widths[value]
        values, funcs = self.sum_of_values, self.func_dict
        
        #total
        if avg == False:
            data = round(values[value], round_point)
        else :
            data = round(values[value]/self.N, round_point)
        if data != 0 :
            print(str_w(format(data, ','), width_total), end = '')
        else :
            print(str_w("-", width_total), end = '')
        
        #each
        for i in range(self.N):
            if i in tasks.keys():
                data = round(funcs[value](tasks[i]), round_point)
                print(str_w(format(data, ','), width_each), end = '')
            else:
                print(str_w("-", width_each), end = '')
        print(" | ", end = '')
    
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
