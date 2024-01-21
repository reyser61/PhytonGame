from typing import Dict, Tuple, List
import pygame as pg
from abc import ABC
import funcs as f
from sys import exit
from random import choice
from time import perf_counter


Colors: Dict[str, Tuple[int]] = {
    'Black': (0, 0, 0),
    'White': (255, 255, 255),
    'Red': (255, 0, 0),
    'Green': (0, 255, 0),
    'Blue': (0, 0, 255),
    'Yellow': (255, 255, 0)
}


class Field:
    def __init__(self, window_size: Tuple[int], field_path: str, field_sprites_folder: str):


        self.sprite_keys: Tuple[str] = tuple(
            open(f'{field_sprites_folder}\\sprite_keys.txt').readline().split()
        )


        self.wall_keys: Tuple[str] = tuple(
            open(f'{field_sprites_folder}\\wall_keys.txt').readline().split()
        )


        self.draw_field, self.play_field = f.read_field(field_path, self.wall_keys)
        self.field_size = len(self.draw_field)


        self.tile_size: int = round(min(window_size) / self.field_size)


        self.sprites: Dict[str, pg.Surface] = f.load_sprite_collection(
            folder=field_sprites_folder, keys=self.sprite_keys,
            size=(self.tile_size, self.tile_size)
        )

        self.horizontal_centering = window_size[0] > window_size[1]
        self.alignment_offset = (max(window_size) - self.field_size * self.tile_size) // 2

    def draw(self, screen: pg.Surface) -> None:

        if self.horizontal_centering:

            for i, row in enumerate(self.draw_field):
                for j in range(len(row)):

                    try:

                        screen.blit(self.sprites[self.draw_field[i][j]],
                                    (self.alignment_offset + j * self.tile_size, i * self.tile_size))

                    except BaseException:

                        pass

        else:

            for i, row in enumerate(self.draw_field):
                for j in range(len(row)):

                    try:

                        screen.blit(self.sprites[self.draw_field[i][j]],
                                    (j * self.tile_size, self.alignment_offset + i * self.tile_size))

                    except BaseException:

                        pass

    def get_screen_pos(self, row: int, col: int) -> Tuple[int]:

        if self.horizontal_centering:

            return (self.alignment_offset + col * self.tile_size, row * self.tile_size)

        else:

            return (col * self.tile_size, self.alignment_offset + row * self.tile_size)


