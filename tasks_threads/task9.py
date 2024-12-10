import threading
import queue
import math
from scipy.integrate import quad

def calculate_factorial(n, result_queue):
    try:
        if n < 0:
            raise ValueError("Факториал не определен для отрицательных чисел.")
        result = math.factorial(n)
        result_queue.put(("factorial", n, result))
    except Exception as e:
        result_queue.put(("factorial", n, str(e)))

def calculate_power(base, exponent, result_queue):
    try:
        result = base ** exponent
        result_queue.put(("power", (base, exponent), result))
    except Exception as e:
        result_queue.put(("power", (base, exponent), str(e)))

def calculate_integration(func, a, b, result_queue):
    try:
        result, _ = quad(func, a, b)
        result_queue.put(("integration", (a, b), result))
    except Exception as e:
        result_queue.put(("integration", (a, b), str(e)))


result_queue = queue.Queue()
Threads = []

n = int(input("Введите число для подсчета факториала: "))
thread_factorial = threading.Thread(target=calculate_factorial, args=(n, result_queue))
Threads.append(thread_factorial)
thread_factorial.start()


base = int(input("Введите основание степени: "))
exponent = int(input("Введите показатель степени: "))
thread_power = threading.Thread(target=calculate_power, args=(base, exponent, result_queue))
Threads.append(thread_power)
thread_power.start()

func = lambda x: x ** 2
a = int(input("Введите начало интервала: "))
b = int(input("Введите конец интервала: "))
thread_integration = threading.Thread(target=calculate_integration, args=(func, a, b, result_queue))
Threads.append(thread_integration)
thread_integration.start()

for thread in Threads:
    thread.join()

print("Результаты вычислений:")
while not result_queue.empty():
    operation, input_data, result = result_queue.get()
    if operation == "factorial":
        print(f"Факториал {input_data} = {result}")
    elif operation == "power":
        print(f"{input_data[0]} в степени {input_data[1]} = {result}")
    elif operation == "integration":
        print(f"Интеграл функции на интервале [{input_data[0]}, {input_data[1]}] = {result}")

