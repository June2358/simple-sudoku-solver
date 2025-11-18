"""
스도쿠 시각화 모듈

pygame을 사용한 인터랙티브 스도쿠 솔버 GUI입니다.
단계별 해결 과정을 시각화하고 사용자가 탐색할 수 있도록 합니다.
"""

import pygame
from sudoku import SudokuBoard, SudokuSolver
from sudoku.utils import get_conflicting_cells
from sudoku.gui_constants import (
    WHITE, BLACK, GRAY, LIGHT_GRAY, BLUE, GREEN, RED, YELLOW, 
    ORANGE, DARK_BLUE, LIGHT_BLUE, PRIMARY, PRIMARY_DARK, ACCENT, ACCENT_LIGHT,
    ACCENT_YELLOW, ACCENT_YELLOW_LIGHT, CANDIDATE_GRAY, get_fonts,
    VisualizerConstants, InputDialogConstants
)
from typing import Optional, Tuple, List
from copy import deepcopy


# ============================================================================
# Button 클래스
# ============================================================================

class Button:
    """버튼 UI 컴포넌트"""
    
    def __init__(self, x: int, y: int, width: int, height: int, text: str, 
                 color: Tuple[int, int, int], font, text_color: Tuple[int, int, int] = WHITE):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.base_color = color
        self.font = font
        self.text_color = text_color
        self.is_hovered = False
    
    def update_hover(self, mouse_pos: Tuple[int, int]):
        """마우스 호버 상태 업데이트"""
        self.is_hovered = self.rect.collidepoint(mouse_pos)
    
    def is_clicked(self, mouse_pos: Tuple[int, int]) -> bool:
        """버튼이 클릭되었는지 확인"""
        return self.rect.collidepoint(mouse_pos)
    
    def draw(self, screen: pygame.Surface):
        """버튼 그리기"""
        color = self._get_color()
        border_color = tuple(max(0, c - InputDialogConstants.BUTTON_BORDER_DARKEN) for c in color)
        
        # 그림자
        shadow_rect = pygame.Rect(
            self.rect.x + InputDialogConstants.BUTTON_SHADOW_OFFSET,
            self.rect.y + InputDialogConstants.BUTTON_SHADOW_OFFSET,
            self.rect.width,
            self.rect.height
        )
        shadow_surface = pygame.Surface((self.rect.width, self.rect.height))
        shadow_surface.set_alpha(InputDialogConstants.BUTTON_SHADOW_ALPHA)
        shadow_surface.fill(BLACK)
        screen.blit(shadow_surface, shadow_rect.topleft)
        
        # 버튼 배경
        self._draw_rect(screen, color, self.rect)
        
        # 테두리
        self._draw_rect(screen, border_color, self.rect, width=2)
        
        # 텍스트
        text_surface = self.font.render(self.text, True, self.text_color)
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)
    
    def _get_color(self) -> Tuple[int, int, int]:
        """현재 상태에 맞는 색상 반환"""
        if self.is_hovered:
            return tuple(min(255, c + InputDialogConstants.BUTTON_HOVER_BRIGHTNESS) 
                        for c in self.base_color)
        return self.base_color
    
    @staticmethod
    def _draw_rect(screen: pygame.Surface, color: Tuple[int, int, int], 
                   rect: pygame.Rect, width: int = 0):
        """사각형 그리기 (pygame 버전 호환)"""
        # pygame 2.0+ border_radius 지원 확인 (try-except 방식)
        border_radius = InputDialogConstants.BUTTON_BORDER_RADIUS
        try:
            if width == 0:
                pygame.draw.rect(screen, color, rect, border_radius=border_radius)
            else:
                pygame.draw.rect(screen, color, rect, width, border_radius=border_radius)
        except TypeError:
            # 호환성: border_radius 미지원 시 일반 사각형
            pygame.draw.rect(screen, color, rect, width)


# ============================================================================
# SudokuVisualizer 클래스
# ============================================================================

