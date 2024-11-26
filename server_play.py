import socket
import threading
import time

clients = []
addresses = []
cities_used = []
counter = 0

def broadcast(msg):
    for client in clients:
        client.send(msg.encode())

def accept_incoming_connections(sock):
    while len(clients) < 2:
        client, client_address = sock.accept()
        clients.append(client)
        addresses.append(client_address)

        if len(clients) == 2:
            broadcast("Игра началась! Первый игрок, введите город.")
            threading.Thread(target=play_game).start()
        else:
            client.send("Вы подключены. Ожидание второго игрока...".encode())

def play_game():
    current_player = 0
    game_active = True
    while game_active:
        client = clients[current_player]
        global counter
        counter += 1
        timer_thread = threading.Thread(target=timer, args=(current_player, counter), daemon=True)
        timer_thread.start()

        while True:
            client.send("Введите город: ".encode())
            try:
                city = client.recv(1024).decode().strip()
                if city.lower() == 'exit':
                    game_active = False
                    break
                elif check_city(city):
                    cities_used.append(city)
                    broadcast(f"Игрок №{current_player + 1} назвал город: {city}")
                    break
                else:
                    client.send("Неправильный ввод, попробуйте снова.\n".encode())
            except:
                break
        current_player = 1 - current_player
    end_game()

def check_city(city):
    if city in cities_used:
        return False
    if len(cities_used) > 0 and city[0].lower() != cities_used[-1][-1].lower():
        return False
    return True

def timer(current_player, current_number):
    global counter
    time.sleep(30)
    if current_number == counter:
        broadcast(f"Игрок №{current_player + 1} не ответил вовремя. Игра окончена. Победитель: Игрок №{1 - current_player + 1}.")
        end_game()

def end_game():
    broadcast('end')
    for client in clients:
        client.close()

    clients.clear()
    addresses.clear()
    cities_used.clear()

def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("127.0.0.1", 10015))
    sock.listen(2)
    print("Ожидание подключеня...")

    accept_thread = threading.Thread(target=accept_incoming_connections, args=(sock,))
    accept_thread.start()

if __name__ == "__main__":
    main()