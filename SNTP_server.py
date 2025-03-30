import socket
import ntplib
from time import ctime, time
import struct
import sys

UDP_PORT = 12345
CONFIG_FILE = 'sntp_server.conf'
HOST_OTHER_SNTP = 'time.windows.com'


def read_offset():
    """Чтение смещения из конфигурационного файла"""
    try:
        with open(CONFIG_FILE, 'r') as f:
            offset = int(f.read().strip())
            return offset
    except FileNotFoundError:
        print(f"Ошибка: Конфигурационный файл {CONFIG_FILE} не найден.")
        sys.exit(1)
    except ValueError:
        print(
            f"Ошибка: Некорректное значение в конфигурационном файле {CONFIG_FILE}.")
        sys.exit(1)


def get_accurate_time():
    """Получение точного времени от другого SNTP сервера"""
    ntp_client = ntplib.NTPClient()
    try:
        response = ntp_client.request(HOST_OTHER_SNTP, timeout=10)
        return response.tx_time
    except ntplib.NTPException as e:
        print(f"Ошибка при запросе к SNTP серверу: {e}")
        return None
    except socket.gaierror:
        print(f"Ошибка: Не удалось разрешить доменное имя {HOST_OTHER_SNTP}.")
        return None
    except socket.timeout:
        print("Ошибка: Сервер 'time.windows.com' не ответил в течение 10 секунд.")
        return None


def to_ntp_time(timestamp):
    """Преобразует Unix-время в NTP-время."""
    ntp_epoch = 2208988800
    return int((timestamp + ntp_epoch) * 2 ** 32)


def sntp_server():
    """Основная функция SNTP сервера"""
    offset = read_offset()

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('127.0.0.1', UDP_PORT))

    print(f"SNTP сервер запущен на порту {UDP_PORT} с отклонением {offset} секунд.")

    while True:
        data, addr = sock.recvfrom(1024)
        print(f"Получен запрос от {addr}")

        accurate_time = get_accurate_time()
        adjusted_time = accurate_time + offset

        # Преобразуем время в формат, подходящий для SNTP
        sntp_time = int(adjusted_time + 2208988800)

        # Формируем ответ (упрощенный SNTP пакет)
        response = bytearray(48)
        response[0] = 0x24  # Версия и режим
        response[1] = 1  # Stratum
        response[2] = 10  # Poll
        response[3] = 0xEC  # Precision
        response[4:8] = struct.pack('!I', 0)
        response[8:12] = struct.pack('!I', 0)
        response[12:16] = b'LOCK'

        reference_time = to_ntp_time(adjusted_time)  # Время последней синхронизации
        originate_time = to_ntp_time(struct.unpack('!I', data[40:44])[0] / 2 ** 32)  # Время запроса клиента
        receive_time = to_ntp_time(time())  # Время получения запроса
        transmit_time = to_ntp_time(adjusted_time)  # Время отправки ответа

        # Записываем временные метки в пакет
        response[16:24] = struct.pack('!Q',reference_time)
        response[24:32] = struct.pack('!Q',originate_time)
        response[32:40] = struct.pack('!Q', receive_time)
        response[40:48] = struct.pack('!Q',transmit_time)

        sock.sendto(response, addr)
        print(f"Отправлено время: {ctime(adjusted_time)}")


if __name__ == "__main__":
    sntp_server()
