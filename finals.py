import pygame
from sys import exit
from grid2 import *
from unit_stats import *
import math

pygame.init()
x = 0
# constants for grid size and cell dimensions
grid_width = 23
grid_height = 18

cell_size = 45
cell_margin = 3
cell_total = cell_margin + cell_size
cell_offsetx = 22.5
cell_offsety = 45

cell_transparency = 100
GREY = (65, 65, 65)

# number of blue cells when a character is selected
DISTANCE_THRESHOLD = 5
detection_range = 5 * math.sqrt(2)

# screen settings
screen_width = (cell_size + cell_margin) * grid_width
screen_height = (cell_size + cell_margin) * grid_height

# setting up the screen
screen = pygame.display.set_mode((screen_width, screen_height))
screen_rect = screen.get_rect()
pygame.display.set_caption("Maliq and THE essentials")

# framerate cap
clock = pygame.time.Clock()
fps_max = 60

# background image/map
scale_factor = 3
map_surface = pygame.image.load('Assets/Map/FE7MAP.png')
map_surface = pygame.transform.scale_by(map_surface, scale_factor)

# game variables "flags"
player_select = False
player_action = False
enemy_select = False
enemy_action = False
action_early = False

turn_count = 1
player_counter = 0  # the max number of this will be len(player_list)
enemy_counter = 0  # the max number of this will be len(enemy_list)

# game state
game_active = False

# starting position of each character (corresponding to index)
player_pos = [(11, 13), (12, 13), (11, 14), (12, 14), (13, 14)]
enemy_pos = [(3, 7), (4, 7), (4, 4), (9, 2), (12, 0), (13, 5), (14, 5)]

# some index to correspond player.index to index of position
some_index = 0

# list of player and enemy names
player_alive = ['p1', 'p2', 'p3', 'p4', 'p5']
enemy_alive = ['e1', 'e2', 'e3', 'e4', 'e5', 'e6', 'e7']

player_names = []
enemy_names = []

# players that is selected list
player_move = []
# enemies that can be targeted
attack_target = []

# enemies that can move list
enemy_move = []

# mouse pos
first_mouse_pos = (0, 0)
stats_mouse_pos = (0, 0)

# cursor movement
cursor_move = True