class Pacman:
    def __init__(self, size: int, sprite_folder: str, field: Field,
                 field_pos: Tuple[int], v: float):

        self.size: Tuple[int] = (size, size)
        self.sprite: pg.Surface = f.surf_import(f'{sprite_folder}\pacman.png', self.size)

        self.field: Field = field
        self.field_pos: List[int] = list(field_pos)
        self.prev_pos: List[int] = list(field_pos)
        self.screen_pos: List[int] = field.get_screen_pos(field_pos[1], field_pos[0])
        self.velocity: float = v
        self.direction: List[int] = [0, 0]
        self.direction_queue: List[Tuple[int]] = []

        self.can_eat_ghosts: bool = False
        self.pu_start_time: int = 0

        self.score: int = 0

    def change_dir(self, direction: Tuple[int]) -> None:

        if self.direction == list(direction):

            pass

        elif self.direction == list(f.neg_dir(direction)):

            self.prev_pos = self.field_pos

            self.direction = list(direction)

        elif self.direction == [0, 0]:

            new_field_pos = f.vec_sum(direction, self.field_pos)

            if self.field.play_field[new_field_pos[1]][new_field_pos[0]] == 0:
                self.direction = list(direction)

        else:

            if self.direction_queue.count(direction) == 0:
                self.direction_queue.append(direction)

    def __check_dir_queue(self) -> None:

        if len(self.direction_queue) > 1:

            for i, dir1 in enumerate(self.direction_queue):
                for j, dir2 in enumerate(self.direction_queue):

                    if i != j and dir1 == f.neg_dir(dir2):

                        if i > j:

                            self.direction_queue.remove(dir2)

                        else:

                            self.direction_queue.remove(dir1)

        if len(self.direction_queue) == 1:

            tile_sc_pos = self.field.get_screen_pos(self.field_pos[1], self.field_pos[0])

            if abs(self.screen_pos[0] - tile_sc_pos[0]) < self.velocity and \
                    abs(self.screen_pos[1] - tile_sc_pos[1]) < self.velocity:

                new_f_pos = f.vec_sum(self.direction_queue[0], self.field_pos)

                if self.field.play_field[new_f_pos[1]][new_f_pos[0]] == 0:
                    self.direction = list(self.direction_queue[0])
                    self.direction_queue.pop(0)

        elif len(self.direction_queue) == 0:

            pass

        else:

            exit('Direction queue is broken.')

    def __check_position(self) -> None:

        new_field_pos = f.vec_sum(self.direction, self.field_pos)
        new_screen_pos = self.field.get_screen_pos(new_field_pos[1], new_field_pos[0])

        in_new_tile = False

        match self.direction:

            case [0, -1]:
                in_new_tile = self.screen_pos[1] <= new_screen_pos[1]

            case [1, 0]:
                in_new_tile = self.screen_pos[0] >= new_screen_pos[0]

            case [0, 1]:
                in_new_tile = self.screen_pos[1] >= new_screen_pos[1]

            case [-1, 0]:
                in_new_tile = self.screen_pos[0] <= new_screen_pos[0]

            case _:

                pass

        if in_new_tile:

            self.prev_pos = self.field_pos
            self.field_pos = list(new_field_pos)
            self.screen_pos = list(new_screen_pos)

            match self.field.draw_field[new_field_pos[1]][new_field_pos[0]]:

                case 'pu':

                    self.field.draw_field[new_field_pos[1]][new_field_pos[0]] = 'em'

                    self.can_eat_ghosts = True
                    self.pu_start_time = perf_counter()

                case 'f':

                    self.field.draw_field[new_field_pos[1]][new_field_pos[0]] = 'em'

                    self.score += 100

                case _:

                    pass

    def __check_powerup(self):

        if perf_counter() - self.pu_start_time >= 5:
            self.can_eat_ghosts = False

    def move(self) -> None:
        # Assisting funcs
        self.__check_position()
        self.__check_dir_queue()
        if self.can_eat_ghosts:
            self.__check_powerup()

        new_field_pos = f.vec_sum(self.direction, self.field_pos)

        if self.field.play_field[new_field_pos[1]][new_field_pos[0]] == 0:
            self.screen_pos = [self.screen_pos[0] + self.direction[0] * self.velocity,
                               self.screen_pos[1] + self.direction[1] * self.velocity]

    def draw(self, screen: pg.Surface) -> None:

        phi: float = .0

        match self.direction:

            case [0, -1]:
                phi = -90.0

            case [1, 0]:
                phi = 180.0

            case [0, -1]:
                phi = 90.0

            case [-1, 0]:
                phi = 0.0

            case _:

                pass

        screen.blit(
            pg.transform.rotate(self.sprite, phi), tuple(self.screen_pos)
        )