class SudokuVisualizer:
    """pygame을 사용한 스도쿠 시각화"""
    
    def __init__(self, board: SudokuBoard, cell_size: int = VisualizerConstants.DEFAULT_CELL_SIZE, screen=None):
        self.original_board = board
        self.board = SudokuBoard(board.board)
        self.cell_size = cell_size
        self.grid_size = SudokuBoard.SIZE
        self.margin = VisualizerConstants.DEFAULT_MARGIN
        self.window_size = self.grid_size * self.cell_size + 2 * self.margin
        self.side_panel_width = VisualizerConstants.SIDE_PANEL_WIDTH
        
        self._init_screen(screen)
        self._init_fonts()
        self._init_state()
    
    def _init_screen(self, screen: Optional[pygame.Surface]):
        """화면 초기화"""
        if not pygame.get_init():
            pygame.init()
        
        screen_size = (self.window_size + self.side_panel_width, self.window_size)
        if screen is None:
            self.screen = pygame.display.set_mode(screen_size)
        else:
            self.screen = pygame.display.set_mode(screen_size)
        
        pygame.display.set_caption("스도쿠 솔버 - 단계별 시각화")
        pygame.event.clear()
    
    def _init_fonts(self):
        """폰트 초기화"""
        (self.font, self.small_font, self.tiny_font,
         self.medium_font, self.bold_font, self.step_font) = get_fonts()
        self.clock = pygame.time.Clock()
    
    def _init_state(self):
        """상태 초기화"""
        self.running = True
        self.highlighted_cells: List[Tuple[int, int]] = []
        self.last_filled_cell: Optional[Tuple[int, int]] = None
        self.current_step_text = ""
        self.current_technique_name = ""
        self.current_logic_name = ""
        self.step_count = 0
        self.animation_cells: List[Tuple[int, int, float]] = []
        self.animation_time = 0.0
        self.animation_duration = VisualizerConstants.ANIMATION_DURATION
        self.strategy_related_cells: List[Tuple[int, int]] = []
        self.step_history: List[dict] = []
        self.current_step_index = -1
        self.conflicting_cells: List[Tuple[int, int]] = []
        self.autoplay_enabled = False
        self.autoplay_direction = 1
        self.autoplay_interval = VisualizerConstants.AUTOPLAY_INTERVAL
        self.autoplay_timer = 0.0
    
    def draw_grid(self):
        """스도쿠 그리드 그리기"""
        self.screen.fill(WHITE)
        self._draw_box_backgrounds()
        self._draw_grid_lines()
    
    def _draw_box_backgrounds(self):
        """3x3 박스 배경 그리기"""
        box_size = SudokuBoard.BOX_SIZE
        for box_row in range(box_size):
            for box_col in range(box_size):
                x = self.margin + box_col * box_size * self.cell_size
                y = self.margin + box_row * box_size * self.cell_size
                rect = pygame.Rect(x, y, box_size * self.cell_size, box_size * self.cell_size)
                if (box_row + box_col) % 2 == 0:
                    pygame.draw.rect(self.screen, LIGHT_GRAY, rect)
    
    def _draw_grid_lines(self):
        """그리드 선 그리기"""
        box_size = SudokuBoard.BOX_SIZE
        for i in range(self.grid_size + 1):
            line_width = 4 if i % box_size == 0 else 1
            color = BLACK if i % box_size == 0 else GRAY
            
            # 세로선
            x = self.margin + i * self.cell_size
            start_pos = (x, self.margin)
            end_pos = (x, self.margin + self.grid_size * self.cell_size)
            pygame.draw.line(self.screen, color, start_pos, end_pos, line_width)
            
            # 가로선
            y = self.margin + i * self.cell_size
            start_pos = (self.margin, y)
            end_pos = (self.margin + self.grid_size * self.cell_size, y)
            pygame.draw.line(self.screen, color, start_pos, end_pos, line_width)
    
    def draw_numbers(self):
        """숫자 그리기"""
        self.conflicting_cells = get_conflicting_cells(self.board.board)
        
        for i in range(self.grid_size):
            for j in range(self.grid_size):
                x = self.margin + j * self.cell_size
                y = self.margin + i * self.cell_size
                val = self.board.board[i][j]
                
                if val != 0:
                    self._draw_number(x, y, i, j, val)
                else:
                    self._draw_candidates(x, y, i, j)
    
    def _draw_number(self, x: int, y: int, row: int, col: int, val: int):
        """숫자 그리기"""
        color = RED if (row, col) in self.conflicting_cells else self._get_number_color(row, col)
        scale = self._get_animation_scale(row, col)
        
        text = self.font.render(str(val), True, color)
        if scale != 1.0:
            text_width = int(text.get_width() * scale)
            text_height = int(text.get_height() * scale)
            text = pygame.transform.scale(text, (text_width, text_height))
        
        text_rect = text.get_rect(center=(x + self.cell_size // 2, y + self.cell_size // 2))
        self.screen.blit(text, text_rect)
    
    def _get_number_color(self, row: int, col: int) -> Tuple[int, int, int]:
        """숫자 색상 결정"""
        original_val = self.original_board.board[row][col]
        return BLACK if original_val != 0 else ACCENT
    
    def _get_animation_scale(self, row: int, col: int) -> float:
        """애니메이션 스케일 계산"""
        for anim_row, anim_col, progress in self.animation_cells:
            if anim_row == row and anim_col == col:
                if progress < 0.5:
                    return 1.0 + (progress * 2) * 0.3
                else:
                    return 1.3 - ((progress - 0.5) * 2) * 0.3
        return 1.0
    
    def _draw_candidates(self, x: int, y: int, row: int, col: int):
        """후보 숫자 그리기"""
        candidates = sorted(list(self.board.get_candidates(row, col)))
        center = (x + self.cell_size // 2, y + self.cell_size // 2)
        
        if len(candidates) == 0:
            text = self.tiny_font.render("X", True, RED)
            text_rect = text.get_rect(center=center)
            self.screen.blit(text, text_rect)
        elif len(candidates) <= 6:
            cand_text = " ".join(str(c) for c in candidates)
            text = self.tiny_font.render(cand_text, True, CANDIDATE_GRAY)
            text_rect = text.get_rect(center=center)
            self.screen.blit(text, text_rect)
        else:
            text = self.tiny_font.render(f"({len(candidates)})", True, CANDIDATE_GRAY)
            text_rect = text.get_rect(center=center)
            self.screen.blit(text, text_rect)
    
    def _draw_conflict_cells(self, margin_x: int, margin_y: int):
        """모순 셀 배경 표시"""
        for row, col in self.conflicting_cells:
            x = margin_x + col * self.cell_size
            y = margin_y + row * self.cell_size
            conflict_surface = pygame.Surface((self.cell_size - 2, self.cell_size - 2))
            conflict_surface.set_alpha(128)
            conflict_surface.fill(RED)
            self.screen.blit(conflict_surface, (x + 1, y + 1))
    
    def draw_highlights(self):
        """하이라이트 그리기"""
        self._draw_conflict_cells(self.margin, self.margin)
        self._draw_strategy_highlights()
        self._draw_filled_cell_highlights()
    
    def _draw_strategy_highlights(self):
        """전략 관련 셀 하이라이트"""
        for row, col in self.strategy_related_cells:
            if (row, col) not in self.conflicting_cells:
                x = self.margin + col * self.cell_size
                y = self.margin + row * self.cell_size
                strategy_surface = pygame.Surface((self.cell_size - 2, self.cell_size - 2))
                strategy_surface.set_alpha(100)
                strategy_surface.fill(ACCENT_YELLOW_LIGHT)
                self.screen.blit(strategy_surface, (x + 1, y + 1))
    
    def _draw_filled_cell_highlights(self):
        """채워진 셀 하이라이트"""
        cells_to_highlight = self.highlighted_cells if self.highlighted_cells else (
            [self.last_filled_cell] if self.last_filled_cell else []
        )
        
        for row, col in cells_to_highlight:
            if (row, col) not in self.conflicting_cells:
                x = self.margin + col * self.cell_size
                y = self.margin + row * self.cell_size
                highlight_rect = pygame.Rect(x + 2, y + 2, self.cell_size - 4, self.cell_size - 4)
                pygame.draw.rect(self.screen, ACCENT, highlight_rect, 3)
    
    def draw_side_panel(self, total_steps: int = 0):
        """사이드 패널 그리기"""
        panel_x = self.window_size + VisualizerConstants.PANEL_X_OFFSET
        y = VisualizerConstants.TITLE_Y_OFFSET
        
        y = self._draw_title(panel_x, y)
        y = self._draw_step_info(panel_x, y)
        y = self._draw_technique_info(panel_x, y)
        y = self._draw_status_info(panel_x, y)
        self._draw_controls(panel_x, y)
    
    def _draw_title(self, panel_x: int, y: int) -> int:
        """제목 그리기"""
        title = self.bold_font.render("스도쿠 솔버", True, PRIMARY_DARK)
        self.screen.blit(title, (panel_x, y))
        y += 40
        return self._draw_separator(panel_x, y)
    
    def _draw_step_info(self, panel_x: int, y: int) -> int:
        """단계 정보 그리기"""
        if len(self.step_history) == 0:
            return y
        
        header = self.bold_font.render("단계", True, PRIMARY_DARK)
        self.screen.blit(header, (panel_x, y))
        y += header.get_height() + 6
        
        step_num = self.current_step_index + 1
        total_steps = len(self.step_history)
        
        step_text = f"{step_num} / {total_steps}"
        step_rendered = self.step_font.render(step_text, True, BLACK)
        self.screen.blit(step_rendered, (panel_x, y))
        y += self.step_font.get_linesize()
        
        return self._draw_separator(panel_x, y)
    
    def _draw_technique_info(self, panel_x: int, y: int) -> int:
        """전략 정보 그리기"""
        if not (self.current_technique_name or self.current_step_text):
            return y
        
        header = self.bold_font.render("적용된 전략", True, PRIMARY_DARK)
        self.screen.blit(header, (panel_x, y))
        y += header.get_height() + 6
        
        if self.current_technique_name:
            strategy_rendered = self.step_font.render(self.current_technique_name, True, BLACK)
            self.screen.blit(strategy_rendered, (panel_x, y))
            y += self.step_font.get_linesize()
        
        location_text = self.current_step_text or "위치 정보 없음"
        max_width = self.side_panel_width - 20
        lines = self._wrap_text(location_text, self.medium_font, max_width)
        line_height = self.medium_font.get_linesize()
        for line in lines:
            text_surface = self.medium_font.render(line, True, GRAY)
            self.screen.blit(text_surface, (panel_x, y))
            y += line_height
        
        remaining_text = f"남은 빈 칸: {len(self.board.get_empty_cells())}개"
        remaining_rendered = self.medium_font.render(remaining_text, True, GRAY)
        self.screen.blit(remaining_rendered, (panel_x, y))
        y += self.medium_font.get_linesize()
        
        return self._draw_separator(panel_x, y)

    def _draw_status_info(self, panel_x: int, y: int) -> int:
        """상태 정보 그리기"""
        header = self.bold_font.render("상태", True, PRIMARY_DARK)
        self.screen.blit(header, (panel_x, y))
        y += header.get_height() + 6
        
        body_font = self.medium_font
        
        conflict_count = len(self.conflicting_cells)
        if conflict_count > 0:
            conflict_text = f"모순: {conflict_count}개"
            conflict_rendered = body_font.render(conflict_text, True, RED)
            self.screen.blit(conflict_rendered, (panel_x, y))
            y += body_font.get_linesize()
        else:
            ok_text = body_font.render("모순 없음", True, GRAY)
            self.screen.blit(ok_text, (panel_x, y))
            y += body_font.get_linesize()
        
        autoplay_text = f"자동재생: {'ON' if self.autoplay_enabled else 'OFF'}"
        autoplay_color = PRIMARY_DARK if self.autoplay_enabled else GRAY
        autoplay_rendered = body_font.render(autoplay_text, True, autoplay_color)
        self.screen.blit(autoplay_rendered, (panel_x, y))
        y += body_font.get_linesize()
        
        return self._draw_separator(panel_x, y)
    
    def _draw_controls(self, panel_x: int, y: int):
        """조작법 그리기"""
        header = self.bold_font.render("조작법", True, PRIMARY_DARK)
        self.screen.blit(header, (panel_x, y))
        y += header.get_height() + 6
        
        controls = [
            "←/→ 또는 ↑/↓: 이전/다음 단계",
            "마우스 휠: 단계 이동",
            "Space: 자동재생 켜기/끄기",
            "ESC: 수정 모드로 돌아가기"
        ]
        line_height = self.small_font.get_linesize()
        for control in controls:
            text = self.small_font.render(control, True, GRAY)
            self.screen.blit(text, (panel_x, y))
            y += line_height
    
    def _draw_separator(self, panel_x: int, y: int) -> int:
        """구분선 그리기"""
        pygame.draw.line(self.screen, LIGHT_GRAY, 
                        (panel_x, y), 
                        (panel_x + self.side_panel_width - 20, y), 1)
        return y + VisualizerConstants.SECTION_SPACING
    
    @staticmethod
    def _wrap_text(text: str, font, max_width: int) -> List[str]:
        """텍스트를 주어진 너비에 맞춰 줄바꿈"""
        if not text:
            return []
        
        words = text.split()
        if not words:
            return []
        
        lines = []
        current_line = words[0]
        
        for word in words[1:]:
            test_line = f"{current_line} {word}"
            if font.size(test_line)[0] <= max_width:
                current_line = test_line
            else:
                lines.append(current_line)
                current_line = word
        
        lines.append(current_line)
        return lines
    
    def handle_events(self):
        """이벤트 처리"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                return None
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return "edit"
                elif event.key in (pygame.K_RIGHT, pygame.K_DOWN):
                    self._stop_autoplay()
                    self.autoplay_direction = 1
                    self._navigate_step(1)
                elif event.key in (pygame.K_LEFT, pygame.K_UP):
                    self._stop_autoplay()
                    self.autoplay_direction = -1
                    self._navigate_step(-1)
                elif event.key == pygame.K_SPACE:
                    self._toggle_autoplay()
            elif event.type == pygame.MOUSEWHEEL:
                if event.y > 0:
                    self._stop_autoplay()
                    self.autoplay_direction = -1
                    self._navigate_step(-1)
                elif event.y < 0:
                    self._stop_autoplay()
                    self.autoplay_direction = 1
                    self._navigate_step(1)
    
    def _navigate_step(self, direction: int) -> bool:
        """단계 탐색"""
        new_index = self.current_step_index + direction
        if 0 <= new_index < len(self.step_history):
            self.current_step_index = new_index
            self.load_step(self.current_step_index)
            self._start_animation()
            return True
        return False

    def _toggle_autoplay(self):
        """자동 재생 토글"""
        if len(self.step_history) <= 1:
            return
        self.autoplay_enabled = not self.autoplay_enabled
        self.autoplay_timer = 0.0
        if self.autoplay_enabled and not self._can_autoplay_direction(self.autoplay_direction):
            # 반대 방향으로 전환 시도
            opposite = -self.autoplay_direction
            if self._can_autoplay_direction(opposite):
                self.autoplay_direction = opposite
            else:
                self.autoplay_enabled = False

    def _can_autoplay_direction(self, direction: int) -> bool:
        """주어진 방향으로 이동 가능한지 확인"""
        new_index = self.current_step_index + direction
        return 0 <= new_index < len(self.step_history)

    def _stop_autoplay(self):
        """자동 재생 중지"""
        if self.autoplay_enabled:
            self.autoplay_enabled = False
            self.autoplay_timer = 0.0
    def save_step(self, step_text: str, filled_cell: Optional[Tuple[int, int]] = None,
                  highlighted: List[Tuple[int, int]] = None, technique_name: str = "",
                  logic_name: Optional[str] = None):
        """현재 단계 상태 저장"""
        step_data = {
            'text': step_text,
            'filled_cell': filled_cell,
            'highlighted': highlighted or [],
            'technique_name': technique_name,
            'logic_name': logic_name or technique_name,
            'board_state': [[self.board.board[i][j] for j in range(SudokuBoard.SIZE)] 
                           for i in range(SudokuBoard.SIZE)],
            'candidates_state': [[self.board.candidates[i][j].copy() 
                               for j in range(SudokuBoard.SIZE)] 
                               for i in range(SudokuBoard.SIZE)]
        }
        self.step_history.append(step_data)
    
    def load_step(self, step_index: int):
        """저장된 단계 상태 불러오기"""
        if not (0 <= step_index < len(self.step_history)):
            return
        
        self.current_step_index = step_index
        step_data = self.step_history[step_index]
        self.current_step_text = step_data['text']
        self.current_technique_name = step_data.get('technique_name', '')
        self.current_logic_name = step_data.get('logic_name', self.current_technique_name)
        self.last_filled_cell = step_data['filled_cell']
        self.highlighted_cells = step_data['highlighted']
        self.strategy_related_cells = []
        
        # 보드 상태 복원
        for i in range(SudokuBoard.SIZE):
            for j in range(SudokuBoard.SIZE):
                self.board.board[i][j] = step_data['board_state'][i][j]
                self.board.candidates[i][j] = step_data['candidates_state'][i][j]
    
    def _start_animation(self):
        """애니메이션 시작"""
        self.animation_time = 0.0
        self.animation_cells = []
        
        cells = self.highlighted_cells if self.highlighted_cells else (
            [self.last_filled_cell] if self.last_filled_cell else []
        )
        for row, col in cells:
            self.animation_cells.append((row, col, 0.0))
    
    def _update_animation(self, dt: float):
        """애니메이션 업데이트"""
        if not self.animation_cells:
            return
        
        self.animation_time += dt
        
        updated_cells = []
        for row, col, _ in self.animation_cells:
            new_progress = min(1.0, self.animation_time / self.animation_duration)
            updated_cells.append((row, col, new_progress))
        
        self.animation_cells = updated_cells
        
        if self.animation_time >= self.animation_duration:
            self.animation_cells = []

    def _update_autoplay(self, dt: float):
        """자동 재생 업데이트"""
        if not self.autoplay_enabled:
            return
        if len(self.step_history) <= 1:
            self._stop_autoplay()
            return
        self.autoplay_timer += dt
        if self.autoplay_timer < self.autoplay_interval:
            return
        self.autoplay_timer = 0.0
        if not self._navigate_step(self.autoplay_direction):
            self._stop_autoplay()
    
    def solve_with_visualization(self):
        """시각화와 함께 스도쿠 해결"""
        self.step_history.clear()
        self.step_count = 0
        self.current_step_index = -1
        
        solver = SudokuSolver(self.board)
        self._show_loading_screen()
        
        def on_step_callback(technique_name: str, filled_cell: Optional[Tuple[int, int]], 
                            highlighted: List[Tuple[int, int]]):
            if technique_name == "초기 상태":
                return
            
            self.step_count += 1
            self.board = deepcopy(solver.board)
            
            filled_cells = highlighted if highlighted else ([filled_cell] if filled_cell else [])
            is_final_move = solver.board.is_complete()
            if is_final_move:
                technique_display = f"{technique_name} (완성)" if technique_name else "완성"
            else:
                technique_display = technique_name
            
            step_text = self._format_step_text(filled_cells)
            self.save_step(step_text, filled_cells[0] if filled_cells else None, 
                          filled_cells, technique_display, logic_name=technique_name)
            
            if self.step_count % VisualizerConstants.LOADING_UPDATE_INTERVAL == 0:
                self._update_loading_screen()
        
        solver.solve(on_step=on_step_callback)
        self.board = deepcopy(solver.board)
        return self.board.is_complete()
    
    def _format_step_text(self, filled_cells: List[Tuple[int, int]]) -> str:
        """위치 정보를 위한 텍스트 포맷"""
        if not filled_cells:
            return "위치 정보 없음"
        
        if len(filled_cells) == 1:
            row, col = filled_cells[0]
            value = self.board.board[row][col]
            return f"위치: R{row+1}C{col+1} (값 {value})"
        
        locations = [
            f"R{row+1}C{col+1}"
            for row, col in filled_cells[:VisualizerConstants.MAX_DISPLAYED_CELLS]
        ]
        location_text = ", ".join(locations)
        if len(filled_cells) > VisualizerConstants.MAX_DISPLAYED_CELLS:
            remaining = len(filled_cells) - VisualizerConstants.MAX_DISPLAYED_CELLS
            location_text += f" 외 {remaining}개"
        return f"위치: {location_text}"
    
    def _show_loading_screen(self):
        """로딩 화면 표시"""
        loading_text = self.small_font.render("단계 계산 중...", True, BLACK)
        loading_rect = loading_text.get_rect(center=(self.window_size // 2, self.window_size // 2))
        self.screen.fill(WHITE)
        self.screen.blit(loading_text, loading_rect)
        pygame.display.flip()
        pygame.event.clear()
    
    def _update_loading_screen(self):
        """로딩 화면 업데이트"""
        loading_text = self.small_font.render(
            f"단계 계산 중... ({self.step_count}단계)", True, BLACK)
        loading_rect = loading_text.get_rect(center=(self.window_size // 2, self.window_size // 2))
        self.screen.fill(WHITE)
        self.screen.blit(loading_text, loading_rect)
        pygame.display.flip()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
    
    def run(self):
        """메인 루프"""
        solved = self.solve_with_visualization()
        
        if len(self.step_history) == 0:
            self.save_step("초기 상태", None, [], "초기 상태", logic_name="초기 상태")
        
        if len(self.step_history) > 0:
            self.load_step(0)
            self._start_animation()
        else:
            self.current_step_text = "초기 상태"
            self.current_step_index = 0
        
        while self.running:
            dt = self.clock.tick(VisualizerConstants.FPS) / 1000.0
            
            result = self.handle_events()
            if result == "edit":
                return self.original_board.board
            
            self._update_autoplay(dt)
            self._update_animation(dt)
            
            self.draw_grid()
            self.draw_highlights()
            self.draw_numbers()
            self.draw_side_panel()
            
            pygame.display.flip()
        
        return None

