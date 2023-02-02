#각 파티션이 모든 크기(min~max)를 적어도 한번씩은 포함했는지 확인
def is_valid_result(xs):
    for p in xs.values():
        if 0 in p:
            return False
    return True

#각 조합의 파티션별 크기별 횟수 출력
def count_each_part(N, xs, min, max, step):
    
    ret = {}
    for i in range(min, max+1, step) :
        ret[i] = [0 for _ in range(N)]

    for parts in xs :
        if parts == None :
            continue
        for wl in range(len(parts)):
            ret[parts[wl]][wl] += 1
            
    return ret

#ps in psl 출력
def print_list(list):
    print("partition set list")
    print("index", end='')
    for i in range(len(list[0])):
        print(" p%d"%(i+1), end='')
    print()
    
    none = 0
    for i in range(len(list)):
        if list[i] == None:
            none += 1
            print(" rm:[  ]")
            continue

        print("%3d:["%(i+1), end = ' ')
        for j in list[i]:
            print("%2d"%(j) , end = ' ')
        print("]")
    print("num :", len(list) - none)
    print()

#size(row) * part(col) table 
def print_dict(dict):
    print("partition table")
    
    print("size ", end='')
    for i in range(len(list(dict.values())[0])):
        print(" p%d"%(i+1), end='')
    print()
    
    for k in dict.keys():
        print("%3d:["%(k), end = ' ')
        for j in dict[k]:
            print("%2d"%(j) , end = ' ')
        print("]")