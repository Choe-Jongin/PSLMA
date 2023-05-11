
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
def get_minimum_partition_set_list(N, ch, min, max, step, all):
    
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
    
    # return add([all[0]])
    return add([get_even_partition(N,ch)])

def get_even_partition(N, ch = 16):
    
    if ch == 16 :
        if N == 2 :
            return [8, 8]
        if N == 3 :
            return [5, 6, 5]
        if N == 4:
            return [4, 4, 4, 4]
        if N == 5:
            return [3,3,3,3,4]
        if N ==  6:
            return [2,2,3,3,3,3]
    if ch == 32 :
        if N == 2 :
            return [16, 16]
        if N == 3 :
            return [10, 11, 11]
        if N == 4:
            return [8, 8, 8, 8]
        if N == 5:
            return [6,6,6,7,7]
        if N == 6:
            return [5,5,5,5,6,6]
        if N ==  8:
            return [4,4,4,4,4,4]
        
    if ch == 64 :
        if N == 2 :
            return [32, 32]
        if N == 3 :
            return [21, 21, 22]
        if N == 4:
            return [16, 16, 16, 16]
        if N == 5:
            return [12,13,13,13,13]
        if N == 6:
            return [10,10,11,11,11,11]
        if N ==  8:
            return [8,8,8,8,8,8]
        if N ==  10:
            return [6,6,6,6,6,6,7,7,7,7]
        if N ==  12:
            return [5,5,5,5,5,5,5,5,6,6,6,6]
        