import sys
import os
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
            
        #calculate the average.
        self.avg.divide(num)
        self.avg.calculate_detail()
            
class Workload(object):
    
    def __init__(self, name):
        self.name = name
        self.data = {}
        
    def add_data(self, path, size):
        if not size in self.data :
            self.data[size] = []
        
        self.data[size].append(DataFile(path))
    
    #Replace with mean if there are multiple data in a size.
    def reduce(self):
        for size, datum in self.data.items():
            if len(datum) == 1 :
                continue
            for merged in datum[1:]:
                datum[0].merge(merged)
            datum[0].divide(len(datum))
            datum[0].calculate_total()
    
    def get_data(self, size):
        return self.data[size][0]

class Analyzer(object):
    
    ssd = 64
    ch = 16
    ch_size = ssd//ch
    step = ch_size
    
    def __init__(self, dir, N, psl):
        self.N = N
        self.psl = psl
        self.full = pl.part_list(N, True)
        self.workloads = []
        for i in range(N):
            self.workloads.append(Workload(chr(65+i)))
        
        print(self.full)
        
        #read file by workload
        for file in os.listdir(dir):
            filename = dir+"/"+file
            print("read", filename)
            
            parse = file
            parse = parse.replace('wl_', '')
            parse = parse.replace('.data', '')
            parse = parse.replace('.txt', '')
            parsed = parse.split('_')
            index = int(parsed[N])
            
            self.workloads[index].add_data(filename, int(parsed[index]))
        
        #sort by size
        for workload in self.workloads:
            new_dict = {} 
            for k in sorted(workload.data):
                new_dict[k] = workload.data[k]
            workload.data = new_dict
            workload.reduce()
            print(workload.data.keys())
        
        print("Result")
        for ps_str in self.full:
            target_value = 0
            ps = ps_str.strip()
            ps = ps.split(' ')
            
            for i in range(N):
                data = self.workloads[i].get_data(int(ps[i]))
                target_value += data.avg.throughput
            for p in ps:
                print("%3d"%(int(p)*Analyzer.ch_size), end = "")
            print(" : %10d"%(int(target_value)), 
                  "%7d"%(self.workloads[0].get_data(int(ps[0])).avg.throughput),
                  "%7d"%(self.workloads[1].get_data(int(ps[1])).avg.throughput),
                  "%7d"%(self.workloads[2].get_data(int(ps[2])).avg.throughput)
                  )
            
        print("bw  \ size", end = "")
        for size in self.workloads[0].data.keys():
            print("%8d"%(size*Analyzer.ch_size), end = "")
        print()
        for workload in self.workloads:
            print("workload", workload.name, end = "")
            for size in workload.data.keys():
                data = workload.get_data(size).avg.throughput
                print('%8s' % format(data, ','), end = "")
            print()
        print()
        print("waf \ size", end = "")
        for size in self.workloads[0].data.keys():
            print("%8d"%(size*Analyzer.ch_size), end = "")
        print()
        for workload in self.workloads:
            print("workload", workload.name, end = "")
            for size in workload.data.keys():
                data = round(workload.get_data(size).avg.waf*100)
                print('%8s' % format(data, ','), end = "")
            print()
        
            
if __name__ == '__main__':
    analyzer = Analyzer("data", 3, pl.part_list(3))