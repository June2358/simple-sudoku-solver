"""
GUI 상수 및 공통 유틸리티 모듈

pygame 시각화에 사용되는 색상 팔레트, 폰트 설정, GUI 상수와
그리드/모순 셀 그리기와 같은 공통 GUI 유틸리티를 제공합니다.
"""

from typing import List, Tuple

import pygame

from .board import SudokuBoard

# ============================================================================
# 색상 팔레트
# ============================================================================

# 모던한 색상 팔레트
# 주조색 (Primary) - 차분한 파란색 계열
PRIMARY = (59, 130, 246)  # #3B82F6 - 밝은 파란색
PRIMARY_DARK = (37, 99, 235)  # #2563EB - 진한 파란색
PRIMARY_LIGHT = (147, 197, 253)  # #93C5FD - 연한 파란색

# 강조색 (Accent) - 부드러운 녹색/노란색
ACCENT = (34, 197, 94)  # #22C55E - 밝은 녹색
ACCENT_LIGHT = (187, 247, 208)  # #BBF7D0 - 연한 녹색
ACCENT_YELLOW = (250, 204, 21)  # #FACC15 - 부드러운 노란색
ACCENT_YELLOW_LIGHT = (254, 240, 138)  # #FEF08A - 연한 노란색

# 기본 색상
WHITE = (255, 255, 255)
BLACK = (20, 20, 20)  # 순수 검정보다 부드러운 검정
GRAY = (107, 114, 128)  # #6B7280 - 중간 회색
LIGHT_GRAY = (229, 231, 235)  # #E5E7EB - 연한 회색
CANDIDATE_GRAY = (156, 163, 175)  # #9CA3AF - 후보 숫자용 연한 회색

# 기능 색상
RED = (239, 68, 68)  # #EF4444 - 부드러운 빨강
ORANGE = (249, 115, 22)  # #F97316 - 부드러운 주황

# 하위 호환성을 위한 별칭
BLUE = PRIMARY
GREEN = ACCENT
YELLOW = ACCENT_YELLOW
DARK_BLUE = PRIMARY_DARK
LIGHT_BLUE = PRIMARY_LIGHT


def _find_korean_font_name() -> str | None:
    """
    시스템에 설치된 한글 폰트 중 우선순위에 따라 하나를 선택해 이름을 반환.
    실패하면 None 반환.
    """
    import pygame

    korean_fonts = [
        "Pretendard",
        "Noto Sans KR",
        "Noto Sans CJK KR",
        "malgun gothic",
        "맑은 고딕",
        "NanumGothic",
        "나눔고딕",
        "gulim",
        "굴림",
    ]

    for font_name in korean_fonts:
        try:
            test_font = pygame.font.SysFont(font_name, 16)
            test_surface = test_font.render("테스트", True, (0, 0, 0))
            if test_surface.get_width() > 0:
                return font_name
        except Exception:
            continue
    return None


def get_fonts():
    """
    pygame 폰트 객체 생성.
    모던한 한글 폰트를 시도하고, 실패 시 기본 폰트 사용.

    Returns:
        tuple: (font, small_font, tiny_font, medium_font, bold_font, step_font)
    """
    font_name = _find_korean_font_name()

    font = None
    small_font = None
    tiny_font = None
    medium_font = None
    bold_font = None
    step_font = None

    # 폰트 크기 조정
    font_size = 36  # 숫자용 큰 폰트
    small_font_size = 16  # 사이드 패널용 (가독성 향상)
    tiny_font_size = 10  # 후보 표시용 (더 작게)
    medium_font_size = 18  # 중간 크기
    bold_font_size = 22  # Bold 폰트 (제목용)
    step_font_size = 22  # 풀이 단계 표시용

    # 한글 폰트 이름이 감지된 경우 해당 폰트로 모든 크기 생성
    if font_name is not None:
        try:
            font = pygame.font.SysFont(font_name, font_size)
            small_font = pygame.font.SysFont(font_name, small_font_size)
            tiny_font = pygame.font.SysFont(font_name, tiny_font_size)
            medium_font = pygame.font.SysFont(font_name, medium_font_size)
            try:
                bold_font = pygame.font.SysFont(font_name, bold_font_size, bold=True)
            except (pygame.error, TypeError):
                bold_font = pygame.font.SysFont(font_name, bold_font_size)
            step_font = pygame.font.SysFont(font_name, step_font_size)
        except Exception:
            # 폰트 생성 중 오류가 발생하면 기본 폰트로 폴백
            font_name = None

    # 폰트를 찾지 못한 경우 기본 폰트 사용
    if font is None:
        font = pygame.font.Font(None, font_size)
        small_font = pygame.font.Font(None, small_font_size)
        tiny_font = pygame.font.Font(None, tiny_font_size)
        medium_font = pygame.font.Font(None, medium_font_size)
        bold_font = pygame.font.Font(None, bold_font_size)
        step_font = pygame.font.Font(None, step_font_size)

    return font, small_font, tiny_font, medium_font, bold_font, step_font


