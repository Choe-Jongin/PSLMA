from cast_chunk import Chunk
from cast_latency_file import Latency_file

class DataFile(object):
    
    def __init__(self, path = ""):
        
        #all chunk list
        self.chunks = []            # all data each seconds
        
        #special chunks
        self.avg = Chunk()          # average of chunks         : object
        self.tot = Chunk()          # total value of chunks     : object
        self.peak = Chunk()         # peak throughput Chunk     : pointer
        
        #latency
        self.w_latency_buckets = object() # key:size, value:latency_file
                
        #etc
        self.zero_line_count = 0
        self.last_none_zero_line = 0
        
        if path != "" :
            self.read_data_file(path)
        
        #period        
        self.s_time = 0
        self.e_time = 0
        self.set_period(0, len(self.chunks))
        
    def set_period(self, s = -1, e = -1):
        if s >= 0 : self.s_time = s
        if e >= 0 : self.e_time = e
                    
        if self.e_time - self.s_time == 0 :
            return "invalid period"
        
        if self.e_time > len(self.chunks) :
            self.e_time = len(self.chunks)
            return "out of length(need "+str(e)+", but " + str(len(self.chunks)) + ")"

        self.calculate_total()
        return "ok"
            
    def read_data_file(self, path):
        if path == "" :
            return
        
        #file read. line by line
        datafile = open(path, 'r')
        for line in datafile.readlines() :
            new_chunk = Chunk()
            new_chunk.parse_line_to_chunk(line)
            self.add_chunk(new_chunk)
            
            if new_chunk.isZeroThrough() :
                self.zero_line_count += 1
            else :
                self.last_none_zero_line = len(self.chunks)

        #trim zero lines
        self.chunks = self.chunks[:self.last_none_zero_line]
        
        self.r_latency_buckets = Latency_file(path.replace(".data", ".read_latency"))
        self.w_latency_buckets = Latency_file(path.replace(".data", ".write_latency"))
    
    def add_chunk(self, chunk):
        self.chunks.append(chunk)
        
    def set_even_data_file(self, even_file):
        self.even_data_file = even_file
        
    def get_even_data_file(self):
        return self.even_data_file
        
    #TODO : sync
    #sum two data file
    def add(self, other):           
        if (self.s_time < other.s_time):
            self.s_time = other.s_time 
        if (self.e_time > other.e_time):
            self.e_time = other.e_time 
            
        for i in range(self.s_time, self.e_time):
            self.chunks[i].add_other(other.chunks[i])
            
        self.r_latency_buckets.add(other.r_latency_buckets)
        self.w_latency_buckets.add(other.w_latency_buckets)
            
    def divide(self, num):
        for i in range(self.s_time, self.e_time):
            self.chunks[i].divide(num)
        self.r_latency_buckets.divide(num)
        self.w_latency_buckets.divide(num)
            
    def calculate_total(self):
        start   = self.s_time
        end     = self.e_time
        num     = len(self.chunks[start:end])
        
        if len(self.chunks) == 0 or num == 0 :
            return "no chunks"
        
        for chunk in self.chunks[start:end]:
            
            #check peak value
            if self.peak.throughput < chunk.throughput :
                self.peak = chunk 
            
            #sum each chuck
            self.avg.add_other(chunk)
            self.tot.add_other(chunk)
            
        #calculate the average.
        self.avg.divide(num)
        self.avg.calculate_detail()