#! /bin/env python3

from os import environ
environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"

import pygame
from argparse import ArgumentParser, RawDescriptionHelpFormatter
from enum import Enum
from colors import *

DEFAULT_SQUARE_SIZE = 20
DEFAULT_WIDTH = 50
DEFAULT_HEIGHT = 25

UNSOLVABLE = pygame.USEREVENT + 1

FPS = 240
SOLVE_SPEED = 60


class Board:
    class Square(Enum):
        empty = 0
        used = 1
        blocked = 2
        solution = 3
        
        def __str__(self):
            return str(self.name)
        
        def __repr__(self):
            return str(self)
    
    
    def __init__(self, width: int, height: int):
        self._width = width
        self._height = height
        self._screen_matrix = [[Board.Square.empty] * self.height for i in range(self.width)]
        self.edges = None
        self.been_in = None
    
    def __setitem__(self, pos, value):
        self._screen_matrix[pos[0]][pos[1]] = value
    
    def __getitem__(self, pos):
        return self._screen_matrix[pos[0]][pos[1]]
    
    # block a coordinate
    def block(self, x, y):
        self[x, y] = Board.Square.blocked
    
    # unblock a coordinate
    def delete(self, x, y):
        self[x, y] = Board.Square.empty
    
    def __str__(self):
        return '\n'.join([str([self[i, j] for i in range(self.width)]) for j in range(self.height)])        
        
    def __repr__(self):
        return str(self)
    
    @property
    def width(self):
        return self._width
    
    @property
    def height(self):
        return self._height
    
    # draw the board to win
    def draw(self, win):
        # size of "pixel" to print on
        SQUARE_SIZE = win.get_size()[0] // self.width
        win.fill(BLACK)
                
        # print all the squared which are not empty each one with his own color.
        for col in range(self.width):
            for row in range(self.height):        
                # location on the board to print is col "pixels" and row "pixels" from the top left
                if self[col, row] == Board.Square.blocked:
                    pygame.draw.rect(win, BLUE, (SQUARE_SIZE * col,  SQUARE_SIZE * row, SQUARE_SIZE, SQUARE_SIZE))
                elif self[col, row] == Board.Square.used:
                    pygame.draw.rect(win, GREEN, (SQUARE_SIZE * col,  SQUARE_SIZE * row, SQUARE_SIZE, SQUARE_SIZE))      
                elif self[col, row] == Board.Square.solution:
                     pygame.draw.rect(win, RED, (SQUARE_SIZE * col,  SQUARE_SIZE * row, SQUARE_SIZE, SQUARE_SIZE))        
    
    # move one step to solve the shortest path, mark the places that are reached.
    # when solved mark the solution
    def __call__(self, paint=Square.used):     
        """[Moves one click toward the bottom right]

        Args:
            paint ([Square], optional): [What to put in the empty squares that will be reached]. Defaults to Square.used.

        Returns:
            [bool]: [Did we finish, wither find the solution or reached a block]
        """
        
        # if first run, mark the top left and initialize the been_in = squares where we already arrived.
        # edges => locations at the end where we "grow" from 
        if self.edges == None:
            self.edges = []
            self.been_in = dict()
            # only been in top left, and only edge it top left.
            self.been_in[0, 0] = (0, 0)
            self.edges.append((0, 0))  

            # if top left is blocked there is no solution.
            if self[0, 0] == Board.Square.blocked:
                pygame.event.post(pygame.event.Event(UNSOLVABLE))
                return True
            
            # paint the top left.
            self[0, 0] = paint
            
            return False
        
        # list of the new edges at the "border"
        new_edges = []
        # have we reached the end
        ended = False
        
        # for each point on the border
        for coord in self.edges:
            # for all it's neighboard which are not blocked or been in:
            for next in self._get_next(*coord):
                if next not in self.been_in:
                    # add then to the new adges
                    new_edges.append(next)
                    # set it to the dictionary of where we were and how we got there
                    self.been_in[next] = coord
                    self[next] = paint
                    
                    # if we reached the end, mark the solution
                    if next == (self.width - 1, self.height - 1):
                        pos = (self.width - 1, self.height - 1)
                        
                        while pos != (0, 0):
                            self[pos] = Board.Square.solution
                            pos = self.been_in[pos]
                        
                        # set the variables and reset the edges and been in to None for next usage
                        self[0, 0] = Board.Square.solution
                        self.edges = None
                        self.been_in = None 
                        return True
        
        # if we reached a block          
        if new_edges == self.edges:
            # there is no solution
            pygame.event.post(pygame.event.Event(UNSOLVABLE))
            self.edges = None
            self.been_in = None 
            return True
        
        # keep the new edges
        self.edges = new_edges
        return False
    
    # draw the solution and only the solution
    def solve(self):
        self.clear_solution()
        while not self(paint=Board.Square.empty):
            pass
    
    # remove all the marking in the solution process
    def clear_solution(self):
        self.edges = None
        self.been_in = None 
        # remove all the "non-blocked" marking from the board.
        self._screen_matrix = [[self[i, j] if self[i ,j] == Board.Square.blocked else Board.Square.empty for j in range(self.height)] for i in range(self.width)]
 
    # given a coordinates, return all the neighbors you can go to from it.
    def _get_next(self, x, y):
        next = [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]
        return [coord for coord in next if 0 <= coord[0] < self.width and 0 <= coord[1] < self.height and self[coord] != Board.Square.blocked]
    
