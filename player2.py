import socket
import threading


def receive_messages(sock):
    while True:
        msg = sock.recv(1024).decode()
        if msg == "end":
            sock.close()
            break
        else:
            print(msg)


def send_message(sock):
    while True:
        try:
            msg = input()
            if msg.lower() == 'exit':
                sock.send(msg.encode())
                break
            sock.send(msg.encode())
        except:
            break


def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(("127.0.0.1", 10015))

    threading.Thread(target=receive_messages, args=(sock,), daemon=True).start()
    send_message(sock)


if __name__ == "__main__":
    main()