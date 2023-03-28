import os
import sys
from psl import * 

#SSD Settings
ssd = 64
ch = 16
ch_size = ssd//ch

def part_list(N, step = 1, full = False):
    avg=ch/N
    pivot=((avg+(step-0.001))//step*step)
    min=int((pivot/2+(step-0.001))//step*step)
    max=int(ch-min*(N-1))
    
    #find all partition set
    all_solutions   = get_full_partition_set_list(N, min, step, ch)
    validity_dict   = count_each_part(N, all_solutions, min, max, step)
    
    #find minimum partition set
    minimum_sols    = get_minimum_partition_set_list(N, min, max, step, all_solutions)
    validity_dict   = count_each_part(N, minimum_sols, min, max, step)
    
    psl = all_solutions
    if full == False :
        psl = minimum_sols

    ret = []
    for party in psl:
        mount_str = ""
        for p in party :
            mount_str += str(p) + " "
        mount_str = mount_str[:-1]
        print("[",mount_str,"]")
        ret.append(mount_str)
    print("case :", len(ret))
    return ret

#entry point(first call)
if __name__ == '__main__':
    if len(sys.argv) <= 1 :
        # teest run(no arguments)
        n = 5
        part_list(N=n, step=1, full=True)
        print("----------------")
        part_list(N=n, step=2, full=True)
        print("----------------")
        part_list(N=n, step=1, full=False)
        print("----------------")
        part_list(N=n, step=2, full=False)
    elif len(sys.argv) <= 2 :
        part_list(N=int(sys.argv[1]), step=1)
    elif len(sys.argv) <= 3 :
        part_list(N=int(sys.argv[1]), step=int(sys.argv[2]))
    else:
        part_list(N=int(sys.argv[1]), step=int(sys.argv[2]), full=sys.argv[3]=="full")