# print a msg to the screen for 2 seconds
def draw_msg(win, text):
    draw_text = pygame.font.SysFont('comicsans', 100).render(text, 1, WHITE)
    win.blit(draw_text, (win.get_size()[0] // 2 - draw_text.get_width() // 2, win.get_size()[1] // 2 - draw_text.get_height() // 2))
    pygame.display.update()
    pygame.time.delay(2000)    

def main(width, height, square_size):
    clock = pygame.time.Clock()
    win = pygame.display.set_mode((width * square_size, height * square_size))
    pygame.display.set_caption("Shortest Path")
    pygame.font.init()

    board = Board(width, height)
    running = True
    mouse_down = False
    rightclick_down = False

    while running:
        clock.tick(FPS)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_down = pygame.mouse.get_pressed()[0]
                rightclick_down = pygame.mouse.get_pressed()[2]
            elif event.type == pygame.MOUSEBUTTONUP:
                mouse_down = pygame.mouse.get_pressed()[0]
                rightclick_down = pygame.mouse.get_pressed()[2]
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    board.clear_solution()
                    while not board():
                        clock.tick(SOLVE_SPEED) 
                        board.draw(win)
                        pygame.display.update()  
                elif event.key == pygame.K_TAB:
                    board.solve()
                elif event.key == pygame.K_SPACE:
                    board = Board(width, height)
                elif event.key == pygame.K_BACKSPACE:
                    board.clear_solution()
                elif event.key == pygame.K_c:
                    board()
                    
            elif event.type == UNSOLVABLE:
                draw_msg(win, "No Path Exists")
                board.clear_solution()                       
                
        if mouse_down:
            click = (pygame.mouse.get_pos()[0] // square_size, pygame.mouse.get_pos()[1] // square_size)
            board.block(*click)
         
        if rightclick_down:
            click = (pygame.mouse.get_pos()[0] // square_size, pygame.mouse.get_pos()[1] // square_size)
            board.delete(*click)
            
        board.draw(win)
        pygame.display.update()



if __name__ == "__main__":
    parser = ArgumentParser(
        formatter_class=RawDescriptionHelpFormatter,
        description="""
    Use the left mouse click to add a block to the screen.
    Use the right mouse click to remove a block from the screen.
    Use the enter key to find the shortest path from top-left to bottom-right.
    Use the tab key to find the shortest path instantly.
    Use the backspace key to delete the solution.
    Use the spacebar to clear the screen.
        """
    )      
    parser.add_argument("-he", "--height", help="number of squares to the height of the window", action="store", type=int, default=DEFAULT_HEIGHT)
    parser.add_argument("-w", "--width", help="number of squares to the width of the window", action="store", type=int, default=DEFAULT_WIDTH)
    parser.add_argument("-s", "--squaresize", help="size of the squares to use", action="store", type=int, default=DEFAULT_SQUARE_SIZE)
    args = parser.parse_args()
    
    main(height=args.height, width=args.width, square_size=args.squaresize)