class Ghost(ABC):
    def __init__(self, color: str, sprite_folder: str, size: int, field: Field,
                 field_pos: Tuple[int, int], v: float, target: Pacman):

        self.size: Tuple[int, int] = (size, size)
        self.sprite: pg.Surface = f.surf_import(path=f'{sprite_folder}\{color}_ghost.png', size=self.size)
        self.alt_sprite: pg.Surface = f.surf_import(path=f'{sprite_folder}\weak_ghost.png', size=self.size)

        self.field: Field = field
        self.spawn_field_pos: Tuple[int, int] = field_pos
        self.field_pos: List[int] = list(field_pos)
        self.screen_pos: List[int] = list(field.get_screen_pos(field_pos[1], field_pos[0]))
        self.velocity: float = v
        self.alt_v: float = v / 2
        self.direction: List[int] = [0, 0]

        self.target: Pacman = target
        self.tar_pos: List[int] = [0, 0]
        self.path: List[Tuple[int, int]] = []
        self.is_dead = False

    def draw(self, screen: pg.Surface) -> None:

        if not self.target.can_eat_ghosts:

            screen.blit(self.sprite, tuple(self.screen_pos))

        else:

            screen.blit(self.alt_sprite, tuple(self.screen_pos))

    def _get_tar_pos(self) -> List[int]:
        pass

    def _get_dir(self) -> None:
        self.direction = list(f.get_dir(self.field_pos, self.path[0]))

    def _update_path(self) -> None:

        sc_pos = self.field.get_screen_pos(self.field_pos[0], self.field_pos[1])

        if abs(self.screen_pos[0] - sc_pos[0]) < self.velocity and \
                abs(self.screen_pos[1] - sc_pos[1]) < self.velocity:

            self.path = f.Astar(
                field=self.field.play_field, begin=tuple(self.field_pos), end=tuple(self.tar_pos)
            )[0]

        else:

            path1, cost1 = f.Astar(
                field=self.field.play_field, begin=tuple(self.field_pos), end=tuple(self.tar_pos)
            )
            path2, cost2 = f.Astar(
                field=self.field.play_field, end=tuple(self.tar_pos),
                begin=f.vec_sum(self.field_pos, self.direction)
            )

            if cost1 > cost2:

                self.path = path2

            else:

                self.path = path1

                self.field_pos = list(f.vec_sum(self.field_pos, self.direction))

        if list(self.path[0]) == self.field_pos:
            self.path.pop(0)

    def _check_pos(self) -> None:

        new_pos = f.vec_sum(self.field_pos, self.direction)
        new_sc_pos = self.field.get_screen_pos(new_pos[1], new_pos[0])

        in_new_tile = False

        match self.direction:

            case [0, 1]:
                in_new_tile = self.screen_pos[1] >= new_sc_pos[1]

            case [1, 0]:
                in_new_tile = self.screen_pos[0] >= new_sc_pos[0]

            case [0, -1]:
                in_new_tile = self.screen_pos[1] <= new_sc_pos[1]

            case [-1, 0]:
                in_new_tile = self.screen_pos[0] <= new_sc_pos[0]

        if in_new_tile:

            self.field_pos = list(new_pos)
            self.screen_pos = list(new_sc_pos)

            self.path.pop(0)

            if len(self.path) != 0:
                self._get_dir()
            else:
                self.is_dead = False
                self.direction = [0, 0]

    def _check_collision(self) -> None:

        collides: bool = False

        collides = (self.target.screen_pos[0] + self.target.size[0] > self.screen_pos[0] and \
                    self.target.screen_pos[0] < self.screen_pos[0] + self.size[0]) and \
                   (self.target.screen_pos[1] + self.target.size[1] > self.screen_pos[1] and \
                    self.target.screen_pos[1] < self.screen_pos[1] + self.size[1])

        if collides:

            if self.target.can_eat_ghosts and not self.is_dead:

                self.velocity = self.alt_v * 10
                self.target.score += 1000
                self.is_dead = True

            elif not self.target.can_eat_ghosts:

                exit('game over')

    def move(self) -> None:

        # Assisting funcs
        self._check_pos()
        self._check_collision()

        if not self.target.can_eat_ghosts:

            if self.velocity != self.alt_v * 2:
                self.velocity = self.alt_v * 2

            if self._get_tar_pos() != self.tar_pos:
                self.tar_pos = self._get_tar_pos()

                self._update_path()

                self._get_dir()

        else:

            if self.tar_pos != list(self.spawn_field_pos):

                self.tar_pos = list(self.spawn_field_pos)

                self._update_path()

                self._get_dir()

                self.velocity = self.alt_v

        self.screen_pos = [self.screen_pos[0] + self.direction[0] * self.velocity,
                           self.screen_pos[1] + self.direction[1] * self.velocity]


class RedGhost(Ghost):
    def __init__(self, sprite_folder: str, size: int, field: Field,
                 field_pos: Tuple[int, int], v: float, target: Pacman):
        super().__init__(
            color='red', sprite_folder=sprite_folder, size=size,
            field=field, field_pos=field_pos, v=v, target=target
        )

    def _get_tar_pos(self) -> List[int]:
        return self.target.field_pos


class GreenGhost(Ghost):
    def __init__(self, sprite_folder: str, size: int, field: Field,
                 field_pos: Tuple[int, int], v: float, target: Pacman):
        super().__init__(
            color='green', sprite_folder=sprite_folder, size=size,
            field=field, field_pos=field_pos, v=v, target=target
        )

    def _get_tar_pos(self) -> List[int]:
        return self.target.prev_pos


class BlueGhost(Ghost):
    def __init__(self, sprite_folder: str, size: int, field: Field,
                 field_pos: Tuple[int, int], v: float, target: Pacman):

        super().__init__(
            color='blue', sprite_folder=sprite_folder, size=size,
            field=field, field_pos=field_pos, v=v, target=target
        )

    def _get_tar_pos(self) -> List[int]:

        pot_pos: Tuple[int, int] = f.vec_sum(self.target.field_pos, self.target.direction)

        if self.field.play_field[pot_pos[1]][pot_pos[0]] == 0:

            return list(pot_pos)

        else:

            potentials: List[List[int]] = []

            for adj in f.adjacent():

                new_pos: Tuple[int, int] = f.vec_sum(self.target.field_pos, adj)

                if self.field.play_field[new_pos[1]][new_pos[0]] == 0 and \
                        self.direction != f.neg_dir(adj):
                    potentials.append(new_pos)

        if len(potentials) != 0:

            return choice(potentials)

        else:

            return self.target.prev_pos


