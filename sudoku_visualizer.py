"""
스도쿠 시각화 메인 진입점

pygame을 사용한 인터랙티브 스도쿠 솔버 GUI의 메인 함수입니다.
"""

import pygame
from sudoku import SudokuBoard
from sudoku.visualizer import SudokuVisualizer
from sudoku.input_dialog import SudokuInputDialog


def main():
    """메인 함수"""
    if not pygame.get_init():
        pygame.init()
    
    board_data = None
    screen = None
    
    while True:
        input_dialog = SudokuInputDialog(initial_board=board_data, screen=screen)
        screen = input_dialog.screen
        board_data = input_dialog.run()
        
        if board_data is None:
            break
        
        board = SudokuBoard(board_data)
        if not board.is_valid():
            continue
        
        visualizer = SudokuVisualizer(board, screen=screen)
        screen = visualizer.screen
        result = visualizer.run()
        
        if result is None:
            break
        else:
            board_data = result
    
    pygame.quit()


if __name__ == "__main__":
    main()
