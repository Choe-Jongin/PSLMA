import math
import os
import sys
from psl import * 

def part_list(N, step = 1, full = False, ch = 16):
    avg=ch/N
    pivot=int(math.ceil(avg))
    min=int(math.ceil(pivot/2))
    if min % step != 0 :
        min = min + step - min%step
    max=int(ch-min*(N-1))
    
    print("[N"+str(N)+"]", " ch:" + str(ch) + "(" + str(ch*4) + "GB)", ", min:", min,", max:",max, ", step:", step , sep="")
    
    if max < min :
        print("impossible")
        return
    
    #find all partition set
    all_solutions   = get_full_partition_set_list(N, min, max, step, ch)
    validity_dict   = count_each_part(N, all_solutions, min, max, step)
    psl = all_solutions
    
    if full == False:
        #find minimum partition set
        minimum_sols    = get_minimum_partition_set_list(N, min, max, step, all_solutions)
        validity_dict   = count_each_part(N, minimum_sols, min, max, step)
        psl = minimum_sols

    ret = []
    for party in psl:
        mount_str = ""
        for p in party :
            mount_str += str(p) + " "
        mount_str = mount_str[:-1]
        # print("[",mount_str,"]")
        ret.append(mount_str)
    print("Case :", len(ret))
    
    if len(ret) != len(set(ret)):
        print("duplicated!!")
        
    return ret

#entry point(first call)
if __name__ == '__main__':
    
    # test run(no arguments)      
    if len(sys.argv) <= 1 :
        
        part_list(N=2, step=1, full=True, ch = 32)
        part_list(N=3, step=1, full=True, ch = 32)
        part_list(N=4, step=1, full=True, ch = 32)
        part_list(N=5, step=1, full=True, ch = 32)
        # print("-------------------------------------------")
        # part_list(N=2, step=1, full=True, ch = 16)
        # part_list(N=3, step=1, full=True, ch = 16)
        # part_list(N=4, step=1, full=True, ch = 16)
        # part_list(N=5, step=1, full=True, ch = 16)
        # part_list(N=6, step=1, full=True, ch = 32)
        # part_list(N=8, step=1, full=True, ch = 32)
        # part_list(N=10, step=1, full=True, ch = 64)
        # part_list(N=12, step=1, full=True, ch = 64)
            
        # print("-------------------------------------------")
        # part_list(N=2, step=2, full=True, ch = 16)
        # part_list(N=3, step=2, full=True, ch = 16)
        # part_list(N=4, step=2, full=True, ch = 16)
        # part_list(N=5, step=2, full=True, ch = 16)
        # part_list(N=6, step=2, full=True, ch = 32)
        # part_list(N=8, step=2, full=True, ch = 32)
        # part_list(N=10, step=2, full=True, ch = 64)
        # part_list(N=12, step=2, full=True, ch = 64)
        
        # print("-------------------------------------------")
        # print("Greedy")
        # part_list(N=2, step=1, full=False, ch = 16)
        # part_list(N=3, step=1, full=False, ch = 16)
        # part_list(N=4, step=1, full=False, ch = 16)
        # part_list(N=5, step=1, full=False, ch = 16)
        # part_list(N=6, step=1, full=False, ch = 32)
        # part_list(N=8, step=1, full=False, ch = 32)
        # part_list(N=10, step=1, full=False, ch = 64)
        # part_list(N=12, step=1, full=False, ch = 64)
        
        # print("-------------------------------------------")
        # print("Greedy")
        # part_list(N=2, step=2, full=False, ch = 16)
        # part_list(N=3, step=2, full=False, ch = 16)
        # part_list(N=4, step=2, full=False, ch = 16)
        # part_list(N=5, step=2, full=False, ch = 16)
        # part_list(N=6, step=2, full=False, ch = 32)
        # part_list(N=8, step=2, full=False, ch = 32)
        # part_list(N=10, step=2, full=False, ch = 64)
        # part_list(N=12, step=2, full=False, ch = 64)
            
    elif len(sys.argv) <= 2 :
        part_list(N=int(sys.argv[1]), step=1)
    elif len(sys.argv) <= 3 :
        part_list(N=int(sys.argv[1]), step=int(sys.argv[2]))
    else:
        part_list(N=int(sys.argv[1]), step=int(sys.argv[2]), full=sys.argv[3]=="full")