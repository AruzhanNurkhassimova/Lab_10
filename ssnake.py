import pygame
import sys
import random
import time
import psycopg2

# Настройки окна
width, height = 600, 600
cell_size = 20

# Цвета
black = (0, 0, 0)
green = (0, 255, 0)
red = (255, 0, 0)
white = (255, 255, 255)
yellow = (255, 255, 0)
blue = (0, 0, 255)
gray = (200, 200, 200)

# Инициализация
pygame.init()
win = pygame.display.set_mode((width, height))
pygame.display.set_caption("Snake Game")
font = pygame.font.SysFont(None, 36)
clock = pygame.time.Clock()

# Создание таблицы
def create_tables():
    conn = psycopg2.connect(host="localhost", user="postgres", password="Malkuth/Yesod", port=5432)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(255) UNIQUE NOT NULL
        );
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS user_scores (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id),
            score INTEGER NOT NULL,
            level INTEGER NOT NULL,
            saved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    conn.commit()
    cur.close()
    conn.close()

def get_or_create_user(username):
    conn = psycopg2.connect(host="localhost", user="postgres", password="Malkuth/Yesod", port=5432)
    cur = conn.cursor()
    cur.execute("SELECT id FROM users WHERE username = %s", (username,))
    user = cur.fetchone()
    if user:
        user_id = user[0]
    else:
        cur.execute("INSERT INTO users (username) VALUES (%s) RETURNING id", (username,))
        user_id = cur.fetchone()[0]
        conn.commit()
    cur.close()
    conn.close()
    return user_id

def get_user_level(user_id):
    conn = psycopg2.connect(host="localhost", user="postgres", password="Malkuth/Yesod", port=5432)
    cur = conn.cursor()
    cur.execute("SELECT MAX(level) FROM user_scores WHERE user_id = %s", (user_id,))
    result = cur.fetchone()
    cur.close()
    conn.close()
    return result[0] if result[0] else 1

def get_user_high_score(user_id):
    conn = psycopg2.connect(host="localhost", user="postgres", password="Malkuth/Yesod", port=5432)
    cur = conn.cursor()
    cur.execute("SELECT MAX(score) FROM user_scores WHERE user_id = %s", (user_id,))
    result = cur.fetchone()
    cur.close()
    conn.close()
    return result[0] if result[0] else 0

def save_score(user_id, score, level):
    conn = psycopg2.connect(host="localhost", user="postgres", password="Malkuth/Yesod", port=5432)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO user_scores (user_id, score, level) VALUES (%s, %s, %s)",
        (user_id, score, level)
    )
    conn.commit()
    cur.close()
    conn.close()

# Функция для генерации еды
# Возвращает позицию, вес и таймер (время исчезновения)
def place_food(snake):
    while True:
        x = random.randint(1, (width - cell_size*2) // cell_size) * cell_size
        y = random.randint(1, (height - cell_size*2) // cell_size) * cell_size
        if (x, y) not in snake:
            weight = random.choice([1, 2, 3])
            timer = pygame.time.get_ticks() + 5000
            return (x, y), weight, timer

# Сброс игры
def reset_game():
    snake = [(100, 100)]
    dx, dy = cell_size, 0
    food, food_weight, food_timer = place_food(snake)
    speed = 10
    score = 0
    level = 1
    return snake, dx, dy, food, food_weight, food_timer, speed, score, level

# Когда запускается
create_tables()
username = input("Введите ваше имя: ")
user_id = get_or_create_user(username)
high_score = get_user_high_score(user_id)
print(f"Добро пожаловать, {username}. Ваш рекорд: {high_score}")

# Состояние игры
snake, dx, dy, food, food_weight, food_timer, speed, score, level = reset_game()
running = True
pause = False

while running:
    clock.tick(speed)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_p:
                pause = not pause
                if pause:
                    save_score(user_id, score, level)
                    print("Игра на паузе. Сохранено.")

    if pause:
        continue
    
    # Управление
    keys = pygame.key.get_pressed()
    if keys[pygame.K_UP] and dy == 0:
        dx, dy = 0, -cell_size
    if keys[pygame.K_DOWN] and dy == 0:
        dx, dy = 0, cell_size
    if keys[pygame.K_LEFT] and dx == 0:
        dx, dy = -cell_size, 0
    if keys[pygame.K_RIGHT] and dx == 0:
        dx, dy = cell_size, 0

    # Передвижение змейки
    head = (snake[0][0] + dx, snake[0][1] + dy)

    # Проверка на столкновение со стеной и самопересечение
    if (head[0] < cell_size or head[0] >= width - cell_size or
        head[1] < cell_size or head[1] >= height - cell_size or
        head in snake):
        win.fill(black)
        game_over_text = font.render("Game Over", True, red)
        win.blit(game_over_text, (width//2 - game_over_text.get_width()//2, height//2))
        pygame.display.update()
        time.sleep(3)
        snake, dx, dy, food, food_weight, food_timer, speed, score, level = reset_game()
        continue

    snake.insert(0, head)
    if head == food:
        score += food_weight
        if score // 4 + 1 > level: 
            level += 1
            speed += 2
        food, food_weight, food_timer = place_food(snake)
    else:
        snake.pop()

    # Проверка таймера еды
    if pygame.time.get_ticks() > food_timer:
        food, food_weight, food_timer = place_food(snake)

    # Отрисовка экрана
    win.fill(black)
    pygame.draw.rect(win, gray, (0, 0, width, height), cell_size)
    for segment in snake:
        pygame.draw.rect(win, green, (*segment, cell_size, cell_size))
    color = red if food_weight == 1 else yellow if food_weight == 2 else blue
    pygame.draw.rect(win, color, (*food, cell_size, cell_size))

    # Отображение очков и уровня
    score_text = font.render(f"Score: {score}  Level: {level}  High Score: {high_score}", True, white)
    win.blit(score_text, (30, 30))

    pygame.display.update()

pygame.quit()
print(f"{username}, ваш лучший результат: {max(high_score, score)}")
