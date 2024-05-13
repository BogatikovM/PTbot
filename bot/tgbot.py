import logging
import re
import paramiko
import os
import psycopg2

from telegram import Update, ForceReply
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler
from dotenv import load_dotenv
from psycopg2 import Error

load_dotenv()

TOKEN = os.getenv('TOKEN')
host = os.getenv('RMHOST')
port = os.getenv('PORT')
username = os.getenv('HOSTUSER')
password = os.getenv('PASSWORD')
userDB = os.getenv('USERDB')
passwordDB = os.getenv('PASSWORDDB')
hostDB = os.getenv('HOSTDB')
portDB = os.getenv('PORTDB')
database = os.getenv('DATABASE')

# Подключаем логирование
logging.basicConfig(
    filename='logfile.txt', format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

storage = '' # глобальное хранилище
columns = {
    'numbers': 'number',
    'emails': 'email'
}

def start(update: Update, context):
    user = update.effective_user
    update.message.reply_text(f'Привет {user.full_name}!')


def helpCommand(update: Update, context):
    update.message.reply_text('/find_email\n\
/find_phone_number\n\
/verify_password\n\
/get_release\n\
/get_uname\n\
/get_uptime\n\
/get_df\n\
/get_free\n\
/get_mpstat\n\
/get_w\n\
/get_auths\n\
/get_critical\n\
/get_ps\n\
/get_ss\n\
/get_apt_list\n\
/get_services\n\
/get_repl_logs\n\
/get_emails\n\
/get_phone_numbers\n\
                        ')

def terminalCommand(command):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=host, username=username, password=password, port=port)
    stdin, stdout, stderr = client.exec_command(command)
    data = stdout.read() + stderr.read()
    client.close()
    data = str(data).replace('\\n', '\n').replace('\\t', '\t')[2:-1]
    return data

def unameCommand(update: Update, context):
    data = terminalCommand('uname -a')
    update.message.reply_text(data)

def releaseCommand(update: Update, context):
    data = terminalCommand('lsb_release -a')
    update.message.reply_text(data)

def uptimeCommand(update: Update, context):
    data = terminalCommand('uptime')
    update.message.reply_text(data)

def dfCommand(update: Update, context):
    data = terminalCommand('df')
    update.message.reply_text(data) 

def freeCommand(update: Update, context):
    data = terminalCommand('free')
    update.message.reply_text(data)   

def mpstatCommand(update: Update, context):
    data = terminalCommand('mpstat')
    update.message.reply_text(data)

def wCommand(update: Update, context):
    data = terminalCommand('w')
    update.message.reply_text(data)

def authsCommand(update: Update, context):
    data = terminalCommand('last -10')
    update.message.reply_text(data)

def criticalCommand(update: Update, context):
    data = terminalCommand('journalctl -p crit -n 5')
    update.message.reply_text(data)

def psCommand(update: Update, context):
    data = terminalCommand('ps')
    update.message.reply_text(data)

def ssCommand(update: Update, context):
    data = terminalCommand('ss -tulpn')
    update.message.reply_text(data)

def servicesCommand(update: Update, context):
    data = terminalCommand('systemctl --type=service --state=running')
    update.message.reply_text(data)

def ReplLogsCommand(update: Update, context):
    data = terminalCommand('cat /var/log/postgresql/postgresql-15-main.log | grep "repl_user" | head -n 20')
    #data = terminalCommand('docker logs db | grep "replication" | head -n 20')
    update.message.reply_text(data)

def selectData(table: str):
    connection = None

    try:
        connection = psycopg2.connect(user=userDB,
                                password=passwordDB,
                                host=hostDB,
                                port=portDB, 
                                database=database)

        cursor = connection.cursor()
        cursor.execute(f"SELECT * FROM {table};")
        data = cursor.fetchall()
        logging.info("Команда успешно выполнена")
        return data
    except (Exception, Error) as error:
        logging.error("Ошибка при работе с PostgreSQL: %s", error)
    finally:
        if connection is not None:
            cursor.close()
            connection.close()

