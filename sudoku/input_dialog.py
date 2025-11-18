"""
스도쿠 입력 다이얼로그 모듈

사용자가 스도쿠 문제를 입력하거나 불러올 수 있는 GUI 다이얼로그입니다.
"""

import pygame
import random
from sudoku import SudokuBoard
from sudoku.utils import get_puzzles_by_difficulty, get_all_puzzles, get_available_difficulties, get_conflicting_cells
from sudoku.gui_constants import (
    WHITE, BLACK, GRAY, LIGHT_GRAY, BLUE, GREEN, RED, YELLOW, 
    ORANGE, DARK_BLUE, LIGHT_BLUE, PRIMARY, PRIMARY_DARK, ACCENT, ACCENT_LIGHT,
    ACCENT_YELLOW, ACCENT_YELLOW_LIGHT, CANDIDATE_GRAY, get_fonts,
    VisualizerConstants, InputDialogConstants
)
from sudoku.visualizer import Button
from typing import Optional, Tuple, List


class SudokuInputDialog:
    """스도쿠 문제 입력 다이얼로그"""
    
    def __init__(self, initial_board=None, screen=None):
        self._init_pygame()
        self._init_screen(screen)
        self._init_fonts()
        self._init_layout()
        self._init_state(initial_board)
        self._init_buttons()
    
    def _init_pygame(self):
        """pygame 초기화"""
        if not pygame.get_init():
            pygame.init()
    
    def _init_screen(self, screen: Optional[pygame.Surface]):
        """화면 초기화"""
        screen_size = (InputDialogConstants.WIDTH, InputDialogConstants.HEIGHT)
        if screen is None:
            self.screen = pygame.display.set_mode(screen_size)
        else:
            self.screen = pygame.display.set_mode(screen_size)
        
        pygame.display.set_caption("스도쿠 문제 입력")
        pygame.event.clear()
    
    def _init_fonts(self):
        """폰트 초기화"""
        font, small_font, _, _, bold_font, _ = get_fonts()
        self.font = font
        self.small_font = small_font
        self.bold_font = bold_font
        self.title_font = self._create_title_font()
    
    def _create_title_font(self):
        """제목 폰트 생성"""
        korean_fonts = ["malgun gothic", "맑은 고딕", "NanumGothic", "나눔고딕", "gulim", "굴림"]
        
        for font_name in korean_fonts:
            font = self._try_create_font(font_name, InputDialogConstants.TITLE_FONT_SIZE)
            if font is not None:
                return font
        
        # 모든 폰트 실패 시 기본 폰트
        return pygame.font.SysFont("malgun gothic", InputDialogConstants.TITLE_FONT_SIZE)
    
    @staticmethod
    def _try_create_font(font_name: str, size: int):
        """폰트 생성 시도 (에러 없이 처리)"""
        font = pygame.font.SysFont(font_name, size)
        test_surface = font.render(InputDialogConstants.FONT_TEST_STRING, True, BLACK)
        # 렌더링이 성공하고 너비가 0보다 크면 유효한 폰트
        if test_surface.get_width() > 0:
            return font
        return None
    
    def _init_layout(self):
        """레이아웃 초기화"""
        self.cell_size = InputDialogConstants.CELL_SIZE
        self.margin = InputDialogConstants.MARGIN
        self.grid_width = SudokuBoard.SIZE * self.cell_size
        self.grid_start_x = self.margin
        self.grid_start_y = InputDialogConstants.GRID_START_Y
        self.panel_x = (self.grid_start_x + self.grid_width +
                        InputDialogConstants.PANEL_GAP)
        self.panel_inner_width = InputDialogConstants.PANEL_WIDTH - 2 * InputDialogConstants.PANEL_PADDING
    
    def _init_state(self, initial_board):
        """상태 초기화"""
        if initial_board:
            self.board = [row[:] for row in initial_board]
        else:
            self.board = [[0] * SudokuBoard.SIZE for _ in range(SudokuBoard.SIZE)]
        
        self.selected_cell = None
        self.running = True
        self.validation_error = None
        self.conflicting_cells: List[Tuple[int, int]] = []
        self.instructions_bottom = self.grid_start_y
    
    def _init_buttons(self):
        """버튼 초기화"""
        difficulties = get_available_difficulties()
        num_difficulties = len(difficulties)
        
        button_spacing = InputDialogConstants.BUTTON_SPACING
        
        button_start_y = self.grid_start_y
        button_colors = self._get_button_colors(num_difficulties)
        cols = min(InputDialogConstants.BUTTONS_PER_ROW, num_difficulties) if num_difficulties else 0
        rows = (num_difficulties + cols - 1) // cols if cols else 0
        effective_button_width = self._compute_panel_button_width(cols, button_spacing)
        
        self.buttons = []
        for idx, (difficulty, color) in enumerate(zip(difficulties, button_colors)):
            row = idx // cols
            col = idx % cols
            row_remaining = num_difficulties - row * cols
            row_cols = min(cols, row_remaining)
            row_width = (row_cols * effective_button_width +
                         (row_cols - 1) * button_spacing) if row_cols > 0 else 0
            row_start_x = self.panel_x + InputDialogConstants.PANEL_PADDING + \
                max(0, (self.panel_inner_width - row_width) // 2)
            x = row_start_x + col * (effective_button_width + button_spacing)
            y = button_start_y + row * (InputDialogConstants.BUTTON_HEIGHT +
                                        InputDialogConstants.BUTTON_ROW_SPACING)
            button = Button(x, y, effective_button_width, InputDialogConstants.BUTTON_HEIGHT,
                            difficulty, color, self.small_font)
            self.buttons.append(button)
        
        if rows == 0:
            buttons_bottom = button_start_y
        else:
            last_row_offset = (rows - 1) * (InputDialogConstants.BUTTON_HEIGHT +
                                            InputDialogConstants.BUTTON_ROW_SPACING)
            buttons_bottom = button_start_y + last_row_offset + InputDialogConstants.BUTTON_HEIGHT
        
        start_y = buttons_bottom + 20
        start_x = self.panel_x + InputDialogConstants.PANEL_PADDING
        self.start_button = Button(
            start_x,
            start_y,
            self.panel_inner_width,
            InputDialogConstants.BUTTON_HEIGHT + 4,
            "풀이 시작",
            PRIMARY_DARK,
            self.small_font
        )
    def _compute_panel_button_width(self, cols: int, spacing: int) -> int:
        """패널 내부에서 버튼 너비 계산"""
        if cols <= 0:
            return 0
        total_spacing = (cols - 1) * spacing
        return max(70, (self.panel_inner_width - total_spacing) // cols)
    
    def _get_button_colors(self, num_difficulties: int) -> List[Tuple[int, int, int]]:
        """버튼 색상 리스트 생성"""
        base_colors = [
            ACCENT, PRIMARY, ORANGE, RED,
            (150, 50, 150), (50, 50, 50)
        ]
        
        if num_difficulties > len(base_colors):
            multiplier = (num_difficulties // len(base_colors)) + 1
            base_colors = base_colors * multiplier
        
        return base_colors[:num_difficulties]
    
    def draw(self):
        """화면 그리기"""
        self.screen.fill(WHITE)
        self._draw_title()
        self._draw_grid()
        self._draw_panel_background()
        self._draw_buttons()
        self._draw_start_button()
        self._draw_instructions()
        self._draw_validation_error()
        pygame.display.flip()
    
    def _draw_panel_background(self):
        """우측 패널 배경"""
        panel_height = SudokuBoard.SIZE * self.cell_size
        panel_rect = pygame.Rect(
            self.panel_x,
            self.grid_start_y,
            InputDialogConstants.PANEL_WIDTH,
            panel_height
        )
        pygame.draw.rect(self.screen, LIGHT_GRAY, panel_rect, border_radius=10)
        inner_rect = panel_rect.inflate(-8, -8)
        pygame.draw.rect(self.screen, WHITE, inner_rect, border_radius=10)
    
    def _draw_title(self):
        """제목 그리기"""
        title = self.bold_font.render("스도쿠 문제 입력", True, PRIMARY_DARK)
        title_rect = title.get_rect(center=(InputDialogConstants.WIDTH // 2, 40))
        self.screen.blit(title, title_rect)
    
    def _draw_grid(self):
        """그리드 그리기"""
        self._draw_grid_lines()
        self._draw_conflict_cells()
        self._draw_numbers()
        self._draw_selected_cell()
    
    def _draw_grid_lines(self):
        """그리드 선 그리기"""
        box_size = SudokuBoard.BOX_SIZE
        for i in range(SudokuBoard.SIZE + 1):
            line_width = 3 if i % box_size == 0 else 1
            color = BLACK if i % box_size == 0 else GRAY
            
            # 세로선
            x = self.grid_start_x + i * self.cell_size
            pygame.draw.line(self.screen, color,
                           (x, self.grid_start_y),
                           (x, self.grid_start_y + SudokuBoard.SIZE * self.cell_size),
                           line_width)
            
            # 가로선
            y = self.grid_start_y + i * self.cell_size
            pygame.draw.line(self.screen, color,
                           (self.grid_start_x, y),
                           (self.grid_start_x + SudokuBoard.SIZE * self.cell_size, y),
                           line_width)
    
    def _draw_conflict_cells(self):
        """모순 셀 그리기"""
        self.conflicting_cells = get_conflicting_cells(self.board)
        
        for row, col in self.conflicting_cells:
            x = self.grid_start_x + col * self.cell_size
            y = self.grid_start_y + row * self.cell_size
            conflict_surface = pygame.Surface((self.cell_size - 2, self.cell_size - 2))
            conflict_surface.set_alpha(128)
            conflict_surface.fill(RED)
            self.screen.blit(conflict_surface, (x + 1, y + 1))
    
    def _draw_numbers(self):
        """숫자 그리기"""
        for i in range(SudokuBoard.SIZE):
            for j in range(SudokuBoard.SIZE):
                if self.board[i][j] != 0:
                    x = self.grid_start_x + j * self.cell_size
                    y = self.grid_start_y + i * self.cell_size
                    color = RED if (i, j) in self.conflicting_cells else BLACK
                    text = self.font.render(str(self.board[i][j]), True, color)
                    text_rect = text.get_rect(center=(x + self.cell_size // 2, y + self.cell_size // 2))
                    self.screen.blit(text, text_rect)
    
    def _draw_selected_cell(self):
        """선택된 셀 하이라이트"""
        if not self.selected_cell:
            return
        
        row, col = self.selected_cell
        x = self.grid_start_x + col * self.cell_size
        y = self.grid_start_y + row * self.cell_size
        
        rect = pygame.Rect(x + 3, y + 3, self.cell_size - 6, self.cell_size - 6)
        if (row, col) in self.conflicting_cells:
            pygame.draw.rect(self.screen, RED, rect, 3)
        else:
            pygame.draw.rect(self.screen, ACCENT_YELLOW, rect, 3)
            highlight_surface = pygame.Surface((self.cell_size - 6, self.cell_size - 6))
            highlight_surface.set_alpha(60)
            highlight_surface.fill(ACCENT_YELLOW_LIGHT)
            self.screen.blit(highlight_surface, (x + 3, y + 3))
    
    def _draw_buttons(self):
        """버튼 그리기"""
        mouse_pos = pygame.mouse.get_pos()
        for button in self.buttons:
            button.update_hover(mouse_pos)
            button.draw(self.screen)
    
    def _draw_start_button(self):
        """풀이 시작 버튼 그리기"""
        mouse_pos = pygame.mouse.get_pos()
        self.start_button.update_hover(mouse_pos)
        self.start_button.draw(self.screen)
    
    def _draw_instructions(self):
        """안내 텍스트 그리기"""
        y_pos = self.start_button.rect.bottom + 25
        text_x = self.panel_x + InputDialogConstants.PANEL_PADDING
        
        sections = [
            ("입력", [
                "마우스로 칸을 선택하세요",
                "숫자 1-9 입력, 0/Delete 삭제",
                "화살표 키로 이동"
            ]),
            ("문제 불러오기", [
                "난이도 버튼 클릭 시 샘플 퍼즐 불러오기",
                "C 또는 R 키로 전체 초기화"
            ]),
            ("풀이 시작 / 종료", [
                "풀이 시작 버튼 또는 Enter/S 키",
                "ESC 키로 창 종료"
            ])
        ]
        
        for section_title, instructions in sections:
            title_text = self.small_font.render(section_title, True, DARK_BLUE)
            self.screen.blit(title_text, (text_x, y_pos))
            y_pos += InputDialogConstants.SECTION_TITLE_SPACING
            
            for instruction in instructions:
                text = self.small_font.render(f"• {instruction}", True, GRAY)
                self.screen.blit(text, (text_x, y_pos))
                y_pos += InputDialogConstants.INSTRUCTION_SPACING
            
            y_pos += InputDialogConstants.SECTION_GAP
        
        self.instructions_bottom = y_pos
    
    def _draw_validation_error(self):
        """검증 에러 메시지 그리기"""
        if not self.validation_error:
            return
        
        anchor = max(self.instructions_bottom, self.start_button.rect.bottom)
        y_pos = anchor + 10
        
        error_lines = self.validation_error.split('\n')
        for line in error_lines:
            error_text = self.small_font.render(line, True, RED)
            error_rect = error_text.get_rect(center=(
                self.panel_x + InputDialogConstants.PANEL_WIDTH // 2,
                y_pos))
            self.screen.blit(error_text, error_rect)
            y_pos += InputDialogConstants.ERROR_MESSAGE_SPACING
    
    def handle_events(self):
        """이벤트 처리"""
        mouse_pos = pygame.mouse.get_pos()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                return None
            
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    result = self._handle_mouse_click(event.pos)
                    if result is not None:
                        return result
            
            elif event.type == pygame.KEYDOWN:
                result = self._handle_keydown(event)
                if result is not None:
                    return result
        
        return None
    
    def _handle_mouse_click(self, mouse_pos: Tuple[int, int]) -> Optional[List[List[int]]]:
        """마우스 클릭 처리"""
        # 버튼 클릭 확인
        for i, button in enumerate(self.buttons):
            if button.is_clicked(mouse_pos):
                self._load_difficulty_puzzle(i)
                return None
        
        if self.start_button.is_clicked(mouse_pos):
            return self._handle_start()
        
        # 그리드 클릭 확인
        if self._is_point_in_grid(mouse_pos):
            self._select_cell(mouse_pos)
    
    def _load_difficulty_puzzle(self, button_index: int):
        """난이도별 퍼즐 불러오기"""
        difficulties = get_available_difficulties()
        if 0 <= button_index < len(difficulties):
            puzzles = get_puzzles_by_difficulty(difficulties[button_index])
            random_puzzle = random.choice(puzzles)
            self.board = [row[:] for row in random_puzzle]
            self.selected_cell = None
            self.validation_error = None
            self.draw()
            pygame.display.flip()
    
    def _is_point_in_grid(self, pos: Tuple[int, int]) -> bool:
        """포인트가 그리드 내부인지 확인"""
        mouse_x, mouse_y = pos
        return (self.grid_start_x <= mouse_x < self.grid_start_x + SudokuBoard.SIZE * self.cell_size and
                self.grid_start_y <= mouse_y < self.grid_start_y + SudokuBoard.SIZE * self.cell_size)
    
    def _select_cell(self, mouse_pos: Tuple[int, int]):
        """셀 선택"""
        mouse_x, mouse_y = mouse_pos
        col = (mouse_x - self.grid_start_x) // self.cell_size
        row = (mouse_y - self.grid_start_y) // self.cell_size
        self.selected_cell = (row, col)
    
    def _handle_keydown(self, event) -> Optional[List[List[int]]]:
        """키 입력 처리"""
        if self._is_start_key(event.key):
            return self._handle_start()
        
        if event.key == pygame.K_ESCAPE:
            self.running = False
            return None
        
        if event.key in (pygame.K_r, pygame.K_c):
            self._reset_board()
            return None
        
        if event.key == pygame.K_l:
            self._load_random_puzzle()
            return None
        
        if self.selected_cell:
            self._handle_cell_input(event)
        
        return None
    
    def _is_start_key(self, key: int) -> bool:
        """시작 키인지 확인"""
        return key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_s)
    
    def _handle_start(self) -> Optional[List[List[int]]]:
        """시작 처리"""
        board = self.get_board()
        test_board = SudokuBoard(board)
        
        if not test_board.is_valid():
            self.validation_error = "입력된 스도쿠에 모순이 있습니다!\n(같은 행/열/박스에 중복된 숫자가 있습니다)"
            return None
        
        self.validation_error = None
        self.draw()
        pygame.display.flip()
        pygame.event.clear()
        pygame.time.wait(100)
        self.running = False
        return board
    
    def _reset_board(self):
        """보드 초기화"""
        self.board = [[0] * SudokuBoard.SIZE for _ in range(SudokuBoard.SIZE)]
        self.selected_cell = None
        self.validation_error = None
    
    def _load_random_puzzle(self):
        """랜덤 퍼즐 불러오기"""
        all_puzzles = get_all_puzzles()
        if all_puzzles:
            random_puzzle = random.choice(all_puzzles)
            self.board = [row[:] for row in random_puzzle]
            self.selected_cell = None
            self.validation_error = None
    
    def _handle_cell_input(self, event):
        """셀 입력 처리"""
        row, col = self.selected_cell
        
        if event.key in (pygame.K_DELETE, pygame.K_BACKSPACE):
            self.board[row][col] = 0
            self.validation_error = None
        elif pygame.K_1 <= event.key <= pygame.K_9:
            self.board[row][col] = event.key - pygame.K_0
            self.validation_error = None
        elif pygame.K_KP1 <= event.key <= pygame.K_KP9:
            self.board[row][col] = event.key - pygame.K_KP0
            self.validation_error = None
        elif event.key in (pygame.K_0, pygame.K_KP0):
            self.board[row][col] = 0
            self.validation_error = None
        else:
            self._handle_arrow_keys(event, row, col)
    
    def _handle_arrow_keys(self, event, row: int, col: int):
        """화살표 키 처리"""
        if event.key == pygame.K_UP and row > 0:
            self.selected_cell = (row - 1, col)
        elif event.key == pygame.K_DOWN and row < SudokuBoard.SIZE - 1:
            self.selected_cell = (row + 1, col)
        elif event.key == pygame.K_LEFT and col > 0:
            self.selected_cell = (row, col - 1)
        elif event.key == pygame.K_RIGHT and col < SudokuBoard.SIZE - 1:
            self.selected_cell = (row, col + 1)
    
    def get_board(self):
        """입력된 보드 반환"""
        return self.board
    
    def run(self):
        """입력 다이얼로그 실행"""
        clock = pygame.time.Clock()
        
        while self.running:
            result = self.handle_events()
            if result is not None:
                return result
            
            self.draw()
            clock.tick(VisualizerConstants.FPS)
        
        return None

