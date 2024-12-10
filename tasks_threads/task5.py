import threading

def sort_subarray(subarray, index):
    subarray.sort()
    sorted_subarrays[index] = subarray

def merge_sorted_arrays(arrays):
    merged = []
    indices = [0] * len(arrays)
    while True:
        min_value = None
        min_index = -1

        for i in range(len(arrays)):
            if indices[i] < len(arrays[i]):
                if min_value is None or arrays[i][indices[i]] < min_value:
                    min_value = arrays[i][indices[i]]
                    min_index = i

        if min_index == -1:
            break
        merged.append(min_value)
        indices[min_index] += 1
    return merged

n = int(input("Введите количество элементов в массиве: "))
arr = [int(input()) for _ in range(n)]
num_threads = 10
subarrays = [arr[i::num_threads] for i in range(num_threads)]
sorted_subarrays = [None] * num_threads
Threads = []

for i in range(num_threads):
    th = threading.Thread(target=sort_subarray, args=(subarrays[i], i))
    th.start()
    Threads.append(th)


for th in Threads:
    th.join()

sorted_array = merge_sorted_arrays(sorted_subarrays)
print("Отсортированный массив:", sorted_array)