import pygame
import random
import logging

# Настройка логирования
logging.basicConfig(
    filename='lab_4/game_log.txt',  
    level=logging.DEBUG,       
    format='%(asctime)s - %(levelname)s - %(message)s'
)

SCREEN = WIDTH, HEIGHT = 288, 512
display_height = 0.80 * HEIGHT

pygame.mixer.init()
wing_fx = pygame.mixer.Sound('lab_4/Sounds/wing.wav')

class Grumpy:
    """
    Класс, представляющий персонажа 'Grumpy' в игре.
    """

    def __init__(self, win):
        """
        Инициализация объекта Grumpy.

        Параметры:
            win (pygame.Surface): Поверхность, на которую будет рисоваться Grumpy.

        Загружает изображения для анимации и вызывает метод reset().
        """
        self.win = win
        self.im_list = []
        bird_color = random.choice(['red', 'blue', 'yellow'])
        for i in range(1, 4):
            try:
                img = pygame.image.load(f'lab_4/Assets/Grumpy/{bird_color}{i}.png')
                self.im_list.append(img)
            except pygame.error as e:
                logging.error("Image upload error: %s", e)

        self.reset()
        logging.info("Grumpy initialized with color: %s", bird_color)

    def update(self):
        """
        Обновляет состояние Grumpy.

        Увеличивает скорость падения, обрабатывает ввод мыши для прыжков,
        обновляет изображение и позицию Grumpy на экране.
        """
        self.vel += 0.3
        if self.vel >= 8:
            self.vel = 8
        if self.rect.bottom <= display_height:
            self.rect.y += int(self.vel)

        if self.alive:
            if pygame.mouse.get_pressed()[0] == 1 and not self.jumped:
                wing_fx.play()
                self.jumped = True
                self.vel = -6
            if pygame.mouse.get_pressed()[0] == 0:
                self.jumped = False
            self.flap_counter()
            self.image = pygame.transform.rotate(self.im_list[self.index], self.vel * -2)
        else:
            if self.rect.bottom <= display_height:
                self.theta -= 2
            self.image = pygame.transform.rotate(self.im_list[self.index], self.theta)

        self.win.blit(self.image, self.rect)

    def flap_counter(self):
        """
        Обновляет счетчик анимации и индекс текущего изображения.

        Увеличивает счетчик и переключает индекс изображения для анимации
        каждые 5 кадров. Сбрасывает индекс, если он превышает количество изображений.
        """
        self.counter += 1
        if self.counter > 5:
            self.counter = 0
            self.index += 1
        if self.index >= 3:
            self.index = 0

    def draw_flap(self):
        """
        Рисует анимацию хлопка крыльев.

        Управляет позицией и изображением Grumpy во время хлопка,
        изменяет позицию по оси Y для создания эффекта движения вверх и вниз.
        """
        self.flap_counter()
        if self.flap_pos <= -10 or self.flap_pos > 10:
            self.flap_inc *= -1
        self.flap_pos += self.flap_inc
        self.rect.y += self.flap_inc
        self.rect.x = WIDTH // 2 - 20
        self.image = self.im_list[self.index]
        self.win.blit(self.image, self.rect)

    def reset(self):
        """
        Сбрасывает состояние Grumpy к начальному.

        Устанавливает начальные значения атрибутов, таких как индекс изображения,
        позиция, скорость и флаги состояния.
        """
        self.index = 0
        self.image = self.im_list[self.index]
        self.rect = self.image.get_rect()
        self.rect.x = 60
        self.rect.y = int(display_height) // 2
        self.counter = 0
        self.vel = 0
        self.jumped = False
        self.alive = True
        self.theta = 0
        self.mid_pos = display_height // 2
        self.flap_pos = 0
        self.flap_inc = 1
        logging.info("Grumpy has been reset")

