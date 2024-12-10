import threading
import random
import time

class Parking:
    def __init__(self, capacity):
        self.capacity = capacity
        self.current_auto = 0
        self.lock = threading.Lock()

    def park_auto(self, num):
        with self.lock:
            if self.current_auto < self.capacity:
                self.current_auto += 1
                print(f"Автомобиль №{num} припаркован.")
                return True
            else:
                print("Нет свободных мест для парковки.")
                return False

    def leave_auto(self, num):
        with self.lock:
            if self.current_auto > 0:
                self.current_auto -= 1
                print(f"Автомобиль №{num} уехал.")
            else:
                print("Нет автомобилей на парковке.")

def auto(parking_lot, num):
    if parking_lot.park_auto(num):
        parking_time = random.randint(1, 5)  # Время на парковке от 1 до 5 секунд
        time.sleep(parking_time)
        parking_lot.leave_auto(num)


capacity = int(input("Введите максимальное количество мест на парковке: "))
parking_lot = Parking(capacity)

threads = []
for i in range(10):
    thread = threading.Thread(target=auto, args=(parking_lot, i+1,))
    threads.append(thread)
    thread.start()
    time.sleep(random.uniform(0.1, 0.5))

for thread in threads:
    thread.join()
