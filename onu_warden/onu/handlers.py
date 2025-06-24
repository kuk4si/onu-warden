import pexpect
from pathlib import Path
import re
import os
from django.conf import settings

def onu_warden(ip_address, ports, max_dbm):

    #print(max_dbm)

    start_port = 1
    script_dir = Path(__file__).parent.resolve()
    results_dir = script_dir / 'results'
    results_dir.mkdir(exist_ok=True)
    
    accounts_path = results_dir / 'accounts.txt'
    rx_tx_path = results_dir / 'rx_tx.txt'
    merged_result_path = results_dir / 'merged_result.txt'

    host = ip_address
    username = os.getenv("DJANGO_TELNET_LOGIN")
    password = os.getenv("DJANGO_TELNET_PASSWORD")

    print(settings.SECRET_KEY)

    # Открываем файлы в режиме записи
    with open(accounts_path, 'wb') as accounts, open(rx_tx_path, 'wb') as rx_tx:
        # Старт сессии
        session = pexpect.spawn(f"telnet {host}")
        session.setwinsize(2000, 2000)

        # Аутентификация
        session.expect(">>User name:")
        session.sendline(username)
        session.expect(">>User password:")
        session.sendline(password)

        # Переход в режим конфигурации
        session.expect(">")
        session.sendline('enable')
        session.expect("#")
        session.sendline('config')
        session.expect("#")

        # Запись в accounts.txt
        session.logfile = accounts
        for i in range(start_port, int(ports) + 1):
            session.sendline(f"show ont info 0/0 {i} all")
            session.expect("#")
        
        # Сбрасываем буфер и отключаем логирование
        session.logfile = None
        session.flush()
        
        # Переходим в EPON интерфейс
        session.sendline("interface epon 0/0")
        session.expect("0/0", timeout=10)

        # Запись optical-info в rx_tx.txt (цикл по тем же портам)
        session.logfile = rx_tx
        for i in range(start_port, int(ports) + 2):
            session.sendline(f"show ont optical-info {i} all")  # Добавлен номер ONT ({i})
            session.expect("#", timeout=10)
        session.logfile = None

        # Закрываем сессию
        session.close()




    # Обработка файлов (удаление лишних строк)
    def clean_file(file_path, words_to_remove, start_line=0, end_line=0):
        with open(file_path, 'r') as file:
            lines = file.readlines()
            # Фильтрация строк


        if words_to_remove:
            lines = [
                line for line in lines 
                if not any(word in line.lower() for word in words_to_remove)
            ]
        
        with open(file_path, 'w') as file:
            file.writelines(lines)

    clean_file(accounts_path, words_to_remove = ["show", "  total", "(config)"], start_line=2, end_line=2)
    clean_file(rx_tx_path, words_to_remove = ["show", "optical-info", "  --           --"], start_line=3, end_line=2)

    # Объединение файлов
    def merge_tables_properly(file1, file2, output_file):
        with open(file1, 'r') as f1, open(file2, 'r') as f2:
            table1 = f1.readlines()
            table2 = f2.readlines()
        
        table1_width = max(len(line.rstrip()) for line in table1)
        separator = '    '  # 4 пробела
        
        with open(output_file, 'w') as out:
            for i in range(max(len(table1), len(table2))):
                line1 = table1[i].rstrip() if i < len(table1) else ''
                line2 = table2[i].rstrip() if i < len(table2) else ''
                out.write(f"{line1.ljust(table1_width)}{separator}{line2}\n")

    merge_tables_properly(accounts_path, rx_tx_path, merged_result_path)



    def filter_rx_optical(file_path, threshold):
        """
        Фильтрует строки по Rx optical power (единственное отрицательное число в строке).
        Удаляет строки, содержащие слово "initial" (в любом регистре).
        threshold - минимальное допустимое значение (уже учитывает знак минус).
        """
        with open(file_path, 'r') as f:
            lines = f.readlines()
        
        filtered_lines = []
        
        for line in lines:
            # Пропускаем строки где есть слова )))
            if "initial" in line.lower():
                continue
            if "---------------" in line.lower():
                continue
            if "state" in line.lower():
                continue
            if "bias" in line.lower():
                continue
            if "            " in line.lower():
                continue
                
                
            # Ищем все отрицательные числа в строке
            negative_numbers = re.findall(r'-\d+\.\d+', line)
            
            # Если нет отрицательных чисел - сохраняем строку (возможно заголовок)
            if not negative_numbers:
                filtered_lines.append(line)
                continue
                
            try:
                rx_power = float(negative_numbers[0])
                if rx_power <= threshold:
                    filtered_lines.append(line)
            except (ValueError, IndexError):
                filtered_lines.append(line)
        
        # Перезаписываем файл
        with open(file_path, 'w') as f:
            f.writelines(filtered_lines)

    if max_dbm:
        filter_rx_optical(merged_result_path, max_dbm)
