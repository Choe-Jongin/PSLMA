import sys
import os
import copy
import part_list as pl

class Chunk(object):
    
    def __init__(self):
        self.set_chunk(0,0,0,0,0,0,0,0)
        self.valid = True
        
    def set_chunk(self, time, read, write, gc, r_cached, r_device, w_sum, w_user):
        #base
        self.throughput = read + write
        self.time = time
        self.read = read
        self.write = write
        self.gc = gc
        
        #detail
        self.r_cached = r_cached
        self.r_device = r_device
        self.w_user = w_user
        self.w_gc = w_sum - w_user
        
        self.w_sum = w_sum
        
        if r_device + r_cached != read :
            self.valid = False
        if write != w_user :
            self.valid = False
            
        self.calculate_detail()

    def calculate_detail(self):
        if self.w_user > 0 :
            self.waf = (self.w_user + self.w_gc) / self.w_user
        else :
            self.waf = 0
            
        if self.read > 0 :
            self.hit = self.r_cached / self.read
        else :
            self.hit = 0
            
    def add_other(self, other):
            self.throughput += other.throughput
            self.read       += other.read
            self.write      += other.write
            self.gc         += other.gc
            self.r_cached   += other.r_cached
            self.r_device   += other.r_device
            self.w_user     += other.w_user
            self.w_gc       += other.w_gc
            self.w_sum       += other.w_sum
            
            self.calculate_detail()
    
    def divide(self, num):
            self.throughput //= num
            self.read       //= num
            self.write      //= num
            self.gc         //= num
            self.r_cached   //= num
            self.r_device   //= num
            self.w_user     //= num
            self.w_gc       //= num
            self.w_sum       //= num
            
    def print_chunk(self):
        if self.valid == False :
            print('[invalid]', end = '')
        print(  "[t:",  round(self.time), 
                "][r:",  self.read, 
                "][w:",  self.write,
                "][rd:", self.r_device, 
                "][rc:", self.r_cached,
                "][wu:", self.w_user, 
                "][wg:", self.w_gc,
                "][waf:", round(self.waf, 2),
                "][hit:", round(self.hit, 2),
                sep="", end="]\n")

class DataFile(object):
    
    def __init__(self, path = ""):
        self.chunks = []            # all data each seconds
        self.avg = Chunk()          # average of chunks
        self.tot = Chunk()          # total value of chunks
        
        #peak values
        self.peak_throughput        = 0
        self.peak_throughput_read   = 0
        self.peak_throughput_time   = 0
        self.peak_throughput_write  = 0

        self.read_data_file(path)
        
        #period        
        self.s_time = 0
        self.e_time = 0
        self.set_period(0, len(self.chunks))
        
        self.calculate_total()
    
    def set_period(self, s = -1, e = -1):
        if s >= 0:
            self.s_time = s
        if e >= 0 :
            self.e_time = e
            
        if self.e_time > len(self.chunks) :
            self.e_time = len(self.chunks)
            
        self.calculate_total()
            
    def read_data_file(self, path):
        if path == "" :
            return
        datafile = open(path, 'r')
        for line in datafile.readlines() :
            new_chunk = Chunk()
            line = line.replace('(', ' ')
            line = line.replace(')', ' ')
            line = line.replace('[', ' ')
            line = line.replace(']', ' ')
            line = line.replace(':', ' ')
            line = line.replace('/', ' ')
            line = line.replace('s', ' ')
            line = line.replace('r', ' ')
            line = line.replace('w', ' ')
            line = line.replace('\t', ' ')
            line = line.replace('Detail', ' ')
            line = line.strip()
            while '  ' in line :
                line = line.replace('  ', ' ')
            
            values = line.split(' ')
            new_chunk.set_chunk(float(values[0]),
                                int(values[1]),
                                int(values[2]),
                                int(values[3]),
                                int(values[4]),
                                int(values[5]),
                                int(values[7]),
                                int(values[8]))
            self.add_chunk(new_chunk)
    
    def add_chunk(self, chunk):
        self.chunks.append(chunk)
    
    #TODO : sync
    def merge(self, other):
        if (self.s_time < other.s_time):
            self.s_time = other.s_time 
        if (self.e_time > other.e_time):
            self.e_time = other.e_time 
            
        for i in range(self.s_time, self.e_time):
            self.chunks[i].add_other(other.chunks[i])
            
    def divide(self, num):
        for i in range(self.s_time, self.e_time):
            self.chunks[i].divide(num)
            
    def calculate_total(self):
        start   = self.s_time
        end     = self.e_time
        num = len(self.chunks[start:end])
        
        for chunk in self.chunks[start:end]:
            
            #check peak value
            if self.peak_throughput < chunk.throughput :
                self.peak_throughput = chunk.throughput 
                self.peak_throughput_time   = chunk.time
                self.peak_throughput_read   = chunk.read 
                self.peak_throughput_write  = chunk.write
            
            #sum each chuck
            self.avg.add_other(chunk)
            self.tot.add_other(chunk)
            
        #calculate the average.
        self.avg.divide(num)
        self.avg.calculate_detail()
            
