
from utils import * 

# 모든 조합을 찾는 함수
def get_full_partition_set_list(n, min, max, step, remain):
    
    def get_next(n, min, max, step, remain, part):
        if n <= 1 :
            if remain > max :
                return None
            if remain < min :
                return None
            if (remain-min)%step != 0:
                return None
            return [part + [remain]]
        else :
            parts = []
            stop = max if max < remain-min else remain-min
            for i in range( min, stop+1, step):
                next = get_next(n-1, min, max, step, remain - i, part + [i])
                if next != None:
                    parts.extend(next)
            return parts
        
    return get_next(n, min, max, step, remain, [])

#greedy
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