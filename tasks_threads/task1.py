import threading

def output_name():
    print(f"Name thread: {threading.current_thread().name}")

n = int(input("Введите количество потоков: "))
threads = [threading.Thread(target=output_name) for _ in range(n)]

for i in threads:
    i.start()
    i.join()

print("Все потоки завершились")
