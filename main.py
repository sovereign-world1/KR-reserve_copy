import configparser
import requests
import json
from tqdm import tqdm
from datetime import datetime

class VK:
    def __init__(self, token, version='5.199'):
        # Инициализация параметров для запросов к API ВКонтакте
        self.params = {
            'access_token': token,  # Токен доступа к API ВКонтакте
            'v': version  # Версия API ВКонтакте
        }
        self.base = 'https://api.vk.com/method'  # Базовый URL для запросов к API ВКонтакте

    def get_photos(self, user_id, count=5, album_id='profile'):
        # Получение фотографий пользователя из указанного альбома
        url = f'{self.base}/photos.get'  # URL для метода photos.get
        params = {
            'owner_id': user_id,  # ID пользователя, чьи фотографии нужно получить
            'count': count,  # Количество фотографий для получения
            'album_id': album_id,  # ID альбома (по умолчанию 'profile')
            'extended': 1,  # Получение расширенной информации о фотографиях
            'photo_sizes': 1  # Получение информации о различных размерах фотографий
        }
        params.update(self.params)  # Обновление параметров запроса
        response = requests.get(url, params=params)  # Выполнение GET-запроса
        if response.status_code != 200:
            print(f"Ошибка при получении фотографий: {response.status_code} - {response.text}")
            return []
        return response.json().get('response', {}).get('items', [])  # Возврат списка фотографий

    def sort_photos_by_likes_and_size(self, photos):
        # Сортировка фотографий по количеству лайков и размеру
        def photo_key(photo):
            # Ключ для сортировки: количество лайков и размер (ширина * высота)
            likes = photo.get('likes', {}).get('count', 0)  # Количество лайков
            sizes = photo.get('sizes', [])  # Список размеров фотографии
            max_size = max(sizes, key=lambda x: x['width'] * x['height'], default={})  # Наибольший размер
            return (likes, -max_size.get('width', 0) * max_size.get('height', 0))  # Кортеж для сортировки
        
        sorted_photos = sorted(photos, key=photo_key, reverse=True)  # Сортировка фотографий
        return sorted_photos

class YD:
    def __init__(self, token):
        # Инициализация параметров для запросов к API Яндекс.Диска
        self.headers = {
            'Authorization': f'OAuth {token}'  # Токен доступа к API Яндекс.Диска
        }
        self.base = 'https://cloud-api.yandex.net/v1/disk/resources/'  # Базовый URL для запросов к API Яндекс.Диска

    def ensure_folder_exists(self, folder_name):
        # Создание папки на Яндекс.Диске, если она не существует
        url = f'{self.base}?path={folder_name}'  # URL для проверки существования папки
        response = requests.get(url, headers=self.headers)  # Выполнение GET-запроса
        if response.status_code == 200:
            print(f"Папка {folder_name} уже существует.")
            return True
        elif response.status_code == 404:
            # Папка не существует, создаем её
            create_response = requests.put(url, headers=self.headers)  # Выполнение PUT-запроса для создания папки
            if create_response.status_code == 201:
                print(f"Папка {folder_name} успешно создана.")
                return True
            else:
                print(f"Ошибка при создании папки {folder_name}: {create_response.status_code} - {create_response.text}")
                return False
        else:
            print(f"Ошибка при проверке существования папки {folder_name}: {response.status_code} - {response.text}")
            return False

    def upload_file(self, file_content, file_name, folder_name):
        # Загрузка файла на Яндекс.Диск
        full_path = f"{folder_name}/{file_name}"  # Полный путь к файлу на Яндекс.Диске
        url = f'{self.base}upload?path={full_path}&overwrite=true'  # URL для получения ссылки на загрузку
        print(f"Полный путь к файлу на Яндекс.Диске: {full_path}")  # Логирование полного пути к файлу
        print(f"URL для загрузки файла {file_name}: {url}")  # Логирование URL для отладки
        response = requests.get(url, headers=self.headers)  # Выполнение GET-запроса
        if response.status_code != 200:
            print(f"Ошибка при получении ссылки для загрузки файла {file_name}: {response.status_code} - {response.text}")
            return False
        
        upload_url = response.json().get('href')  # Получение ссылки для загрузки файла
        if not upload_url:
            print(f"Ссылка для загрузки файла {file_name} не найдена.")
            return False
        
        try:
            upload_response = requests.put(upload_url, data=file_content)  # Выполнение PUT-запроса для загрузки файла
            if upload_response.status_code == 201:
                print(f"Файл {file_name} успешно загружен в папку {folder_name}.")
                return True
            else:
                print(f"Ошибка при загрузке файла {file_name}: {upload_response.status_code} - {upload_response.text}")
                return False
        except Exception as e:
            print(f"Ошибка при загрузке файла {file_name} на Яндекс.Диск: {e}")
            return False

