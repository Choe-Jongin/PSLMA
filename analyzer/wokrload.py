class workload(object):
    def __init__(self, name, min, max, step = 1):
        self.name = name 
        self.min = min
        self.max = max
        self.step = step
        
        self.partitions = {}
        for i in range(min, max+1, step):
            self.partitions[i] = []
            