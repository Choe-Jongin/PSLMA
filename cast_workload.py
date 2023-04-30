from cast_data_file import DataFile
import copy

class Workload(object):
    
    def __init__(self, name):
        self.name = name
        self.data = {}
        self.merged_data = {}
        self.even_data = object()
        
    def sort(self):
        new_dict = {} 
        for k in sorted(self.data):
            new_dict[k] = self.data[k]
        self.data = new_dict
    
    def make_empty_data_list(self, size):
            self.data[size] = []
            self.merged_data[size] = DataFile()
        
    def add_data(self, size, datafile, is_even=False):
        #for this workload, first size(part) data
        if size not in self.data :
            self.make_empty_data_list(size)
            
        # register the data in data_list by size  (use dictionary)
        self.data[size].append(datafile)
        
        #if even partitioning data
        if is_even:
            self.even_data = datafile
    
    #Replace with mean if there are multiple data in a size.
    def reduce(self):
        for size, datum in self.data.items(): # size, data file list pair
            print("size :", size, "\t|#", len(datum))
            if len(datum) == 0 :
                continue
            self.merged_data[size] = copy.deepcopy(datum[0])
            
            #sum then divide
            for merge in datum[1:]:
                self.merged_data[size].add(merge)
            self.merged_data[size].divide(len(datum))
            self.merged_data[size].calculate_total()
    
    def get_data(self, size):
        if size in self.merged_data.keys():
            return self.merged_data[size]
        if not size in self.data.keys() :
            # return DataFile("")
            return "-"
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