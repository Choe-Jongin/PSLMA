
class Chunk(object):
    
    def __init__(self):
        self.set_chunk(0,0,0,0,0,0,0,0)
        self.valid = True
    
    def parse_line_to_chunk(self, line):
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
        self.set_chunk(float(values[0]),
                    int(values[1]),
                    int(values[2]),
                    int(values[3]),
                    int(values[4]),
                    int(values[5]),
                    int(values[7]),
                    int(values[8]))
    
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
            
    def isZeroThrough(self):
        return self.throughput == 0
            
    def add_other(self, other):
            self.throughput += other.throughput
            self.read       += other.read
            self.write      += other.write
            self.gc         += other.gc
            self.r_cached   += other.r_cached
            self.r_device   += other.r_device
            self.w_user     += other.w_user
            self.w_gc       += other.w_gc
            self.w_sum      += other.w_sum
            
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
        print(  "[t:",  round(self.time),   "]",
                "[r:",  self.read,          "]",
                "[w:",  self.write,         "]",
                "[rd:", self.r_device,      "]",
                "[rc:", self.r_cached,      "]",
                "[wu:", self.w_user,        "]",
                "[wg:", self.w_gc,          "]",
                "[waf:",round(self.waf, 2), "]",
                "[hit:",round(self.hit, 2), "]",
                sep="", end="\n")
