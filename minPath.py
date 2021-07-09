#! /bin/env python3

from os import environ
environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"

import pygame
from argparse import ArgumentParser, RawDescriptionHelpFormatter
from enum import Enum
from colors import *
from collections import namedtuple

DEFAULT_SQUARE_SIZE = 20
DEFAULT_WIDTH = 50
DEFAULT_HEIGHT = 25

# increase STRAIGHT_PRICE for better accuracy, this is the price=distance of moving straight or in the diagonal way
STRAIGHT_PRICE = 1 << 20
DIAGONAL_PRICE = round(2 ** 0.5 * STRAIGHT_PRICE)

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
        self.coordinate_repr = namedtuple("Coordinate", "prev price")
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
        """Moves one click toward the bottom right

        Args:
            paint (Square, optional): [What to put in the empty squares that will be reached]. Defaults to Square.used.

        Returns:
            bool: Did we finish, wether we found the solution or got stuck
            bool: Is the position definitely unsolvable
        """
        
        # if first run, mark the top left and initialize the been_in = squares where we already arrived.
        # edges => locations at the end where we "grow" from 
        if self.edges == None:
            self.edges = dict()
            self.been_in = dict()
            # only been in top left, price is 0. and only edge it top left.
            self.been_in[0, 0] = self.coordinate_repr(None, 0)
            self.edges[0, 0] = 0  

            # if top left is blocked there is no solution.
            if self[0, 0] == Board.Square.blocked:
                return False, True
            
            # paint the top left.
            self[0, 0] = paint
            
            return False, False
        
        # list of the new edges at the "border"
        new_edges = dict()
        
        # for each point on the border
        for coord, price in self.edges.items():
            # for all it's neighboard which are not blocked or been in:
            for next, next_price in self._get_next(*coord, price):
                if next not in self.been_in or self.been_in[next].price > next_price:
                    # add to the new edges
                    new_edges[next] = next_price
                    # add or update to been_in with prev and price.
                    self.been_in[next] = self.coordinate_repr(coord, next_price)
                    # paint on the board
                    self[next] = paint
    
        # if we reached a block, or finished        
        if new_edges == dict():
            if (self.width - 1, self.height - 1) in self.been_in:
                coordinate = (self.width - 1, self.height - 1)
                # while didn't finish painting path (the only coordinate without a prev is: (0, 0))
                while coordinate:
                    self[coordinate] = Board.Square.solution
                    coordinate = self.been_in[coordinate].prev
                    
                return True, False
            
            # there is no solution
            self.edges = None
            self.been_in = None 
            return False, True
        
        # update edges
        self.edges = new_edges
        return False, False

    # draw the solution and only the solution
    def solve(self):
        self.clear_solution()
        solved, unsolvable = self(paint=Board.Square.empty)
        while not solved and not unsolvable:
            solved, unsolvable = self(paint=Board.Square.empty)
        return solved, unsolvable
    
    # remove all the marking in the solution process
    def clear_solution(self):
        self.edges = None
        self.been_in = None 
        # remove all the "non-blocked" marking from the board.
        self._screen_matrix = [[self[i, j] if self[i ,j] == Board.Square.blocked else Board.Square.empty for j in range(self.height)] for i in range(self.width)]
    
    def clear(self):
        """clear the board completely, essentially equal to reconstructing the board.
        """
        self._screen_matrix = [[Board.Square.empty] * self.height for i in range(self.width)]
        self.edges = None
        self.been_in = None
 
    # given a coordinates, return all the neighbors you can go to from it.
    def _get_next(self, x, y, price):
        next = [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]
        next_diagonal = [(x+ 1, y + 1), (x + 1, y - 1), (x - 1, y + 1), (x - 1, y - 1)]
        return [(coord, price + STRAIGHT_PRICE) for coord in next if 0 <= coord[0] < self.width and 0 <= coord[1] < self.height and Board.Square.blocked != self[coord]] + [(coord, price + DIAGONAL_PRICE) for coord in next_diagonal if 0 <= coord[0] < self.width and 0 <= coord[1] < self.height and Board.Square.blocked != self[coord]]  

def draw_msg(win: pygame.Surface, text: str, color: tuple[int, int, int]=WHITE):
    """display a text message to the center of the screen.

    Args:
        win (pygame.Surface): Screen to print on. 
        text (str): Text to print to the screen.
        color (tuple[int, int, int]: RGB color of the text to print)
    """
    draw_text = pygame.font.SysFont('comicsans', 100).render(text, 1, color)
    win.blit(draw_text, (win.get_size()[0] // 2 - draw_text.get_width() // 2, win.get_size()[1] // 2 - draw_text.get_height() // 2))

def main(width, height, square_size):
    clock = pygame.time.Clock()
    win = pygame.display.set_mode((width * square_size, height * square_size))
    pygame.display.set_caption("Shortest Path")
    pygame.font.init()

    board = Board(width, height)
    running = True
    mouse_down = False
    rightclick_down = False
    solved = False
    unsolvable = False

    while running:
        clock.tick(FPS)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            # get_pressed() returns a tuple of 3 of which buttons where clicked, 0 => left click, 1 => scroll wheel, 2 => right click 
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_down = pygame.mouse.get_pressed()[0]
                rightclick_down = pygame.mouse.get_pressed()[2]
                if solved:
                    board.clear_solution()
                solved = False
            elif event.type == pygame.MOUSEBUTTONUP:
                mouse_down = pygame.mouse.get_pressed()[0]
                rightclick_down = pygame.mouse.get_pressed()[2]
                if solved:
                    board.clear_solution()
                solved = False
            
            elif event.type == pygame.KEYDOWN:
                # Enter key => solve while showing how:
                if event.key == pygame.K_RETURN:
                    # clear previous solution if exists
                    board.clear_solution()                    
                    # while not finished solving: solve with clock tick
                    solved, unsolvable = board()
                    while not solved and not unsolvable:
                        pygame.display.update()
                        clock.tick(SOLVE_SPEED) 
                        board.draw(win)
                        pygame.display.update()
                        solved, unsolvable = board()
                    
                    solved = True  
                # tap => instal-solve.
                elif event.key == pygame.K_TAB:
                    solved, unsolvable = board.solve()
                # space => clear the board.
                elif event.key == pygame.K_SPACE:
                    board.clear()
                # backspace => clears all solution painting
                elif event.key == pygame.K_BACKSPACE:
                    board.clear_solution()
                # clicking c => step one step towards the solution
                elif event.key == pygame.K_c:
                    solved, unsolvable = board()
                
        # mouse down => drawing blocks
        if mouse_down:
            click = (pygame.mouse.get_pos()[0] // square_size, pygame.mouse.get_pos()[1] // square_size)
            board.block(*click)
            board.clear_solution()
         
        # rightclick down => removing blocks
        if rightclick_down:
            click = (pygame.mouse.get_pos()[0] // square_size, pygame.mouse.get_pos()[1] // square_size)
            board.delete(*click)
            board.clear_solution()
        
        # if board cannot be solved then display an error msg.
        if unsolvable:
            draw_msg(win, "No Path Exists")
            pygame.display.update()
            pygame.time.delay(2000)
            unsolvable = False
            board.clear_solution()
            
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