def insertData(table: str, dataList: list):
    connection = None

    try:
        connection = psycopg2.connect(user=userDB,
                                password=passwordDB,
                                host=hostDB,
                                port=portDB, 
                                database=database)

        cursor = connection.cursor()
        for i in dataList:
            cursor.execute(f"INSERT INTO {table} ({columns[table]}) VALUES ('{i}');")
        connection.commit()
        logging.info("Команда успешно выполнена")
        message = "Команда успешно выполнена"
    except (Exception, Error) as error:
            logging.error("Ошибка при работе с PostgreSQL: %s", error)
            message = "Ошибка при выполнении операции"
    finally:
        if connection is not None:
            cursor.close()
            connection.close()
            logging.info("Соединение с PostgreSQL закрыто")
        return message

def getEmailsCommand(update: Update, context):
    data = selectData('emails')
    emails = ''
    for row in data:
        emails += f'{row[0]}. {row[1]} \n'
    update.message.reply_text(emails)

def getNumbersCommand(update: Update, context):
    data = selectData('numbers')
    numbers = ''
    for row in data:
        numbers += f'{row[0]}. {row[1]} \n'
    update.message.reply_text(numbers)

def findPhoneNumbersCommand(update: Update, context):
    update.message.reply_text('Введите текст для поиска телефонных номеров: ')

    return 'findPhoneNumbers'

def findPhoneNumbers (update: Update, context):
    user_input = update.message.text # Получаем текст, содержащий(или нет) номера телефонов

    phoneNumRegex = re.compile(r'(8|\+7)(\s|-){0,1}(\(\d{3}\)|\d{3})(\s|-){0,1}(\d{3})(\s|-){0,1}(\d{2})(\s|-){0,1}(\d{2})')

    phoneNumberList = phoneNumRegex.findall(user_input) # Ищем номера телефонов

    if not phoneNumberList: # Обрабатываем случай, когда номеров телефонов нет
        update.message.reply_text('Телефонные номера не найдены')
        return ConversationHandler.END # Завершаем выполнение функции

    phoneNumbers = '' # Создаем строку, в которую будем записывать номера телефонов
    for i in range(len(phoneNumberList)):
        phoneNumber = ''.join(phoneNumberList[i])
        phoneNumbers += f'{i+1}. {phoneNumber}\n' # Записываем очередной номер
        
    update.message.reply_text(phoneNumbers) # Отправляем сообщение пользователю

    global storage
    storage = phoneNumberList
    update.message.reply_text('Записать данные в базу? (yes/no)')
    return 'writePhoneNumbers'

def writePhoneNumbers (update: Update, context):
    global storage
    user_input = update.message.text
    if user_input == 'yes':
        phoneNumbersList = []
        for i in range(len(storage)):
            phoneNumbersList.append(''.join(storage[i]))
        message = insertData('numbers', phoneNumbersList)
        update.message.reply_text(message)
    else:
        update.message.reply_text('Данные не записаны')

    return ConversationHandler.END # Завершаем работу обработчика диалога

def findEmailsCommand(update: Update, context):
    update.message.reply_text('Введите текст для поиска электронных почт: ')

    return 'findEmails'

def findEmails (update: Update, context):
    user_input = update.message.text # Получаем текст

    emailRegex = re.compile(r"[a-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+/=?^_`{|}~-]+)*@(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?")

    emailsList = emailRegex.findall(user_input)

    if not emailsList: 
        update.message.reply_text('Электронные почты не найдены')
        return ConversationHandler.END# Завершаем выполнение функции

    emails = ''
    for i in range(len(emailsList)):
        emails += f'{i+1}. {emailsList[i]}\n'
        
    update.message.reply_text(emails) # Отправляем сообщение пользователю
    
    global storage
    storage = emailsList
    update.message.reply_text('Записать данные в базу? (yes/no)')
    return 'writeEmails'

def writeEmails (update: Update, context):
    global storage
    user_input = update.message.text
    if user_input == 'yes':
        emailsList = []
        for i in range(len(storage)):
            emailsList.append(''.join(storage[i]))
        message = insertData('emails', emailsList)
        update.message.reply_text(message)
    else:
        update.message.reply_text('Данные не записаны')

    return ConversationHandler.END # Завершаем работу обработчика диалога

def verifyPasswordCommand(update: Update, context):
    update.message.reply_text('Введите пароль для проверки: ')

    return 'verifyPassword'