class Player(pygame.sprite.Sprite):
    def __init__(self, name):
        super().__init__()
        self.name = name

        # loading player images
        p1_scale = 0.6
        p2_scale = 0.6

        p1 = pygame.image.load('Assets/Player/player1/player_walk_1.png')
        p1 = pygame.transform.scale_by(p1, p1_scale)

        p2 = pygame.image.load('Assets/Player/lady/lady1.png')
        p2 = pygame.transform.scale_by(p2, p2_scale)

        p3 = pygame.image.load('Assets/Player/player2/1 Pink_Monster/Pink_Monster.png')
        p4 = pygame.image.load('Assets/Player/player2/2 Owlet_Monster/Owlet_Monster.png')
        p5 = pygame.image.load('Assets/Player/player2/3 Dude_Monster/Dude_Monster.png')
        p3 = pygame.transform.scale2x(p3)
        p4 = pygame.transform.scale2x(p4)
        p5 = pygame.transform.scale2x(p5)

        # name list whose index matches image list and position list (outside the class)
        self.name_list = ['p1', 'p2', 'p3', 'p4', 'p5']
        self.image_list = [p1, p2, p3, p4, p5]
        self.index = self.name_list.index(name)

        # player stats
        self.hp = player_data[self.name]['health']
        self.atk = player_data[self.name]['atk']
        self.defense = player_data[self.name]['def']

        # player image and rect
        self.image = self.image_list[self.index]
        self.rect = self.image.get_rect()
        self.rect.midbottom = (cell_offsetx + player_pos[self.index][0] * cell_total,
                                 cell_offsety + player_pos[self.index][1] * cell_total)

        # counts the number of cells moved vertically and horizontally
        self.vert_count = 0
        self.hor_count = 0

        # check for early action
        self.action_early = False

        # check if can attack
        self.canATK = False

        # enemies that can be targeted
        self.attack_target = []

        # where players can attack enemy:
        self.w = False
        self.a = False
        self.s = False
        self.d = False

        # position on screen
        self.screen_side = None

        # space
        self.__space = []

        # final target coordinate
        self.final_coord = None

    def damaged(self, enemy_atk):
        self.hp = self.hp - (enemy_atk - self.defense // 2)
        pygame.mixer.Channel(2).play(hit)

    def get_coord(self):
        return self.rect.centerx//cell_total, self.rect.centery//cell_total

    def get_spaces(self):
        """Method to get the available spaces where this player can get attacked"""
        self.__space.append((self.get_coord()[0] + 1, self.get_coord()[1]))
        self.__space.append((self.get_coord()[0] - 1, self.get_coord()[1]))
        self.__space.append((self.get_coord()[0], self.get_coord()[1] + 1))
        self.__space.append((self.get_coord()[0], self.get_coord()[1] - 1))
        return self.__space

    def space_shortest_distance(self, selected, attacking_spots):
        """Method to get the shortest distance in the attacking spot"""
        integer_distance = 100
        if len(attacking_spots) > 0:
            for coord in attacking_spots:
                distance = math.sqrt((selected.rect.centerx//cell_total - coord[0])**2 +
                                     (selected.rect.centery//cell_total - coord[1])**2)
                if distance <= integer_distance:
                    integer_distance = distance
                    self.final_coord = coord
            return self.final_coord
        else:
            return None

    def get_which_side(self):
        if self.rect.x < screen_width // 2:
            self.screen_side = "Left"
        else:
            self.screen_side = "Right"

        return self.screen_side


class Enemy(pygame.sprite.Sprite):
    def __init__(self, name):
        super().__init__()
        self.name = name

        all_scale = 1.4

        # enemy images
        e1 = pygame.image.load('Assets/Enemy/round ghost/round ghost idle/sprite_0.png')
        e2 = pygame.image.load('Assets/Enemy/round ghost/round ghost idle/sprite_0.png')
        e3 = pygame.image.load('Assets/Enemy/round ghost/round ghost idle/sprite_0.png')
        e4 = pygame.image.load('Assets/Enemy/round ghost/round ghost idle/sprite_0.png')
        e5 = pygame.image.load('Assets/Enemy/round ghost/round ghost idle/sprite_0.png')
        e6 = pygame.image.load('Assets/Enemy/round ghost/round ghost idle/sprite_0.png')
        e7 = pygame.image.load('Assets/Enemy/round ghost/round ghost idle/sprite_0.png')

        e1 = pygame.transform.scale_by(e1, all_scale)
        e2 = pygame.transform.scale_by(e2, all_scale)
        e3 = pygame.transform.scale_by(e3, all_scale)
        e4 = pygame.transform.scale_by(e4, all_scale)
        e5 = pygame.transform.scale_by(e5, all_scale)
        e6 = pygame.transform.scale_by(e6, all_scale)
        e7 = pygame.transform.scale_by(e7, all_scale)

        # name list whose index matches image list and position list (outside the class)
        self.name_list = ['e1', 'e2', 'e3', 'e4', 'e5', 'e6', 'e7']
        self.image_list = [e1, e2, e3, e4, e5, e6, e7]
        self.index = self.name_list.index(name)

        # image surface of self.image is taken from image_list; if name parameter is 'e1', self.image = e1
        self.image = self.image_list[self.index]
        self.rect = self.image.get_rect()
        self.rect.midbottom = (cell_offsetx + enemy_pos[self.index][0] * cell_total,
                               cell_offsety + enemy_pos[self.index][1] * cell_total)

        # player stats
        self.hp = enemy_data[self.name]['health']
        self.atk = enemy_data[self.name]['atk']
        self.defense = enemy_data[self.name]['def']

        # counts the number of cells moved vertically and horizontally
        self.vert_count = 0
        self.hor_count = 0

        # check if able to move or not
        self.move = False

        # check if collide with player to attack
        self.action_early = False

        # distance list
        self.final_distance = []

        # players that can be targetted list
        self.attack_target = []

        # players that can be targetted AND within attacking range
        self.final_attack_target = []

        # position on screen:
        self.screen_side = None

        # which axis moving in
        self.horizontal = True
        self.vertical = True

        # where players can attack enemy:
        self.w = False
        self.a = False
        self.s = False
        self.d = False

    def get_which_side(self):
        if self.rect.x < screen_width // 2:
            self.screen_side = "Left"
        else:
            self.screen_side = "Right"

    # relating to player targetting
    def append_target_list(self, player):
        if player not in self.attack_target:
            self.attack_target.append(player)

    def get_target_list(self):
        return self.attack_target

    def clear_target_list(self):
        self.attack_target.clear()

    def clear_final_target_list(self):
        self.final_attack_target.clear()

    def clear_distance_list(self):
        self.final_distance.clear()

    def get_nearest_player(self):
        if len(self.attack_target) > 0:
            for target in self.attack_target:
                distance = math.sqrt((self.rect.centerx//cell_total - target.rect.centerx//cell_total)**2 +
                                     (self.rect.centery//cell_total - target.rect.centery//cell_total)**2)

                if distance <= detection_range:
                    self.final_distance.append(distance)
                    self.final_attack_target.append(target)

            if len(self.final_distance) > 0:
                least_distance = min(self.final_distance)
                player_target = self.final_attack_target[self.final_distance.index(least_distance)]

                return player_target

            else:
                return None

    """Collisions Functions"""
    def check_player_collision(self, target, direction):
        # takes the current position in self.get_coord() and sees if one row/col ahead/behind contains the coordinates
        # of an existing player; if yes return False, else return True
        if direction == 'down':
            for player in players:
                coord = player.get_coord()
                if coord[1] == self.get_coord()[1] + 1 and coord[0] == self.get_coord()[0]:
                    return False
                else:
                    return True
        elif direction == 'up':
            for player in players:
                coord = player.get_coord()
                if coord[1] == self.get_coord()[1] - 1 and coord[0] == self.get_coord()[0]:
                    return False
                else:
                    return True
        elif direction == 'left':
            for player in players:
                coord = player.get_coord()
                if coord[1] == self.get_coord()[1] and coord[0] == self.get_coord()[0] - 1:
                    return False
                else:
                    return True
        elif direction == 'right':
            for player in players:
                coord = player.get_coord()
                if coord[1] == self.get_coord()[1] and coord[0] == self.get_coord()[0] + 1:
                    return False
                else:
                    return True

    def check_enemy_collision(self, target, direction):
        if direction == 'down':
            for enemy in enemies:
                coord = enemy.get_coord()
                if coord[1] == self.get_coord()[1] + 1 and coord[0] == self.get_coord()[0]:
                    return False
                else:
                    return True
        elif direction == 'up':
            for enemy in enemies:
                coord = enemy.get_coord()
                if coord[1] == self.get_coord()[1] - 1 and coord[0] == self.get_coord()[0]:
                    return False
                else:
                    return True
        elif direction == 'left':
            for enemy in enemies:
                coord = enemy.get_coord()
                if coord[1] == self.get_coord()[1] and coord[0] == self.get_coord()[0] - 1:
                    return False
                else:
                    return True
        elif direction == 'right':
            for enemy in enemies:
                coord = enemy.get_coord()
                if coord[1] == self.get_coord()[1] and coord[0] == self.get_coord()[0] + 1:
                    return False
                else:
                    return True

    # references the env_matrix whose value of [row][col] equals the coordinates of the grid (x, y)
    def check_wall_collision(self, direction):
        if direction == 'down':
            if env_matrix[self.get_coord()[1] + 1][self.get_coord()[0]] == 0:
                return False
            else:
                return True
        elif direction == 'up':
            if env_matrix[self.get_coord()[1] - 1][self.get_coord()[0]] == 0:
                return False
            else:
                return True
        elif direction == 'left':
            if env_matrix[self.get_coord()[1]][self.get_coord()[0] - 1] == 0:
                return False
            else:
                return True
        elif direction == 'right':
            if env_matrix[self.get_coord()[1]][self.get_coord()[0] + 1] == 0:
                return False
            else:
                return True

    def clear_all_list(self):
        self.clear_target_list()
        self.clear_final_target_list()
        self.clear_distance_list()

    def attacked(self, player_atk):
        self.hp = self.hp - (player_atk - self.defense//2)
        pygame.mixer.Channel(2).play(hit)

    def get_coord(self):
        return self.rect.center[0]//cell_total, self.rect.center[1]//cell_total

    def update(self):
        self.move = False


class ActionMenu:
    """The class for the menu, contains all its properties"""
    def __init__(self):
        # Box Properties
        posx = 1 * cell_total
        posy = 13 * cell_total
        size = 4 * cell_total
        self.box_color = (0, 0, 0)
        self.outline_color = (255, 255, 255)
        self.outline_width = 3
        self.box_rect = pygame.rect.Rect(posx, posy, size, size)

        # Box Options Properties
        font_size = 50
        font_color_active = (220,220,220)  # if option is available
        font_color_inactive = (128,128,128)  # if option (attack) is unavailable
        option_pos1 = (2*cell_total, 14*cell_total)
        option_pos2 = (2*cell_total, 15*cell_total)
        option_pos3 = (2*cell_total, 16*cell_total)

        self.text_font = pygame.font.Font('Assets/font/Pixeltype.ttf', font_size)

        self.text_attack_surf1 = self.text_font.render('Attack', False, font_color_active)
        self.text_attack_surf2 = self.text_font.render('Attack', False, font_color_inactive)

        self.text_end_surf = self.text_font.render('End', False, font_color_active)
        self.text_cancel_surf = self.text_font.render('Cancel', False, font_color_active)

        self.text_attack_rect1 = self.text_attack_surf1.get_rect(midleft=option_pos1)
        self.text_attack_rect2 = self.text_attack_surf2.get_rect(midleft=option_pos1)
        self.text_end_rect = self.text_end_surf.get_rect(midleft=option_pos2)
        self.text_cancel_rect = self.text_cancel_surf.get_rect(midleft=option_pos3)

        # Triangle/Pointer Property
        self.triangle_color = (255, 255, 255)
        self.triangle_pos = 0
        self.triangle_displacement = self.triangle_pos//1 * cell_total

        # coordinates for each vertex of triangle polygon
        self.triangle_coord1 = (1 * cell_total + cell_total//3,
                                self.text_attack_rect1.midleft[1] - cell_total//4 + self.triangle_displacement)
        self.triangle_coord2 = (self.triangle_coord1[0],
                                self.text_attack_rect1.midleft[1] + cell_total//4 + self.triangle_displacement)
        self.triangle_coord3 = (2 * cell_total - cell_total//4,
                                self.text_attack_rect1.midleft[1] + self.triangle_displacement)

        # bool check for which option is selected
        self.attack = False
        self.end = False
        self.cancel = False

        # bool check to see if atk option can be selected
        self.canATK = False

        # check for cursor movement
        self.cursor_move = True

    def draw(self, can_attack):
        # draw box and its outline
        pygame.draw.rect(screen, self.box_color, self.box_rect)
        pygame.draw.rect(screen, self.outline_color, self.box_rect, self.outline_width)

        # draw the options available in the box
        # if selected player can attack show this
        if can_attack:
            # where attack is not greyed out
            self.canATK = True
            screen.blit(self.text_attack_surf1, self.text_attack_rect1)
            screen.blit(self.text_end_surf, self.text_end_rect)
            screen.blit(self.text_cancel_surf, self.text_cancel_rect)
        else:
            # where attack is greyed out
            screen.blit(self.text_attack_surf2, self.text_attack_rect2)
            screen.blit(self.text_end_surf, self.text_end_rect)
            screen.blit(self.text_cancel_surf, self.text_cancel_rect)
            self.canATK = False

    def move_pointer(self):
        # draw the pointer
        rate_of_move = 0.175
        keys = pygame.key.get_pressed()
        if keys[pygame.K_s] and self.cursor_move:
            if self.triangle_pos < 2:
                self.triangle_pos += rate_of_move
                # // 1 is in order to make the pointer snap instead of a continuous movement
                self.triangle_displacement = self.triangle_pos//1 * cell_total
                self.triangle_coord1 = (1 * cell_total + cell_total // 3,
                                        self.text_attack_rect1.midleft[
                                            1] - cell_total // 4 + self.triangle_displacement)
                self.triangle_coord2 = (self.triangle_coord1[0],
                                        self.text_attack_rect1.midleft[
                                            1] + cell_total // 4 + self.triangle_displacement)
                self.triangle_coord3 = (2 * cell_total - cell_total // 4,
                                        self.text_attack_rect1.midleft[1] + self.triangle_displacement)

        if keys[pygame.K_w] and self.cursor_move:
            # max = 3 because the rate of move is 0.2, it is continuously increasing so the actual value of
            # triangle pos is greater than 2 even though the upper limit is 2 (in K_s). The lower limit is 0.2
            # because of the same reason; the actual value might be something like 0.05, and lowering that will
            # cause triangle_pos to be a negative number
            if 3 > self.triangle_pos > 0.175:
                self.triangle_pos -= rate_of_move
                # // 1 is in order to make the pointer snap instead of a continuous movement
                self.triangle_displacement = self.triangle_pos//1 * cell_total
                self.triangle_coord1 = (1 * cell_total + cell_total // 3,
                                        self.text_attack_rect1.midleft[
                                            1] - cell_total // 4 + self.triangle_displacement)
                self.triangle_coord2 = (self.triangle_coord1[0],
                                        self.text_attack_rect1.midleft[
                                            1] + cell_total // 4 + self.triangle_displacement)
                self.triangle_coord3 = (2 * cell_total - cell_total // 4,
                                        self.text_attack_rect1.midleft[1] + self.triangle_displacement)

        pygame.draw.polygon(screen, self.triangle_color, [self.triangle_coord1, self.triangle_coord2
                                                          , self.triangle_coord3])

    def check_option(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_e]:
            # the distance between each option in the aciton menu is 1 cell_total
            # if statements will see the distance travelled by the 'pointer' to see which option it's on
            if self.triangle_displacement == 0 * cell_total and self.canATK:
                self.attack = True
                self.cursor_move = False
            elif self.triangle_displacement == 1 * cell_total:
                self.end = True
                self.cursor_move = False
            elif self.triangle_displacement == 2 * cell_total:
                self.cancel = True
                self.cursor_move = False

    def reset_option(self):
        self.attack = False
        self.end = False
        self.cancel = False
        self.cursor_move = True

    def update(self, can_attack):
        self.draw(can_attack)
        self.move_pointer()


# function to construct grid
def construct_grid():
    """Function to create grid; blits cell if env_matrix[x][y] == 1, else: no blit"""
    # iterating through each row
    for y in range(grid_height):
        # iterating through each col
        for x in range(grid_width):
            # checks if specific element in env_matrix is 1; if yes: the cells are blit
            if env_matrix[y][x] == 1:
                # establishing cell surface and rect
                cell_pos = (x * cell_total, y * cell_total)
                cell_surface = pygame.Surface((cell_size, cell_size))
                cell_surface.fill(GREY)
                cell_surface.set_alpha(cell_transparency)
                cell_rect = cell_surface.get_rect()
                cell_rect.topleft = cell_pos

                # blitting the cells
                screen.blit(cell_surface, cell_rect)


# function to check for wall so player doesn't walk through
def check_wall(player_rect, direction):
    """Checks for collision with wall by referencing the env_matrix and grid_matrix. The function accepts parameters
    'player.rect' and 'direction of movement' (key press in form of string). First, function will iterate through
    each row of the grid_matrix and also iterate through each element in a row; each element is a tuple
    representing coordinates of the grid.

     {Each 0 and 1s in the env_matrix corresponds to a coordinate in the grid_matrix of the SAME position}

     Then, there is an if statement to check if the player_coord (the position of the player character in terms
     of grid coordinates) is equal to some element (tuple of coordinate) in some row.
     Within the if statement, the index of the coordinate is stored in variables some_col (for the element in row)
      and some_row (for the row in the matrix).

      Next, are a sequence of if statements. Depending on the direction parameter, if w: checks to see if 1 row in front
       of player_coord is traversable. If traversable, returns True; else, returns False"""
    # player position in grid formula
    global some_row, some_col

    player_coord = (player_rect.centerx// cell_total,
                  player_rect.centery // cell_total)

    # iterates through rows of grid_matrix
    for row in grid_matrix:
        for col in row:
            if player_coord == col:
                # since grid_matrix corresponds to env_matrix, this matches the corresponding indexes
                some_row = grid_matrix.index(row)
                some_col = row.index(col)

    # for the corresponding index of the player_coord in grid_matrix, checks for collision (0/1) in env_matrix
    if direction == 'w':
        if env_matrix[some_row - 1][some_col] == 1:
            return True
        else:
            return False

    elif direction == 's':
        if env_matrix[some_row + 1][some_col] == 1:
            return True
        else:
            return False

    elif direction == 'd':
        if env_matrix[some_row][some_col + 1] == 1:
            return True
        else:
            return False

    elif direction == 'a':
        if env_matrix[some_row][some_col - 1] == 1:
            return True
        else:
            return False


# checking for player to player collision
def check_player_collision(player, event_key):
    """Checks for collision between selected player and every other player"""
    # iterates through each unit in players sprite group and checks for collision with the selected player
    for unit in players:
        if player != unit:
            # if/elif statement for event key to check for which side of the unit is collided with selected player
            if event_key == pygame.K_w:
                # rect of selected player moves in opposite direction, and vert/hor count reverses
                if player.rect.collidepoint(unit.rect.center):
                    player.rect.y += cell_total
                    player.vert_count -= 1
            elif event_key == pygame.K_s:
                if player.rect.collidepoint(unit.rect.center):
                    player.rect.y -= cell_total
                    player.vert_count += 1
            elif event_key == pygame.K_a:
                if player.rect.collidepoint(unit.rect.center):
                    player.rect.x += cell_total
                    player.hor_count -= 1
            elif event_key == pygame.K_d:
                if player.rect.collidepoint(unit.rect.center):
                    player.rect.x -= cell_total
                    player.hor_count += 1


# check if player can attack
def check_dumb_collision():
    """Checks for collision between any player and any enemy, if True player can attack (.canATK attribute is set
    to True)"""
    for player in players:
        for enemy in enemies:
            # checking if collision in within one block of player, if True player is able to select attack option
            if player.rect.collidepoint(enemy.rect.midtop):
                player.canATK = True
                # appends the enemy object into a list in the player object so it can be attacked later on
            elif player.rect.collidepoint(enemy.rect.midleft):
                player.canATK = True
            elif player.rect.collidepoint(enemy.rect.midright):
                player.canATK = True
            elif player.rect.collidepoint(enemy.rect.midbottom):
                player.canATK = True


def check_player_enemy_collision(player, event_key):
    """Checks collision between enemy and SELECTED player"""
    """This function accepts player object and event.key. enemies sprite group is iterated in a for loop, if there
    is collision with the player.rect and the enemy's center the rect of the player is pushed back the opposite
    direction by 1 cell_total. The direction is determined by event.key"""
    # iterates through each unit in players sprite group and checks for collision with the selected player
    for enemy in enemies:
        # if/elif statement for event key to check for which side of the unit is collided with selected player
        if event_key == pygame.K_w:
            # rect of selected player moves in opposite direction, and vert/hor count reverses
            if player.rect.collidepoint(enemy.rect.center):
                player.rect.y += cell_total
                player.vert_count -= 1
        elif event_key == pygame.K_s:
            if player.rect.collidepoint(enemy.rect.center):
                player.rect.y -= cell_total
                player.vert_count += 1
        elif event_key == pygame.K_a:
            if player.rect.collidepoint(enemy.rect.center):
                player.rect.x += cell_total
                player.hor_count -= 1
        elif event_key == pygame.K_d:
            if player.rect.collidepoint(enemy.rect.center):
                player.rect.x -= cell_total
                player.hor_count += 1


def display_stats(event_pos):
    """This function accepts mouse position and blits the stats of the units when
    mouse pos and player/unit rect collides"""
    # text font
    font_size = 30
    player_text_color = (80, 200, 120)
    enemy_text_color = (255, 0, 0)
    bg_color = (0, 0, 0)
    text_font = pygame.font.Font('Assets/font/Pixeltype.ttf', font_size)

    # getting coordinates of the cell
    event_coord = (event_pos[0]//cell_total, event_pos[1]//cell_total)


    for player in players:
        # check for mouse collision
        if player.rect.collidepoint(event_pos):

            # for players: text surface, rect
            player_stats = text_font.render(f'Name: {player.name} | HP: {player.hp} | '
                                             f'ATK: {player.atk} | DEF: {player.defense}',
                                             False, player_text_color, bg_color)
            player_stats_rect = player_stats.get_rect()
            player_stats_rect.midbottom = player.rect.midtop

            screen.blit(player_stats, player_stats_rect)

    for enemy in enemies:
        if enemy.rect.collidepoint(event_pos):
        # if enemy_pos.index(event_coord) == enemy.index:
            # for enemies: text surface, rect
            enemy_stats = text_font.render(f'Name: {enemy.name} | HP: {enemy.hp} | '
                                             f'ATK: {enemy.atk} | DEF: {enemy.defense}',
                                             False, enemy_text_color, bg_color)
            enemy_stats_rect = enemy_stats.get_rect()
            enemy_stats_rect.midbottom = enemy.rect.midtop

            screen.blit(enemy_stats, enemy_stats_rect)

            # since stats are usually blit on top of player/enemy, this is an alternative way to blit stats (bottom)
            # checks if y coordinate is at 0
            if event_coord[1] == 0:
                enemy_stats_rect.midbottom = enemy.rect.midbottom
                screen.blit(enemy_stats, enemy_stats_rect)


def attack_instruction(player):
    font_size = 40
    text_font = pygame.font.Font('Assets/font/Pixeltype.ttf', font_size)
    text_color = (255, 255, 255)
    background_color = (0, 0, 0)

    for target in player.attack_target:
        # instruction for w key (enemy target above player)
        if target.rect.center[1] < player.rect.center[1]:
            text_w = text_font.render(' W ', False, text_color, background_color)
            w_rect = text_w.get_rect(midbottom=target.rect.midtop)
            screen.blit(text_w, w_rect)
        if target.rect.center[1] > player.rect.center[1]:
            text_s = text_font.render(' S ', False, text_color, background_color)
            s_rect = text_s.get_rect(midtop=target.rect.midbottom)
            screen.blit(text_s, s_rect)
        if target.rect.center[0] < player.rect.center[0]:
            text_a = text_font.render(' A ', False, text_color, background_color)
            a_rect = text_a.get_rect(midbottom=target.rect.midtop)
            screen.blit(text_a, a_rect)
        if target.rect.center[0] > player.rect.center[0]:
            text_d = text_font.render(' D ', False, text_color, background_color)
            d_rect = text_d.get_rect(midbottom=target.rect.midtop)
            screen.blit(text_d, d_rect)


def check_targetable_e():
    for player in players:
        for enemy in enemies:
            # checking if collision in within one block of player, if True player is able to select attack option
            if enemy not in player.attack_target:
                if player.rect.collidepoint(enemy.rect.midtop):
                    # appends the enemy object into a list in the player object so it can be attacked later on
                    player.attack_target.append(enemy)
                    enemy.s = True
                    player.s = True
                elif player.rect.collidepoint(enemy.rect.midleft):
                    player.attack_target.append(enemy)
                    enemy.d = True
                    player.d = True
                elif player.rect.collidepoint(enemy.rect.midright):
                    player.attack_target.append(enemy)
                    enemy.a = True
                    player.a = True
                elif player.rect.collidepoint(enemy.rect.midbottom):
                    player.attack_target.append(enemy)
                    enemy.w = True
                    player.w = True
            # else:
            #     if not player.rect.collidepoint(enemy.rect.midtop):
            #         # appends the enemy object into a list in the player object so it can be attacked later on
            #         # player.attack_target.remove(enemy)
            #         enemy.s = False
            #         player.s = False
            #     elif not player.rect.collidepoint(enemy.rect.midleft):
            #         # player.attack_target.remove(enemy)
            #         enemy.d = False
            #         player.d = False
            #     elif not player.rect.collidepoint(enemy.rect.midright):
            #         # player.attack_target.remove(enemy)
            #         enemy.a = False
            #         player.a = False
            #     elif not player.rect.collidepoint(enemy.rect.midbottom):
            #         # player.attack_target.remove(enemy)
            #         enemy.w = False
            #         player.w = False


def check_lingering_collision():
    for player in players:
        for enemy in enemies:
            if enemy in player.attack_target:
                if not player.rect.collidepoint(enemy.rect.midtop):
                    player.attack_target.remove(enemy)
                elif not player.rect.collidepoint(enemy.rect.midleft):
                    player.attack_target.remove(enemy)
                elif not player.rect.collidepoint(enemy.rect.midright):
                    player.attack_target.remove(enemy)
                elif not player.rect.collidepoint(enemy.rect.midbottom):
                    player.attack_target.remove(enemy)


# function to attack the enemy after
def commit_attack(player, event_key):
    # to get key input
    for target in player.attack_target:
        if target.w and event_key == pygame.K_w:
            target.attacked(player.atk)
            target.w = False
        elif target.s and event_key == pygame.K_s:
            target.attacked(player.atk)
            target.s = False
        elif target.a and event_key == pygame.K_a:
            target.attacked(player.atk)
            target.a = False
        elif target.d and event_key == pygame.K_d:
            target.attacked(player.atk)
            target.d = False


# function to remove enemy once HP = 0
def kill_enemy():
    for enemy in enemies:
        if enemy.hp <= 0:
            enemy_pos.pop(enemy.index)
            for enemy2 in enemies:
                if enemy2 != enemy:
                    enemy2.name_list.remove(enemy.name)
                    enemy2.index = enemy2.name_list.index(enemy2.name)
                    enemy2.image_list.pop(enemy_alive.index(enemy.name))
            enemy_alive.remove(enemy.name)
            enemies.remove(enemy)

# function remove player once HP = 0

def kill_player():
    for player in players:
        if player.hp <= 0:
            player_pos.pop(player.index)
            for player2 in players:
                if player2 != player:
                    player2.name_list.remove(player.name)
                    player2.index = player2.name_list.index(player2.name)
                    player2.image_list.pop(player_alive.index(player.name))
            player_alive.remove(player.name)
            players.remove(player)


# player class instances
p1 = Player('p1')
p2 = Player('p2')
p3 = Player('p3')
p4 = Player('p4')
p5 = Player('p5')

# sprite group for players
players = pygame.sprite.Group()
players.add(p1)
players.add(p2)
players.add(p3)
players.add(p4)
players.add(p5)

# enemy class instances
e1 = Enemy('e1')
e2 = Enemy('e2')
e3 = Enemy('e3')
e4 = Enemy('e4')
e5 = Enemy('e5')
e6 = Enemy('e6')
e7 = Enemy('e7')

# sprite group for enemies
enemies = pygame.sprite.Group()
enemies.add(e1)
enemies.add(e2)
enemies.add(e3)
enemies.add(e4)
enemies.add(e5)
enemies.add(e6)
enemies.add(e7)

# action_menu instance
menu = ActionMenu()

time = pygame.time.get_ticks()

# audios
bg_alive = pygame.mixer.Sound('Assets/audio/02 Opening Title ~ Demo (no intro).wav')

bg_alive.set_volume(0.1)
song_length = 130000
play = True

move_tiles = pygame.mixer.Sound('Assets/audio/movingtiles.wav')

select_sound = pygame.mixer.Sound('Assets/audio/selectplayer.wav')

select_option = pygame.mixer.Sound('Assets/audio/selectingoptions.wav')

cancel = pygame.mixer.Sound('Assets/audio/cancel.wav')

hit = pygame.mixer.Sound('Assets/audio/Hit damage 1.wav')

# main game loop
while True:
    screen.blit(map_surface, screen_rect.topleft)
    if play:
        pygame.mixer.Channel(0).play(bg_alive, 10)
        play = False

    # to check if player can attack
    check_dumb_collision()

    # universal mouse pos, used for mouse hover to get unit stats
    stats_mouse_pos = pygame.mouse.get_pos()

    if player_select:
        construct_grid()

    # getting the mouse position in terms of grid coordinate
    if player_select is False:
        first_mouse_pos = (pygame.mouse.get_pos()[0] // cell_total,
                           pygame.mouse.get_pos()[1] // cell_total)

    # check for player actions
    if player_action is True:
        # draws Menu for player actions
        for player in players:
            # if statement to make sure the menu is unique for each player (some can attack some can't)
            if player in player_move:
                menu.update(player.canATK)
        # checks which option is selected
        menu.check_option()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            exit()

        # check if a player is selected
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and first_mouse_pos in player_pos\
                and player_alive[player_pos.index(first_mouse_pos)] not in player_names:
            player_select = True
            pygame.mixer.Channel(1).play(select_sound)

        # check for keydown events
        elif event.type == pygame.KEYDOWN:
            print(event.key)
            # iterates through each player sprite/instance in the players Group
            for player in players:
                print(player.name)
                print(f'This is {player.name} index: {player.index}')
                # names that are not in player_names will get their turn
                if player.name not in player_names and player_select and player not in player_move:
                    # moves the character up by 1 cell
                    if event.key == pygame.K_w:
                        # targeting the specific player by matching the index of the coordinate in player_pos
                        # and player.index since the index of a player corresponds to the index of their coordinate
                        if player.index == player_pos.index(first_mouse_pos) and check_wall(player.rect, 'w'):
                            pygame.mixer.Channel(1).play(move_tiles)
                            player.rect.y -= cell_total
                            player.vert_count += 1
                            check_player_collision(player, event.key)
                            check_player_enemy_collision(player, event.key)
                            check_lingering_collision()
                            player.attack_target.clear()
                            player.w = False
                            player.s = False
                            player.a = False
                            player.d = False
                            player.canATK = False

                    # moves the character down by 1 cell
                    elif event.key == pygame.K_s:
                        if player.index == player_pos.index(first_mouse_pos) and check_wall(player.rect, 's'):
                            pygame.mixer.Channel(1).play(move_tiles)
                            player.rect.y += cell_total
                            player.vert_count -= 1
                            check_player_collision(player, event.key)
                            check_player_enemy_collision(player, event.key)
                            check_lingering_collision()
                            player.attack_target.clear()
                            player.w = False
                            player.s = False
                            player.a = False
                            player.d = False
                            player.canATK = False

                    # moves the character right by 1 cell
                    elif event.key == pygame.K_d:
                        if player.index == player_pos.index(first_mouse_pos) and check_wall(player.rect, 'd'):
                            pygame.mixer.Channel(1).play(move_tiles)
                            player.rect.x += cell_total
                            player.hor_count -= 1
                            check_player_collision(player, event.key)
                            check_player_enemy_collision(player, event.key)
                            check_lingering_collision()
                            player.attack_target.clear()
                            player.w = False
                            player.s = False
                            player.a = False
                            player.d = False
                            player.canATK = False

                    # moves the character left by 1 cell
                    elif event.key == pygame.K_a:
                        if player.index == player_pos.index(first_mouse_pos) and check_wall(player.rect, 'a'):
                            pygame.mixer.Channel(1).play(move_tiles)
                            player.rect.x -= cell_total
                            player.hor_count += 1
                            check_player_collision(player, event.key)
                            check_player_enemy_collision(player, event.key)
                            check_lingering_collision()
                            player.attack_target.clear()
                            player.w = False
                            player.s = False
                            player.a = False
                            player.d = False
                            player.canATK = False

                    elif event.key == pygame.K_SPACE and player.action_early is False:
                        if player.index == player_pos.index(first_mouse_pos):
                            pygame.mixer.Channel(1).play(select_sound)
                            player.action_early = True
                            check_player_collision(player, event.key)
                            check_player_enemy_collision(player, event.key)
                            check_lingering_collision()
                            player.attack_target.clear()
                            player.w = False
                            player.s = False
                            player.a = False
                            player.d = False

                # This block limits player selection to one per turn and handles player actions
                # counts the number of cell distance travelled and will limit it to DISTANCE_THRESHOLD = 5
                if (abs(player.vert_count) + abs(player.hor_count)) == DISTANCE_THRESHOLD or player.action_early:
                    if len(player_move) < 1:
                        player_move.append(player)
                    # player action set to True so that menu can be blit
                    # player select set to False so that units cannot move
                    player_action = True
                    check_targetable_e()

                    # if press enter when cursor on 'Attack'
                    if player.canATK and menu.attack and event.key == pygame.K_w and player.w:
                        pygame.mixer.Channel(1).play(select_option)
                        commit_attack(player, event.key)
                        # updating player_pos list with current player position
                        player_pos[player.name_list.index(player.name)] = (player.rect.centerx // cell_total,
                                                                           player.rect.centery // cell_total)

                        # updating mouse_pos with current player position
                        first_mouse_pos = player_pos[player.name_list.index(player.name)]
                        player_names.append(player.name)
                        # reset the ver_count and hor_count of each player for their next turn
                        player.vert_count = 0
                        player.hor_count = 0
                        # check variables are set to False so new character can be selected and perform an action
                        player_action = False
                        player_select = False
                        player.action_early = False
                        player_move.clear()
                        menu.reset_option()
                        player.attack_target.clear()
                        player.w = False
                        player.s = False
                        player.a = False
                        player.d = False

                    elif player.canATK and menu.attack and event.key == pygame.K_s and player.s:
                        pygame.mixer.Channel(1).play(select_option)
                        commit_attack(player, event.key)
                        # updating player_pos list with current player position
                        player_pos[player.name_list.index(player.name)] = (player.rect.centerx // cell_total,
                                                                           player.rect.centery // cell_total)

                        # updating mouse_pos with current player position
                        first_mouse_pos = player_pos[player.name_list.index(player.name)]
                        player_names.append(player.name)
                        # reset the ver_count and hor_count of each player for their next turn
                        player.vert_count = 0
                        player.hor_count = 0
                        # check variables are set to False so new character can be selected and perform an action
                        player_action = False
                        player_select = False
                        player.action_early = False
                        player_move.clear()
                        menu.reset_option()
                        player.attack_target.clear()
                        player.w = False
                        player.s = False
                        player.a = False
                        player.d = False

                    elif player.canATK and menu.attack and event.key == pygame.K_a and player.a:
                        pygame.mixer.Channel(1).play(select_option)
                        commit_attack(player, event.key)
                        # updating player_pos list with current player position
                        player_pos[player.name_list.index(player.name)] = (player.rect.centerx // cell_total,
                                                                           player.rect.centery // cell_total)

                        # updating mouse_pos with current player position
                        first_mouse_pos = player_pos[player.name_list.index(player.name)]
                        player_names.append(player.name)
                        # reset the ver_count and hor_count of each player for their next turn
                        player.vert_count = 0
                        player.hor_count = 0
                        # check variables are set to False so new character can be selected and perform an action
                        player_action = False
                        player_select = False
                        player.action_early = False
                        player_move.clear()
                        menu.reset_option()
                        player.attack_target.clear()
                        player.w = False
                        player.s = False
                        player.a = False
                        player.d = False

                    elif player.canATK and menu.attack and event.key == pygame.K_d and player.d:
                        pygame.mixer.Channel(1).play(select_option)
                        commit_attack(player, event.key)
                        # updating player_pos list with current player position
                        player_pos[player.name_list.index(player.name)] = (player.rect.centerx // cell_total,
                                                                           player.rect.centery // cell_total)

                        # updating mouse_pos with current player position
                        first_mouse_pos = player_pos[player.name_list.index(player.name)]
                        player_names.append(player.name)
                        # reset the ver_count and hor_count of each player for their next turn
                        player.vert_count = 0
                        player.hor_count = 0
                        # check variables are set to False so new character can be selected and perform an action
                        player_action = False
                        player_select = False
                        player.action_early = False
                        player_move.clear()
                        menu.reset_option()
                        player.attack_target.clear()
                        player.w = False
                        player.s = False
                        player.a = False
                        player.d = False

                    # if press enter when cursor on 'End', ends unit's turn (unit cannot be selected until next turn)
                    if menu.end and event.key == pygame.K_e:
                        # updating player_pos list with current player position
                        pygame.mixer.Channel(1).play(select_sound)
                        player_pos[player.name_list.index(player.name)] = (player.rect.centerx // cell_total,
                                                                       player.rect.centery // cell_total)

                        # updating mouse_pos with current player position
                        first_mouse_pos = player_pos[player.name_list.index(player.name)]
                        player_names.append(player.name)

                        # reset the ver_count and hor_count of each player for their next turn
                        player.vert_count = 0
                        player.hor_count = 0

                        # check variables are set to False so new character can be selected and perform an action
                        player_action = False
                        player_select = False
                        player.action_early = False
                        player.canATK = False
                        player_move.clear()
                        player.attack_target.clear()
                        menu.reset_option()
                        player.w = False
                        player.s = False
                        player.a = False
                        player.d = False

                    # if press enter when cursor on 'Cancel', returns unit to previous pos before its selection
                    if menu.cancel and event.key == pygame.K_e:
                        pygame.mixer.Channel(1).play(cancel)
                        # to return to previous pos:
                        if player.vert_count < 0:
                            # if vert_count < 0, shows that net y displacement is downwards (due to s key)
                            for count in range(abs(player.vert_count)):
                                player.rect.y -= cell_total
                        else:
                            for count in range(abs(player.vert_count)):
                                player.rect.y += cell_total

                        if player.hor_count < 0:
                            # if hor_count < 0, shows that net x displacement is left (due to a key)
                            for count in range(abs(player.hor_count)):
                                player.rect.x -= cell_total
                        else:
                            for count in range(abs(player.hor_count)):
                                player.rect.x += cell_total

                        # check variables are set to False and vert_count and hor_count are set to 0 so character can
                        # be reselected
                        player.vert_count = 0
                        player.hor_count = 0
                        player_action = False
                        player.action_early = False
                        player.canATK = False
                        player_select = False
                        player_move.clear()
                        player.attack_target.clear()
                        menu.reset_option()
                        player.w = False
                        player.s = False
                        player.a = False
                        player.d = False

    kill_enemy()
    for enemy in enemies:
        print(f'{enemy.name} index: {enemy.index}')
    # enemy turn start
    if len(player_names) == len(players):
        enemy_select = True
        print("enemy_move",len(enemy_move))
        if len(enemy_move) > 0:
            print(enemy_move[0].name)

    if enemy_select:
        # the target unique to each player
        for enemy in enemies:
            if len(enemy_move) < 1 and enemy not in enemy_names:
                enemy_move.append(enemy)

        """Enemy Actions"""
        for selected_enemy in enemy_move:
            """Getting the target player"""
            selected_enemy.get_which_side()
            target_list = selected_enemy.get_target_list()

            for player in players:
                # to confirm that enemy and player target are on the same side of the screen
                player.get_which_side()
                if player.screen_side == selected_enemy.screen_side:
                    selected_enemy.append_target_list(player)

            nearest_player = selected_enemy.get_nearest_player()

            """To remove the coordinate if there is a player/enemy/wall in its spot"""
            if nearest_player is not None:
                enemy_coord = selected_enemy.get_coord()
                attacking_spots = nearest_player.get_spaces()

                # to remove the coordinate if there is a player in its spot
                for player in players:
                    coordP = player.get_coord()
                    if coordP in attacking_spots:
                        attacking_spots.remove(coordP)

                # to remove the coordinate if there is an enemy in its spot
                for enemy in enemies:
                    coordE = enemy.get_coord()
                    if coordE in attacking_spots and enemy != selected_enemy:
                        attacking_spots.remove(coordE)

                # to remove the coordinate if there is a wall in its spot
                for element in attacking_spots:
                    if env_matrix[element[1]][element[0]] == 0:
                        attacking_spots.remove(element)

                final_spot = nearest_player.space_shortest_distance(selected_enemy, attacking_spots)

                # some movement algorithm
                """movement"""
                # find the smallest euclidean distance and target that! ! ! ! ! !
                if ((abs(selected_enemy.vert_count) + abs(selected_enemy.hor_count)) < DISTANCE_THRESHOLD and
                        enemy_coord not in attacking_spots and final_spot is not None):
                    # moving down
                    if (enemy_coord[1] < final_spot[1] and selected_enemy.check_player_collision(nearest_player, 'down')
                            and selected_enemy.check_enemy_collision(selected_enemy, 'down')
                            and selected_enemy.check_wall_collision('down')):
                        pygame.time.delay(200)
                        selected_enemy.rect.y += cell_total
                        selected_enemy.vert_count -= 1

                    # moving right
                    elif (enemy_coord[0] < final_spot[0] and selected_enemy.check_player_collision(nearest_player,'right')
                          and selected_enemy.check_enemy_collision(selected_enemy, 'right')
                            and selected_enemy.check_wall_collision('right')):
                        pygame.time.delay(200)
                        selected_enemy.rect.x += cell_total
                        selected_enemy.hor_count += 1

                    # moving up
                    elif (enemy_coord[1] > final_spot[1] and selected_enemy.check_player_collision(nearest_player,'up')
                            and selected_enemy.check_enemy_collision(selected_enemy, 'up')
                            and selected_enemy.check_wall_collision('up')):
                        pygame.time.delay(200)
                        selected_enemy.rect.y -= cell_total
                        selected_enemy.vert_count += 1
                    # moving left
                    elif (enemy_coord[0] > final_spot[0] and selected_enemy.check_player_collision(nearest_player,'left')
                          and selected_enemy.check_enemy_collision(selected_enemy, 'left')
                          and selected_enemy.check_wall_collision('left')):
                        pygame.time.delay(200)
                        selected_enemy.rect.x -= cell_total
                        selected_enemy.hor_count -= 1
                    # moving down but blocked by obstacle
                    elif (enemy_coord[1] < final_spot[1] and (not selected_enemy.check_player_collision(nearest_player, 'down')
                            or not selected_enemy.check_enemy_collision(selected_enemy, 'down')
                            or not selected_enemy.check_wall_collision('down'))):
                        pygame.time.delay(200)
                        # check for left and right
                        if (selected_enemy.check_player_collision(nearest_player,'left')
                                and selected_enemy.check_enemy_collision(selected_enemy, 'left')
                                and selected_enemy.check_wall_collision('left')):
                            selected_enemy.rect.x -= cell_total
                            selected_enemy.hor_count -= 1
                        elif (selected_enemy.check_player_collision(nearest_player,'right')
                                and selected_enemy.check_enemy_collision(selected_enemy, 'right')
                                and selected_enemy.check_wall_collision('right')):
                            selected_enemy.rect.x += cell_total
                            selected_enemy.hor_count += 1

                elif enemy_coord in attacking_spots:
                    print(f'attack {nearest_player.name}')
                    nearest_player.damaged(selected_enemy.atk)
                    selected_enemy.vert_count = 0
                    selected_enemy.hor_count = 0
                    enemy_names.append(selected_enemy)
                    enemy_move.remove(selected_enemy)

                elif (abs(selected_enemy.vert_count) + abs(selected_enemy.hor_count)) == DISTANCE_THRESHOLD:
                    selected_enemy.vert_count = 0
                    selected_enemy.hor_count = 0
                    enemy_names.append(selected_enemy)
                    enemy_move.remove(selected_enemy)

                elif final_spot == None:
                    selected_enemy.vert_count = 0
                    selected_enemy.hor_count = 0
                    enemy_names.append(selected_enemy)
                    enemy_move.remove(selected_enemy)

                attacking_spots.clear()
                selected_enemy.clear_all_list()
                kill_player()
                # some code to end the moving turn
            else:
                enemy_names.append(selected_enemy)
                enemy_move.remove(selected_enemy)
                print(f'name: {selected_enemy.name}')
                print(f'enemy_names: {enemy_names}')
                print(f'{len(enemy_names)} == {len(enemies)}')
                selected_enemy.clear_all_list()
            """enemies attacking"""
        if len(enemy_names) == len(enemies) and len(enemy_move) == 0:
            enemy_select = False
            enemy_names.clear()
            player_names.clear()

    enemies.draw(screen)
    players.draw(screen)
    if len(player_move) == 1:
        attack_instruction(player_move[0])
    display_stats(stats_mouse_pos)
    clock.tick(60)
    pygame.display.update()