class YellowGhost(Ghost):
    def __init__(self, sprite_folder: str, size: int, field: Field,
                 field_pos: Tuple[int, int], v: float, target: Pacman):

        super().__init__(
            color='yellow', sprite_folder=sprite_folder, size=size,
            field=field, field_pos=field_pos, v=v, target=target
        )

    def _get_tar_pos(self) -> List[int]:

        pos_x: int = 0
        pos_y: int = 0

        while self.field.play_field[pos_y][pos_x] != 0:
            pos_y = choice(range(len(self.field.play_field)))
            pos_x = choice(range(len(self.field.play_field[0])))

        self.tar_pos = [pos_x, pos_y]

        self._update_path()
        self._get_dir()

        return self.tar_pos

    def move(self) -> None:

        self._check_pos()
        self._check_collision()

        if not self.target.can_eat_ghosts:

            if self.velocity != self.alt_v * 2:
                self.velocity = self.alt_v * 2

            if self.field_pos == self.tar_pos or \
                    self.tar_pos == list(self.spawn_field_pos):

                self._get_tar_pos()

            elif self.direction == [0, 0]:
                self._get_tar_pos()

        else:

            if self.tar_pos != list(self.spawn_field_pos):
                self.tar_pos = list(self.spawn_field_pos)

                self._update_path()

                self._get_dir()

                self.velocity = self.alt_v

        self.screen_pos = [self.screen_pos[0] + self.direction[0] * self.velocity,
                           self.screen_pos[1] + self.direction[1] * self.velocity]


class Game:
    def __init__(self, w: int = 800, h: int = 600, fps: int = 60):

        self.size: Tuple[int, int] = (w, h)
        self.fps: int = fps
        self.sc = pg.display.set_mode(self.size)
        self.clock = pg.time.Clock()
        self.is_on: bool = True

        self.score: int = 0

        pg.mixer.init()
        pg.mixer.music.load('sprites/music.mp3')
        pg.mixer.music.play(-1)
        self.field = Field(
            window_size=self.size, field_path='field/field.txt', field_sprites_folder='sprites/field_sprites'
        )

        self.pacman = Pacman(
            size=self.field.tile_size, sprite_folder='sprites', field=self.field,
            field_pos=(1, 2), v=2
        )

        spawns: List[List[int]] = []
        for row in range(len(self.field.draw_field)):
            for col in range(len(self.field.draw_field[row])):
                if self.field.draw_field[row][col] == 'gh':
                    self.field.draw_field[row][col] = 'em'
                    spawns.append((col, row))

        self.ghosts: Dict[str, Ghost] = {
            'Red': RedGhost(
                sprite_folder='sprites', size=self.field.tile_size,
                field=self.field, field_pos=spawns[0], v=1, target=self.pacman
            ),

            'Green': GreenGhost(
                sprite_folder='sprites', size=self.field.tile_size,
                field=self.field, field_pos=spawns[1], v=1, target=self.pacman
            ),

            'Blue': BlueGhost(
                sprite_folder='sprites', size=self.field.tile_size,
                field=self.field, field_pos=spawns[2], v=1, target=self.pacman
            ),

            'Yellow': YellowGhost(
                sprite_folder='sprites', size=self.field.tile_size,
                field=self.field, field_pos=spawns[3], v=1, target=self.pacman
            )
        }

    def process_events(self, events: List[pg.event.Event]) -> None:

        for event in events:

            match event.type:

                case pg.QUIT:

                    self.is_on = False

                case pg.KEYDOWN:

                    match event.key:

                        case pg.K_w | pg.K_UP:

                            self.pacman.change_dir((0, -1))

                        case pg.K_a | pg.K_LEFT:

                            self.pacman.change_dir((-1, 0))

                        case pg.K_s | pg.K_DOWN:

                            self.pacman.change_dir((0, 1))

                        case pg.K_d | pg.K_RIGHT:

                            self.pacman.change_dir((1, 0))

                        case _:

                            pass

    def move(self):

        self.pacman.move()

        for i, ghost in enumerate(self.ghosts.values()):
            ghost.move()


    def draw(self) -> None:

        self.sc.fill(Colors['Black'])

        # Draw field
        self.field.draw(self.sc)

        # Draw pacman
        self.pacman.draw(self.sc)

        # Draw ghosts
        for ghost in self.ghosts.values():
            ghost.draw(self.sc)

    def loop(self) -> None:

        performance_list: List[int] = []

        while self.is_on:

            events = pg.event.get()
            self.process_events(events)

            self.move()

            self.draw()

            pg.display.flip()
            self.clock.tick(self.fps)

            if self.pacman.score != self.score:
                pg.display.set_caption(str(self.pacman.score))
                self.score = self.pacman.score

            if len(performance_list) >= 60:
                print(f'Average time for computing frame is '
                      f'{round(sum(performance_list) / len(performance_list), 2)} ms.'
                      )

                performance_list = []

            performance_list.append(self.clock.get_time())


game = Game()
game.loop()
