
from utils import * 

# 모든 조합을 찾는 함수
def get_full_partition_set_list(n, min, step, remain):
    def get_next(n, min, step, remain, part):
        if n <= 1 :
            return [part + [remain]]
        else :
            parts = []
            for i in range( min, (remain-min)+1, step):
                parts.extend(get_next(n-1, min, step, remain - i, part + [i]))
            return parts
        
    return get_next(n, min, step, remain, [])

def get_minimum_partition_set_list(N, min, max, step, all):
    
    def make_part_dict(sols):
        return count_each_part(N, sols, min, max, step)
    
    def add(sols):
        dict = make_part_dict(sols)
        if is_valid_result(dict) :
            return sols
        
        zero_list = [[] for _ in range(N)]
        
        for size in dict.keys():
            for part in range(N):
                if dict[size][part] == 0:
                    zero_list[part].append(size)
        
        max_cover = 0
        max_part_set = []
        for part_set in all:
            cover = 0
            for part in range(N):
                if part_set[part] in zero_list[part]:
                    cover += 1
                    
            if max_cover < cover :
                max_cover = cover
                max_part_set = part_set
            elif max_cover > 0 and max_cover == cover:
                sum1 = 0
                sum2 = 0
                for part in range(N):
                    sum1 += dict[part_set[part]][part]
                    sum2 += dict[max_part_set[part]][part]
                
                if sum1 <= sum2 :
                    max_part_set = part_set
                    
        return add(sols + [max_part_set])
    
    return add([all[0]])