def get_title_font():
    """
    입력 다이얼로그 등에서 사용하는 제목 폰트 생성.
    한글 폰트를 우선 시도하고, 실패 시 기본 폰트 사용.
    """
    font_name = _find_korean_font_name()
    size = InputDialogConstants.TITLE_FONT_SIZE

    if font_name is not None:
        try:
            font = pygame.font.SysFont(font_name, size)
            test_surface = font.render(
                InputDialogConstants.FONT_TEST_STRING, True, BLACK
            )
            if test_surface.get_width() > 0:
                return font
        except Exception:
            # 폰트 생성 실패 시 기본 폰트로 폴백
            pass

    return pygame.font.Font(None, size)


# ============================================================================
# 공통 그리드/모순 셀 그리기 유틸
# ============================================================================


def draw_sudoku_grid_lines(
    screen: pygame.Surface,
    start_x: int,
    start_y: int,
    cell_size: int,
    thick_width: int = 3,
    thin_width: int = 1,
) -> None:
    """
    스도쿠 그리드 선을 그립니다.

    Args:
        screen: 그릴 pygame Surface
        start_x: 그리드 좌측 상단 X 좌표
        start_y: 그리드 좌측 상단 Y 좌표
        cell_size: 칸 한 개의 픽셀 크기
        thick_width: 박스 경계선 두께
        thin_width: 일반 경계선 두께
    """
    box_size = SudokuBoard.BOX_SIZE
    size = SudokuBoard.SIZE

    for i in range(size + 1):
        is_box_line = i % box_size == 0
        line_width = thick_width if is_box_line else thin_width
        color = BLACK if is_box_line else GRAY

        # 세로선
        x = start_x + i * cell_size
        pygame.draw.line(
            screen,
            color,
            (x, start_y),
            (x, start_y + size * cell_size),
            line_width,
        )

        # 가로선
        y = start_y + i * cell_size
        pygame.draw.line(
            screen,
            color,
            (start_x, y),
            (start_x + size * cell_size, y),
            line_width,
        )


def draw_conflict_cells(
    screen: pygame.Surface,
    conflicts: List[Tuple[int, int]],
    start_x: int,
    start_y: int,
    cell_size: int,
    alpha: int = 128,
) -> None:
    """
    모순이 있는 셀들을 반투명 빨간 배경으로 표시합니다.

    Args:
        screen: 그릴 pygame Surface
        conflicts: (row, col) 튜플 리스트
        start_x: 그리드 좌측 상단 X 좌표
        start_y: 그리드 좌측 상단 Y 좌표
        cell_size: 칸 한 개의 픽셀 크기
        alpha: 배경 투명도 (0~255)
    """
    if not conflicts:
        return

    cell_surface = pygame.Surface((cell_size - 2, cell_size - 2))
    cell_surface.set_alpha(alpha)
    cell_surface.fill(RED)

    for row, col in conflicts:
        x = start_x + col * cell_size
        y = start_y + row * cell_size
        screen.blit(cell_surface, (x + 1, y + 1))


# ============================================================================
# Visualizer 상수
# ============================================================================


class VisualizerConstants:
    """시각화 관련 상수"""

    DEFAULT_CELL_SIZE = 60
    DEFAULT_MARGIN = 50
    SIDE_PANEL_WIDTH = 300
    ANIMATION_DURATION = 0.3
    FPS = 60
    PANEL_X_OFFSET = 10
    TITLE_Y_OFFSET = 20
    SECTION_SPACING = 15
    LINE_SPACING = 18
    MAX_DISPLAYED_CELLS = 2
    LOADING_UPDATE_INTERVAL = 5
    AUTOPLAY_INTERVAL = 0.9


# ============================================================================
# InputDialog 상수
# ============================================================================


class InputDialogConstants:
    """입력 다이얼로그 관련 상수"""

    CELL_SIZE = VisualizerConstants.DEFAULT_CELL_SIZE
    GRID_SIZE = 9  # SudokuBoard.SIZE와 동일하게 유지
    MARGIN = 45
    PANEL_WIDTH = 300
    PANEL_GAP = 30
    GRID_START_Y = 70
    WIDTH = GRID_SIZE * CELL_SIZE + PANEL_WIDTH + PANEL_GAP + 2 * MARGIN
    HEIGHT = 2 * GRID_START_Y + GRID_SIZE * CELL_SIZE
    PANEL_PADDING = 16
    BUTTON_HEIGHT = 40
    BUTTON_SPACING = 10
    BUTTON_ROW_SPACING = 12
    BUTTONS_PER_ROW = 3
    BUTTON_BORDER_RADIUS = 8
    BUTTON_SHADOW_OFFSET = 2
    BUTTON_SHADOW_ALPHA = 50
    BUTTON_HOVER_BRIGHTNESS = 20
    BUTTON_BORDER_DARKEN = 30
    SECTION_TITLE_SPACING = 20
    INSTRUCTION_SPACING = 16
    SECTION_GAP = 12
    ERROR_MESSAGE_SPACING = 22
    FONT_TEST_STRING = "테스트"
    TITLE_FONT_SIZE = 24
