"""
스도쿠 GUI 앱 실행 모듈.

입력 다이얼로그와 단계별 시각화 화면 사이의 흐름을 관리한다.
"""

import pygame

from . import SudokuBoard
from .input_dialog import SudokuInputDialog
from .visualizer import SudokuVisualizer


def main() -> None:
    """앱 메인 함수"""
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

        board_data = result

    pygame.quit()
