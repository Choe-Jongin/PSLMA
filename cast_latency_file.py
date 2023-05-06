
class Latency_file(object):
    
    def __init__(self, path = ""):
        self.array = []
        datafile = open(path, 'r')
        line = datafile.readline().split(' ')
        # print()
        # print(len(line), (line))
        for word in line:
            if  word.isdigit():
                self.array.append(int(word))
        self.array = self.array[:700]
        self.type = 0       # 1024, 512, 256        
        
        
    def get_total(self,):
        total = 0
        for location in self.array:
            total+=location
        return total
                
    def get_avg(self,):
        accumulated = 0
        for i in range(len(self.array)):
            latency = self.get_latency(i)
            accumulated += latency * self.array[i]
        return accumulated/self.get_total()
    
    def get_n_percent(self, per = 0.5):
        
        per_location = int(self.get_total()*per)
        prev_location = 0
        
        for i in range(len(self.array)):
            latency = self.get_latency(i)
            prev_location += self.array[i]
            
            if(prev_location >= per_location) :
                return latency + ((per_location-per_location)/self.array[i])*5
            else :
                continue
            
    def get_latency(self, i):
        if self.type == 0 :
            return 40 + i*5
        
    def add(self, other): 
        for i in range(len(self.array)):
            self.array[i] += other.array[i]
        
    def divide(self, num): 
        for i in range(len(self.array)):
            self.array[i] /= num