class Workload(object):
    
    def __init__(self, name):
        self.name = name
        self.data = {}
        self.merged_data = {}
        self.max_throughput = 0
        
    def add_data(self, path, size):
        if not size in self.data :
            self.data[size] = []
            self.merged_data[size] = object()
        
        new_datafile = DataFile(path)
        self.data[size].append(new_datafile)
        return new_datafile
    
    #Replace with mean if there are multiple data in a size.
    def reduce(self):
        for size, datum in self.data.items():
            self.merged_data[size] = copy.deepcopy(datum[0])
            if len(datum) == 1 :
                continue
            #sum then divide
            for merge in datum[1:]:
                self.merged_data[size].merge(merge)
            self.merged_data[size].divide(len(datum))
            self.merged_data[size].calculate_total()
    
    def get_data(self, size):
        if size in self.merged_data.keys():
            return self.merged_data[size]
        return self.data[size][0]

    def get_original_data(self, size):
        return self.data[size]
    
    def get_max(self):
        self.max_throughput = -1
        for size, datum in self.data.items():
            for node in datum:
                if self.max_throughput < node.avg.throughput:
                    self.max_throughput = node.avg.throughput
        return self.max_throughput
class Analyzer(object):
    
    ssd = 64
    ch = 16
    ch_size = ssd//ch
    step = ch_size
    
    def __init__(self, dir, N, psl, names = [], s_time = -1, end_time = -1):
        self.N = N
        self.psl = psl
        self.full = pl.part_list(N, True)
        self.workloads = []
        self.all_datafiles = {}
        
        #if names is not set, set default name
        for i in range(len(names),N):
            names.append('NoName'+chr(65+i))
            
        #set workload name
        for i in range(N):
            self.workloads.append(Workload(names[i]))
        
        #read file by workload
        for file in os.listdir(dir):
            if file[0] == '.':
                continue
            filename = dir+"/"+file
            print("read", filename)
            
            parse = file
            parse = parse.replace('wl_', '')
            parse = parse.replace('.data', '')
            parse = parse.replace('.txt', '')
            parsed = parse.split('_')
            index = int(parsed[N])
            new_datafile = self.workloads[index].add_data(filename, int(parsed[index]))
            new_datafile.set_period(s_time,end_time)
            self.all_datafiles[parse.replace('_', ' ')] = new_datafile
        
        #sort by size. calculate total
        for workload in self.workloads:
            new_dict = {} 
            for k in sorted(workload.data):
                new_dict[k] = workload.data[k]
            workload.data = new_dict
            workload.reduce()
            print(workload.data.keys())
            
        #### show result ###
        print("-"*80)
        
        print("[ Average Bandwidth ]")
        print("  workload", end = "")
        for size in self.workloads[0].data.keys():
            print("%10d"%(size), end = "")
        print()
        for workload in self.workloads:
            print("%10s"%(workload.name), end = "")
            for size in workload.data.keys():
                data = round(workload.get_data(size).avg.throughput)
                print('%10s' % format(data, ','), end = "")
            print()     
        print()
        
        print("[ Average Flash Write ]")
        print("  workload", end = "")
        for size in self.workloads[0].data.keys():
            print("%10d"%(size), end = "")
        print()
        for workload in self.workloads:
            print("%10s"%(workload.name), end = "")
            for size in workload.data.keys():
                data = round(workload.get_data(size).avg.w_sum*86400//1000//1000/1000, 1)
                print('%6s TBW' % format(data, ','), end = "")
            print()     
        print()
        
        print(" PARTITION ", end ='')
        print("    BW Total", end ='')
        [print("%10s"%(name), end = "") for name in names]
        print(" |  Weighted", end ='')
        [print("%10s"%(name), end = "") for name in names]
        print(" | Write/day", end ='')
        [print("%10s"%(name), end = "") for name in names]
        print(" |      read", end ='')
        [print("%10s"%(name), end = "") for name in names]
        print(" |     write", end ='')
        [print("%10s"%(name), end = "") for name in names]
        print()
        
        for ps_str in self.full:
            target_value1 = 0
            target_value2 = 0
            target_value3 = 0
            target_value4 = 0
            target_value5 = 0

            tasks={}
            for i in range(N):
                parse = ps_str+" "+str(i)
                if parse in self.all_datafiles.keys():
                    tasks[i] = self.all_datafiles[parse]
            for i in range(len(tasks.items())):
                target_value1 += tasks[i].avg.throughput
                target_value2 += tasks[i].avg.throughput/self.workloads[i].get_max()
                target_value3 += tasks[i].avg.w_sum
                target_value4 += tasks[i].avg.read
                target_value5 += tasks[i].avg.write
                
            print("[", end = "")
            [print("%3d"%(int(p)), end = "") for p in ps_str.strip().split(' ')]
            print(" ] ", end = '')
            
            print("%10s" % format(int(target_value1), ',') if target_value1 != 0 else "%10s"%'-', end = '')
            for i in range(N):
                print("%10s" % (format(tasks[i].avg.throughput, ',') if i in tasks.keys() else '-'), end = '')
        
            print(" |", end = '')
            print("%10.2f" % (target_value2) if target_value2 != 0 else "%10s"%'-' , end = '')
            for i in range(N):
                data = 0
                if i in tasks.keys():
                    if self.workloads[i].max_throughput > 0 :
                        data = round(tasks[i].avg.throughput/self.workloads[i].get_max(), 2)
                print("%10s" % (format(data, ',') if i in tasks.keys() else '-'), end = '')
                
            print(" |", end = '')
            target_value3 = round(target_value3*86400//1000//1000/1000,1)
            print("%6s TBW" % format(target_value3, ',') if target_value3 != 0 else "%10s"%'-', end = '')
            for i in range(N):
                print("%6s TBW" % (format(round(tasks[i].avg.w_sum*86400//1000//1000/1000, 1), ',')) if i in tasks.keys() else "%10s"%'-', end = '')
            
            print(" |", end = '')    
            print("%10s" % format(int(target_value4), ',') if target_value1 != 0 else "%10s"%'-', end = '')
            for i in range(N):
                print("%10s" % (format(tasks[i].avg.read, ',') if i in tasks.keys() else '-'), end = '')
                
            print(" |", end = '')
            print("%10s" % format(int(target_value5), ',') if target_value1 != 0 else "%10s"%'-', end = '')
            for i in range(N):
                print("%10s" % (format(tasks[i].avg.write, ',') if i in tasks.keys() else '-'), end = '')
            
            print()
            
if __name__ == '__main__':
    
    workload_names = ['P1', 'P2', 'P3']
    dir = "data"
    N = 3
    psl = pl.part_list(N)
    s_time = -1
    e_time = -1
    
    if len(sys.argv) == 1 :
        dir = "data"
    elif len(sys.argv) == 2 :
        dir = sys.argv[1]
    elif len(sys.argv) >= 3 :
        for i in range(1, len(sys.argv)):
            if sys.argv[i] == "-p" :
                dir = sys.argv[i+1]
            if sys.argv[i] == "-n" :                
                workload_names = []
                for wl in sys.argv[i+1:]:
                    if wl[0] == '-':
                        break
                    workload_names.append(wl)
            if sys.argv[i] == "-s" :      
                s_time = int(sys.argv[i+1])
            if sys.argv[i] == "-e" :      
                e_time = int(sys.argv[i+1])
                
                    
    #make Analyzer
    analyzer = Analyzer(dir, N, psl, workload_names, s_time, e_time)