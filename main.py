import os
import random
import telebot
from telebot import types

# ទាញយក Token ពី Environment Variable
BOT_TOKEN = os.environ.get('BOT_TOKEN')
bot = telebot.TeleBot(BOT_TOKEN)

# រចនាសម្ព័ន្ធផ្លែប៉ោមស្អុយតាមជួរ (Row 1-3: 1, Row 4-6: 2, Row 7-9: 3, Row 10: 4)
ROTTEN_COUNT = {
    1: 1, 2: 1, 3: 1,
    4: 2, 5: 2, 6: 2,
    7: 3, 8: 3, 9: 3,
    10: 4
}

user_games = {}

def generate_row_apples(row_num):
    rotten_num = ROTTEN_COUNT[row_num]
    apples = ['🍎'] * (5 - rotten_num) + ['🍏'] * rotten_num
    random.shuffle(apples)
    return apples

@bot.message_handler(commands=['start', 'game'])
def start_game(message):
    user_id = message.from_user.id
    user_games[user_id] = {
        'current_row': 1,
        'grid': [generate_row_apples(r) for r in range(1, 11)],
        'status': 'playing'
    }
    send_board(message.chat.id, user_id)

def send_board(chat_id, user_id):
    game = user_games.get(user_id)
    if not game:
        return

    markup = types.InlineKeyboardMarkup(row_width=5)
    current_row = game['current_row']

    # បង្កើត Grid 10x5 (បង្ហាញពីជួរទី ១០ ចុះមកជួរទី ១)
    for r in range(10, 0, -1):
        row_buttons = []
        for c in range(5):
            if r == current_row and game['status'] == 'playing':
                btn = types.InlineKeyboardButton("🍏", callback_data=f"select_{r}_{c}")
            elif r < current_row or game['status'] != 'playing':
                apple_type = game['grid'][r-1][c]
                btn = types.InlineKeyboardButton(apple_type, callback_data="none")
            else:
                btn = types.InlineKeyboardButton("❓", callback_data="none")
            row_buttons.append(btn)
        markup.add(*row_buttons)

    if game['status'] == 'playing':
        text = f"🎮 **Apple of Fortune**\n\nជួរទី៖ {current_row}/10\nជ្រើសរើសផ្លែប៉ោមមួយក្នុងជួរភ្លឺ!"
    elif game['status'] == 'won':
        text = "🎉 **អបអរសាទរ! អ្នកបានឈ្នះដល់ជួរទី ១០ ហើយ!** 🎉"
    else:
        text = "💥 **ស៊យហើយ! អ្នកជ្រើសរើសចំផ្លែប៉ោមស្អុយ! Game Over** 💥"
        markup.add(types.InlineKeyboardButton("🔄 លេងម្ដងទៀត", callback_data="restart"))

    bot.send_message(chat_id, text, parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def handle_click(call):
    user_id = call.from_user.id
    game = user_games.get(user_id)

    if call.data == "restart":
        start_game(call.message)
        return

    if not game or game['status'] != 'playing':
        bot.answer_callback_query(call.id, "សូមចាប់ផ្តើមហ្គេមថ្មីដោយវាយ /start")
        return

    if call.data.startswith("select_"):
        _, row_str, col_str = call.data.split("_")
        row, col = int(row_str), int(col_str)

        if row != game['current_row']:
            bot.answer_callback_query(call.id, "សូមជ្រើសរើសតែជួរដែលកំពុងលេង!")
            return

        selected = game['grid'][row-1][col]

        if selected == '🍏': # ប៉ោមស្អុយ
            game['status'] = 'lost'
            bot.answer_callback_query(call.id, "💥 ចំប៉ោមស្អុយហើយ!")
        else: # ប៉ោមល្អ
            if game['current_row'] == 10:
                game['status'] = 'won'
                bot.answer_callback_query(call.id, "🎉 ឈ្នះហ្គេម!")
            else:
                game['current_row'] += 1
                bot.answer_callback_query(call.id, "✨ ឡើងទៅជួរមួយទៀត!")

        send_board(call.message.chat.id, user_id)

# ដំណើរការ Bot ២៤ម៉ោង និងការពារ Anti-Crash
if __name__ == '__main__':
    print("Bot is starting...")
    while True:
        try:
            bot.infinity_polling(timeout=10, long_polling_timeout=5)
        except Exception as e:
            print(f"Error occurred: {e}")
