from typing import Iterable, List, Tuple, Dict
from sys import exit
from pygame import Surface, transform, image
from random import randint


class FieldInputFormatError(Exception):
    pass


def read_field(path: str, wall_keys: Tuple[str]) -> Tuple[List[List[str]], List[List[int]]]:
    draw_field: List[List[str]] = []

    try:

        with open(path) as f:

            size = len(f.readline().split())

            f.seek(0)

            try:
                for line in f.readlines():
                    split = line.split()

                    if len(split) != size:
                        raise FieldInputFormatError
                    else:
                        draw_field.append(split)

                if len(draw_field) != size:
                    raise FieldInputFormatError

            except FieldInputFormatError:
                exit('Field input file has wrong formatting. (func=read_field)')

        play_field: List[List[int]] = []

        for line in draw_field:

            temp = []

            for elem in line:

                if elem == 'tu7':
                    temp.append(2)

                elif elem in wall_keys:
                    temp.append(1)

                else:
                    temp.append(0)

            play_field.append(temp)

        return draw_field, play_field

    except OSError:
        exit(f'No such file. (func=read_field, {path=})')


def surf_import(path: str, size: Tuple[int, int]) -> Surface:
    try:

        img = image.load(path).convert_alpha()

    except OSError:
        print(f'No such file. (func=surf_import, {path=})')
        img = image.load('sprites/pacman.png').convert_alpha()

    return transform.scale(img, size)


def load_sprite_collection(folder: str, keys: Iterable[str],
                           size: Tuple[int, int]) -> Dict[str, Surface]:
    coll: Dict[str, Surface] = {}

    for key in keys:
        coll[key] = surf_import(f'{folder}\\{key}.png', size)

    return coll


def adjacent() -> Tuple[Tuple[int, int]]:
    return ((0, 1), (1, 0), (0, -1), (-1, 0))


def not_in_field(field: Tuple[Tuple[int, int]], pos: Tuple[int, int]) -> bool:
    return (pos[0] > len(field) - 1 or pos[0] < 0) or \
        (pos[1] > len(field) - 1 or pos[1] < 0)


def on_bound(field: List[List[int]], node: Tuple[int, int]) -> bool:
    return (node[0] == 0 or node[0] == len(field[0]) - 1) or \
        (node[1] == 0 or node[1] == len(field) - 1)


class Node:
    def __init__(self, parent=None, position: Tuple[int, int] = None,
                 g=0, h=0):
        self.parent: Node = parent
        self.position: Tuple[int, int] = position

        self.f = g + h
        self.g = g
        self.h = h

    def __eq__(self, other) -> bool:
        return self.position == other.position

    def __lt__(self, other) -> bool:
        return self.f < other.f

    def __gt__(self, other) -> bool:
        return self.f > other.f


def spec_dist(pos1: Tuple[int, int], pos2: Tuple[int, int]) -> int:
    return abs((pos1[0] - pos2[0]) ** 2 + (pos1[1] - pos2[1]) ** 2)


def Astar(field: Tuple[Tuple[int, int]], begin: Tuple[int, int],
          end: Tuple[int, int]) -> Tuple[List[List[int]], int]:
    begin_node = Node(position=begin)
    end_node = Node(position=end)

    open_list: List[Node] = []
    closed_list: List[Node] = []

    open_list.append(begin_node)

    while len(open_list) > 0:

        current_node = open_list[0]
        current_index = 0

        for i, node in enumerate(open_list):
            if node < current_node:
                current_node = node
                current_index = i

        open_list.pop(current_index)
        closed_list.append(current_node)

        if current_node == end_node:

            path = []
            price = 0
            node = current_node

            while node is not None:
                path.append(node.position)
                price += node.f
                node = node.parent

            return path[::-1], price

        for new_pos in adjacent():

            node_pos = (current_node.position[0] + new_pos[0],
                        current_node.position[1] - new_pos[1])

            if not_in_field(field, node_pos):
                continue

            if field[node_pos[1]][node_pos[0]] == 1:
                continue

            is_unique: bool = True

            for closed_node in closed_list:
                if node_pos == closed_node.position:
                    is_unique = False

            for open_node in open_list:
                if node_pos == open_node.position:
                    is_unique = False

            if is_unique:
                open_list.append(Node(parent=current_node, position=node_pos,
                                      g=current_node.h + 1, h=spec_dist(node_pos, end)))


def get_dir(pos1: Tuple[int, int], pos2: Tuple[int, int]) -> Tuple[int, int]:
    return (pos2[0] - pos1[0], pos2[1] - pos1[1])


def neg_dir(direction: Tuple[int, int]) -> Tuple[int, int]:
    return (direction[0] * -1, direction[1] * -1)


def vec_sum(vec1: Tuple[int, int], vec2: Tuple[int, int]) -> Tuple[int, int]:
    return (vec1[0] + vec2[0], vec1[1] + vec2[1])
