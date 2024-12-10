import threading
from math import sqrt
def search_primes(start, end):
    cur_res = []
    for i in range(start, end):
        if i < 2:
            continue
        is_prime = True
        for j in range(2, int(sqrt(i)) + 1):
            if i % j == 0:
                is_prime = False
                break
        if is_prime:
            cur_res.append(i)

    with lock:
        res.extend(cur_res)

print("Программа для поиска простых чисел в заданном диапазоне.")
rangePrimes1 = int(input("Введите начало диапазона: "))
rangePrimes2 = int(input("Введите конец диапазона: "))

lock = threading.Lock()
res = []
num_threads = (rangePrimes2 - rangePrimes1) // 10 if (rangePrimes2 - rangePrimes1) // 10 > 0 else 1
parts = (rangePrimes2 - rangePrimes1 + 1) // num_threads
Threads = []

for i in range(num_threads):
    start = rangePrimes1 + i * parts
    end = rangePrimes1 + (i + 1) * parts if i < num_threads - 1 else rangePrimes2 + 1
    if start < end:
        th = threading.Thread(target=search_primes, args=(start, end,))
        th.start()
        Threads.append(th)

for th in Threads:
    th.join()

res.sort()
print("Найденные простые числа:", ", ".join(map(str, res)))