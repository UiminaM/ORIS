import threading

def count_words(text_chunk, result_dict, lock):
    words = text_chunk.split()
    local_count = {}

    for word in words:
        word = word.lower()
        if word in local_count:
            local_count[word] += 1
        else:
            local_count[word] = 1

    with lock:
        for word, count in local_count.items():
            if word in result_dict:
                result_dict[word] += count
            else:
                result_dict[word] = count


def split_text_into_chunks(text, num_chunks):
    words = text.split()
    chunk_size = len(words) // num_chunks
    chunks = []

    for i in range(num_chunks):
        start_index = i * chunk_size
        if i == num_chunks - 1:
            end_index = len(words)
        else:
            end_index = (i + 1) * chunk_size
        chunks.append(' '.join(words[start_index:end_index]))

    return chunks




with open("../ORIS/text.txt", 'r') as file:
    text = file.read()


num_threads = int(input("Введите количество потоков для подсчета: "))
text_chunks = split_text_into_chunks(text, num_threads)

result = {}
lock = threading.Lock()

Threads = []
for chunk in text_chunks:
    th = threading.Thread(target=count_words, args=(chunk, result, lock))
    Threads.append(th)
    th.start()

for thread in Threads:
    thread.join()

print("Итоговая статистика:")
for word, count in result.items():
    print(f"{word}: {count}")