class Base:
    """
    Класс, представляющий базу в игре.
    """
    def __init__(self, win):
        """
        Инициализация объекта Base.

        Параметры:
            win (pygame.Surface): Поверхность, на которую будет рисоваться база.
        """  
        self.win = win
        try:
            self.image1 = pygame.image.load('lab_4/Assets/base.png')
            self.image2 = self.image1
            self.rect1 = self.image1.get_rect()
            self.rect1.x = 0
            self.rect1.y = int(display_height)
            self.rect2 = self.image2.get_rect()
            self.rect2.x = WIDTH
            self.rect2.y = int(display_height)
        except pygame.error as e:
            logging.error("Error loading the database image: %s", e)

    def update(self, speed):
        """
        Обновляет положение базы на экране.

        Параметры:
            speed (int): Скорость перемещения базы. Чем больше значение,
                         тем быстрее база будет двигаться влево.
        """
        self.rect1.x -= speed
        self.rect2.x -= speed

        if self.rect1.right <= 0:
            logging.info("Base rect1 repositioned")
            self.rect1.x = WIDTH - 5
        if self.rect2.right <= 0:
            logging.info("Base rect2 repositioned")
            self.rect2.x = WIDTH - 5

        self.win.blit(self.image1, self.rect1)
        self.win.blit(self.image2, self.rect2)

class Pipe(pygame.sprite.Sprite):
    """
    Класс, представляющий трубу в игре.
    """
    def __init__(self, win, image, y, position):
        """
        Инициализация объекта Pipe.

        Параметры:
            win (pygame.Surface): Поверхность, на которую будет рисоваться труба.
            image (pygame.Surface): Изображение трубы.
            y (int): Координата y для размещения трубы.
            position (int): Позиция трубы: 1 для верхней трубы и -1 для нижней.
        """
        super(Pipe, self).__init__()
        
        try:
            self.win = win
            self.image = image
            self.rect = self.image.get_rect()
            pipe_gap = 100 // 2
            x = WIDTH

            if position == 1:
                self.image = pygame.transform.flip(self.image, False, True)
                self.rect.bottomleft = (x, y - pipe_gap)
                logging.info("Top pipe created at y: %d", y)
            elif position == -1:
                self.rect.topleft = (x, y + pipe_gap)
                logging.info("Bottom pipe created at y: %d", y)
        except Exception as e:
            logging.error("Error when creating a pipe: %s", e)

    def update(self, speed):
        """
        Обновляет положение трубы на экране.

        Параметры:
            speed (int): Скорость перемещения трубы. Чем больше значение,
                         тем быстрее труба будет двигаться влево.
        """
        self.rect.x -= speed
        if self.rect.right < 0:
            logging.info("The pipe has been removed from the game.")
            self.kill()
        self.win.blit(self.image,  self.rect)

class Score:
    """
    Класс для отображения счета в игре.
    """
    def __init__(self, x, y, win):
        """
        Инициализация объекта Score.

        Параметры:
            x (int): Координата x для размещения счета.
            y (int): Координата y для размещения счета.
            win (pygame.Surface): Поверхность, на которую будет рисоваться счет.
        """
        try:
            self.score_list = []
            for score in range(10):
                img = pygame.image.load(f'lab_4/Assets/Score/{score}.png')
                self.score_list.append(img)
                self.x = x
                self.y = y

            self.win = win
        except pygame.error as e:
            logging.error("Error loading the invoice image: %s", e)

    def update(self, score):
        """
        Обновляет отображение счета на экране.

        Параметры:
            score (int): Текущий счет, который нужно отобразить.
        """
        score_str = str(score)
        for index, num in enumerate(score_str):
            try:
                self.image = self.score_list[int(num)]
                self.rect = self.image.get_rect()
                self.rect.topleft = (self.x - 15 * len(score_str) + 30 * index, self.y)
                self.win.blit(self.image, self.rect)
            except IndexError as e:
                logging.error("Account indexing error: %s", e)


if __name__ == "__main__":
    pygame.init()
    win = pygame.display.set_mode(SCREEN)
    grumpy = Grumpy(win)
    base = Base(win)
    pipes_group = pygame.sprite.Group()
    
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        
        grumpy.update()
        base.update(5) 
        
        pygame.display.update()

    pygame.quit()
