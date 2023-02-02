from psl import * 

#SSD Settings
ssd = 64
ch = 16
ch_size = ssd//ch
step = ch_size

def main():
    #print psl by N(2~6)
    for N in range(2,7):
        avg=ssd/N
        pivot=((avg+(step-0.001))//step*step)
        min=int((pivot/2+(step-0.001))//step*step)
        max=int(ssd-min*(N-1))

        #set this condition
        print("[N:%d avg:%.1f pivot:%d min:%2d max:%2d]"%(N, avg, pivot, min, max))
        
        #find all partition set
        all_solutions   = get_full_partition_set_list(N, min, step, ssd)
        validity_dict   = count_each_part(N, all_solutions, min, max, step)
        print_list(all_solutions)
        print_dict(validity_dict)
        
        #find minimum partition set
        print("\n---SOLUTION---")
        minimum_sols    = get_minimum_partition_set_list(N, min, max, step, all_solutions)
        validity_dict   = count_each_part(N, minimum_sols, min, max, step)
        print_list(minimum_sols)
        print_dict(validity_dict)
        
        #calculate compression rate
        len_one = N*((max-min)//step+1)
        len_all = len(all_solutions)
        len_min = len(minimum_sols)
        print("Compression")
        print("single : ", "%3d"%(len_one), " -> ", len_min, " = ", round(len_min*100/len_one), "%", sep='')
        print("full   : ", "%3d"%(len_all), " -> ", len_min, " = ", round(len_min*100/len_all), "%", sep='')
        
        print()

#entry point(first call)
if __name__ == '__main__':
    main()
    