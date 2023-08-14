

import pygame
import sys
from pygame.math import Vector2 as vector
from pygame.mouse import get_pos as mouse_pos
from pygame.mouse import get_pressed as mouse_buttons

from menu import Menu
from settings import *


class Editor:
    def __init__(self):
        # main setup
        self.display_surface = pygame.display.get_surface()
        # This is a dictionary that contains all the data for the tiles
        self.canvas_data = {}

        # navigation
        self.origin = vector()
        self.pan_active = False
        self.pan_offset = vector()

        # support lines
        self.support_line_surf = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        self.support_line_surf.set_colorkey('green')
        self.support_line_surf.set_alpha(30)

        # Selection
        self.selection_index = 2
        self.last_selected_cell = None

        # Menu
        self.menu = Menu()

    # Support: get current cell
    def get_current_cell(self):
        distance_to_origin = vector(mouse_pos()) - self.origin
        if distance_to_origin.x > 0:
            col = int(distance_to_origin.x / TILE_SIZE)
        else:
            col = int(distance_to_origin.x / TILE_SIZE) - 1

        if distance_to_origin.y > 0:
            row = int(distance_to_origin.y / TILE_SIZE)
        else:
            row = int(distance_to_origin.y / TILE_SIZE) - 1

        return col, row

    # input
    def event_loop(self):
        # Explain: pygame.event.get() returns a list of all events
        # that happened since the last time pygame.event.get() was called.
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            self.pan_input(event)
            self.selection_hotkeys(event)
            self.menu_click(event)
            self.canvas_add()

    def pan_input(self, event):

        # middle mouse button pressed / released
        if event.type == pygame.MOUSEBUTTONDOWN and mouse_buttons()[1]:
            self.pan_active = True
            # distance between mouse and origin
            self.pan_offset = vector(mouse_pos()) - self.origin

        if not mouse_buttons()[1]:
            self.pan_active = False

        # mouse wheel
        if event.type == pygame.MOUSEWHEEL:
            if pygame.key.get_pressed()[pygame.K_LCTRL]:
                self.origin.y -= event.y * 50
            else:
                self.origin.x -= event.y * 50

        # panning update
        if self.pan_active:
            self.origin = vector(mouse_pos()) - self.pan_offset

    def selection_hotkeys(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RIGHT:
                self.selection_index += 1
            if event.key == pygame.K_LEFT:
                self.selection_index -= 1
        # Limiting the selection index based in the range of 2 to 18
        self.selection_index = max(2, min(self.selection_index, 18))

    def menu_click(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and self.menu.rect.collidepoint(mouse_pos()):
            self.selection_index = self.menu.click(mouse_pos(), mouse_buttons())

    def canvas_add(self):
        # Explain: mouse_buttons()[0] returns True if the left mouse button is pressed
        # and we're not clicking on the menu
        if mouse_buttons()[0] and not self.menu.rect.collidepoint(mouse_pos()):
            current_cell = self.get_current_cell()

            #
            if current_cell != self.last_selected_cell:
                if current_cell in self.canvas_data:
                    self.canvas_data[current_cell].add_id(self.selection_index)
                else:
                    # The dictionary have the current cell as key and the value is the selection index
                    self.canvas_data[current_cell] = CanvasTile(self.selection_index)
                self.last_selected_cell = current_cell

        for key, value in self.canvas_data.items():
            print(f'{key}: {value.has_terrain}')

    # drawing
    def draw_tile_lines(self):
        cols = WINDOW_WIDTH // TILE_SIZE
        rows = WINDOW_HEIGHT // TILE_SIZE

        origin_offset = vector(
            x=self.origin.x - int(self.origin.x / TILE_SIZE) * TILE_SIZE,
            y=self.origin.y - int(self.origin.y / TILE_SIZE) * TILE_SIZE)

        self.support_line_surf.fill('green')

        for col in range(cols + 1):
            x = origin_offset.x + col * TILE_SIZE
            pygame.draw.line(self.support_line_surf, LINE_COLOR, (x, 0), (x, WINDOW_HEIGHT))

        for row in range(rows + 1):
            y = origin_offset.y + row * TILE_SIZE
            pygame.draw.line(self.support_line_surf, LINE_COLOR, (0, y), (WINDOW_WIDTH, y))

        self.display_surface.blit(self.support_line_surf, (0, 0))

    def run(self, dt):
        self.event_loop()

        # drawing
        self.display_surface.fill('gray')
        self.draw_tile_lines()
        pygame.draw.circle(self.display_surface, 'red', self.origin, 10)
        self.menu.display(self.selection_index)


class CanvasTile:
    def __init__(self, tile_id):
        # Terrain
        self.has_terrain = False
        self.terrain_neighbors = []

        # Water
        self.has_water = False
        self.water_on_top = False

        # Coin
        self.coin = None  # 4, 5 or 6

        # Enemy
        self.enemy = None

        # Objects
        self.objects = []

        self.add_id(tile_id)

    def add_id(self, tile_id):
        options = {key: value['style'] for key, value in EDITOR_DATA.items()}
        match options[tile_id]:
            case 'terrain': self.has_terrain = True
            case 'water': self.has_water = True
            case 'coin': self.coin = tile_id
            case 'water': self.enemy = tile_id
