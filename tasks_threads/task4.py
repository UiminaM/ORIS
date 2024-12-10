import threading
def factorial(start, end):
    print(f"Поток {threading.current_thread().name} начал свою работу")
    k = 1
    for j in range(start, end):
        k *= j

    with lock:
            res.append(k)
    print(f"Поток {threading.current_thread().name} завершил работу. Результат его выполнения: {k}")

lock = threading.Lock()
res = []
n = int(input("Введите количество потоков: "))
num = int(input("Введите число, факториал которого нужно найти: "))

parts = num // n
Threads = []

for i in range(n):
    st = i * parts + 1
    en = parts * (i + 1) + 1 if i < n - 1 else num + 1
    th = threading.Thread(target=factorial, args=(st, en))
    th.start()
    Threads.append(th)

for th in Threads:
    th.join()


result = 1
for i in res:
    result *= i

print(f"Итоговый результат: {result}")