def save_photo_info_to_json(photo_info_list, filename='photo_info.json'):
    # Сохранение информации о фотографиях в JSON-файл
    with open(filename, 'w') as f:
        json.dump(photo_info_list, f, ensure_ascii=False, indent=4)  # Запись данных в JSON-файл

def main():
    # Основная функция программы
    config = configparser.ConfigParser()  # Создание объекта для работы с конфигурационным файлом
    config.read('settings.ini')  # Чтение конфигурационного файла
    vk_token = config['Tokens']['vk_token']  # Получение токена ВКонтакте из конфигурационного файла
    yd_token = config['Tokens']['yd_token']  # Получение токена Яндекс.Диска из конфигурационного файла

    vk = VK(vk_token)  # Инициализация объекта класса VK
    yd = YD(yd_token)  # Инициализация объекта класса YD

    vk_user_id = input("Введите ID пользователя VK: ")  # Ввод ID пользователя ВКонтакте
    photo_count = int(input("Введите количество фотографий для резервного копирования (по умолчанию 5): ") or 5)  # Ввод количества фотографий

    photos = vk.get_photos(vk_user_id, count=photo_count)  # Получение фотографий пользователя
    sorted_photos = vk.sort_photos_by_likes_and_size(photos)  # Сортировка фотографий

    folder_name = f"backup_{vk_user_id}"  # Создание имени папки для резервного копирования
    if not yd.ensure_folder_exists(folder_name):  # Создание папки на Яндекс.Диске, если она не существует
        print("Не удалось создать папку на Яндекс.Диске. Завершение программы.")
        return

    photo_info_list = []  # Список для хранения информации о фотографиях
    for photo in tqdm(sorted_photos, desc="Загрузка фотографий"):  # Прогресс-бар для отслеживания процесса загрузки
        likes_count = photo.get('likes', {}).get('count', 0)  # Количество лайков фотографии
        date = datetime.fromtimestamp(photo.get('date', 0)).strftime('%Y-%m-%d_%H-%M-%S')  # Дата загрузки фотографии
        sizes = photo.get('sizes', [])  # Список размеров фотографии
        max_size = max(sizes, key=lambda x: x['width'] * x['height'], default={})  # Наибольший размер фотографии
        file_name = f"{likes_count}.jpg"  # Имя файла на основе количества лайков
        if any(p['file_name'] == file_name for p in photo_info_list):
            # Если имя файла уже существует, добавляем дату загрузки
            file_name = f"{likes_count}_{date}.jpg"
        
        photo_url = max_size.get('url', '')  # URL фотографии
        if not photo_url:
            print(f"URL для фотографии не найден.")
            continue
        
        photo_info = {
            'file_name': file_name,  # Имя файла
            'size': max_size.get('type', '')  # Размер фотографии
        }
        photo_info_list.append(photo_info)  # Добавление информации о фотографии в список

        try:
            # Загрузка фотографии в переменную
            response = requests.get(photo_url)
            if response.status_code != 200:
                print(f"Ошибка при загрузке файла {file_name} с ВКонтакте: {response.status_code} - {response.text}")
                continue
            file_content = response.content  # Содержимое файла
        except Exception as e:
            print(f"Ошибка при загрузке файла {file_name} с ВКонтакте: {e}")
            continue
        
        yd.upload_file(file_content, file_name, folder_name)  # Загрузка фотографии на Яндекс.Диск

    save_photo_info_to_json(photo_info_list)  # Сохранение информации о фотографиях в JSON-файл
    print("Процесс завершен.")  # Сообщение о завершении процесса

if __name__ == "__main__":
    main()  # Запуск основной функции при запуске скрипта