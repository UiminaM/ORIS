import os
import threading
import queue

def search_files(directory, pattern, result_queue):
    try:
        for root, dirs, files in os.walk(directory):
            for file in files:
                if pattern in file:
                    result_queue.put(os.path.join(root, file))
    except Exception as e:
        print(f"Ошибка при обработке каталога {directory}: {e}")

def worker(directories, pattern, result_queue):
    for directory in directories:
        search_files(directory, pattern, result_queue)

directories = input("Введите каталоги для поиска: ").split(' ')
directories = [d.strip() for d in directories]
pattern = input("Введите паттерн для поиска: ")

result_queue = queue.Queue()
max_threads = int(input("Введите максимальное количество потоков для поиска: "))
Threads = []

for i in range(0, len(directories), max_threads):
    thread_group = directories[i:i + max_threads]
    thread = threading.Thread(target=worker, args=(thread_group, pattern, result_queue))
    Threads.append(thread)
    thread.start()

for thread in Threads:
    thread.join()

results = []
while not result_queue.empty():
    results.append(result_queue.get())

print("Найденные файлы:")
for result in results:
    print(result)


