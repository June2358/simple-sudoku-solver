"""
공용 UI 컴포넌트 모듈

입력 다이얼로그와 시각화 화면에서 함께 사용하는 컴포넌트를 제공합니다.
"""

from typing import Tuple

import pygame

from .gui_constants import WHITE, BLACK, InputDialogConstants


class Button:
    """버튼 UI 컴포넌트"""

    def __init__(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        text: str,
        color: Tuple[int, int, int],
        font,
        text_color: Tuple[int, int, int] = WHITE,
    ):
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
        border_color = tuple(
            max(0, c - InputDialogConstants.BUTTON_BORDER_DARKEN) for c in color
        )

        # 그림자
        shadow_rect = pygame.Rect(
            self.rect.x + InputDialogConstants.BUTTON_SHADOW_OFFSET,
            self.rect.y + InputDialogConstants.BUTTON_SHADOW_OFFSET,
            self.rect.width,
            self.rect.height,
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
            return tuple(
                min(255, c + InputDialogConstants.BUTTON_HOVER_BRIGHTNESS)
                for c in self.base_color
            )
        return self.base_color

    @staticmethod
    def _draw_rect(
        screen: pygame.Surface,
        color: Tuple[int, int, int],
        rect: pygame.Rect,
        width: int = 0,
    ):
        """사각형 그리기 (pygame 버전 호환)"""
        border_radius = InputDialogConstants.BUTTON_BORDER_RADIUS
        try:
            if width == 0:
                pygame.draw.rect(screen, color, rect, border_radius=border_radius)
            else:
                pygame.draw.rect(
                    screen, color, rect, width, border_radius=border_radius
                )
        except TypeError:
            pygame.draw.rect(screen, color, rect, width)