def verifyPassword (update: Update, context):
    user_input = update.message.text # Получаем текст

    passwordRegex = re.compile(r'(?=.*[0-9])(?=.*[!@#$%^&*()])(?=.*[a-z])(?=.*[A-Z])[0-9a-zA-Z!@#$%^&*()]{8,}')

    password = passwordRegex.search(user_input) # Ищем номера телефонов

    if not password: 
        update.message.reply_text('Пароль простой')        
    else:
        update.message.reply_text('Пароль сложный')
    
    return ConversationHandler.END # Завершаем работу обработчика диалога

def aptListCommand(update: Update, context):
    update.message.reply_text('Введите пакет для поиска (all для просмотра всех пакетов): ')

    return 'aptList'

def aptList (update: Update, context):
    user_input = update.message.text # Получаем текст

    if user_input == 'all':
        data = terminalCommand('apt list --installed | head -n 30')   
    else:
        user_input = user_input.replace('|', '').replace('&','').replace(';','').replace('\n','').replace('`','').replace('$','')
        data = terminalCommand(f'apt list --installed | grep "{user_input}" | head -n 30') 

    update.message.reply_text(data)      
    return ConversationHandler.END # Завершаем работу обработчика диалога

def main():
    updater = Updater(TOKEN, use_context=True)

    # Получаем диспетчер для регистрации обработчиков
    dp = updater.dispatcher

    # Обработчик диалога
    convHandlerFindPhoneNumbers = ConversationHandler(
        entry_points=[CommandHandler('find_phone_number', findPhoneNumbersCommand)],
        states={
            'findPhoneNumbers': [MessageHandler(Filters.text & ~Filters.command, findPhoneNumbers)],
            'writePhoneNumbers': [MessageHandler(Filters.text & ~Filters.command, writePhoneNumbers)],
        },
        fallbacks=[]
    )
	
    convHandlerFindEmails = ConversationHandler(
        entry_points=[CommandHandler('find_email', findEmailsCommand)],
        states={
            'findEmails': [MessageHandler(Filters.text & ~Filters.command, findEmails)],
            'writeEmails': [MessageHandler(Filters.text & ~Filters.command, writeEmails)],
        },
        fallbacks=[]
    )

    convHandlerVerifyPassword = ConversationHandler(
        entry_points=[CommandHandler('verify_password', verifyPasswordCommand)],
        states={
            'verifyPassword': [MessageHandler(Filters.text & ~Filters.command, verifyPassword)],
        },
        fallbacks=[]
    )

    convHandlerAptList = ConversationHandler(
        entry_points=[CommandHandler('get_apt_list', aptListCommand)],
        states={
            'aptList': [MessageHandler(Filters.text & ~Filters.command, aptList)],
        },
        fallbacks=[]
    )
    
	# Регистрируем обработчики команд
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", helpCommand))
    dp.add_handler(CommandHandler("get_release", releaseCommand))
    dp.add_handler(CommandHandler("get_uname", unameCommand))
    dp.add_handler(CommandHandler("get_uptime", uptimeCommand))
    dp.add_handler(CommandHandler("get_df", dfCommand))
    dp.add_handler(CommandHandler("get_free", freeCommand))
    dp.add_handler(CommandHandler("get_mpstat", mpstatCommand))
    dp.add_handler(CommandHandler("get_w", wCommand))
    dp.add_handler(CommandHandler("get_auths", authsCommand))
    dp.add_handler(CommandHandler("get_critical", criticalCommand))
    dp.add_handler(CommandHandler("get_ps", psCommand))
    dp.add_handler(CommandHandler("get_ss", ssCommand))
    dp.add_handler(CommandHandler("get_services", servicesCommand))
    dp.add_handler(CommandHandler("get_emails", getEmailsCommand))
    dp.add_handler(CommandHandler("get_phone_numbers", getNumbersCommand))
    dp.add_handler(CommandHandler("get_repl_logs", ReplLogsCommand))
    dp.add_handler(convHandlerFindPhoneNumbers)
    dp.add_handler(convHandlerFindEmails)
    dp.add_handler(convHandlerVerifyPassword)
    dp.add_handler(convHandlerAptList)

	# Запускаем бота
    updater.start_polling()

	# Останавливаем бота при нажатии Ctrl+C
    updater.idle()


if __name__ == '__main__':
    main()
