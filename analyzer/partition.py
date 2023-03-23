class cpu_chunk():
    def __init__(self, time=0, user=0, nice=0, syst=0, idle=0, wait=0, irq=0, soft=0, steal=0, guest=0):
        self.set_chunk(time, user, nice, syst, idle, wait, irq, soft, steal, guest)
        
    def set_chunk(self, time, user, nice, syst, idle, wait, irq, soft, steal, guest):
        #base
        self.time = time
        
        #detail
        self.user = user
        self.nice = nice
        self.syst = syst
        self.idle = idle
        self.wait = wait
        self.irq = irq
        self.soft = soft
        self.steal = steal
        self.guest = guest
        
        self.util = 0
        self.total = user + nice + syst + idle + wait + irq + soft + steal + guest
        self.used = self.total - idle
        if self.total > 0 :
            self.util = round(self.used/self.total, 2)
            
class data_chunk():
    def __init__(self, time=0, read=0, write=0, gc=0, r_cached=0, w_gc=0, waf=0):
        self.set_chunk(time, read, write, gc, r_cached, w_gc, waf)
        
    def set_chunk(self, time, read, write, gc, r_cached, w_gc, waf):
        #base
        self.time = time
        self.throughput = read + write
        self.read = read
        self.write = write
        self.gc = gc
        
        #detail
        self.r_cached = r_cached
        self.w_gc = w_gc
        self.waf = waf
        
class partition():
    def __init__(self, n):
        self.n = n
        
        self.chunks = []            # all data each seconds
        self.avg = partition()      # average of chunks
        self.peak = partition()     # peak of chunks
        
    def add_chunk(self, chunk):
        if self.peak.throughput < chunk.throughput :
            self.peak = chunk
            
        self.chunks.append(chunk)
        