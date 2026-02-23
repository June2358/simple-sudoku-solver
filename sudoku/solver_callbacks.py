"""
솔버 콜백 유틸 모듈

솔버의 핵심 알고리즘과 분리된 출력/표현용 콜백 생성기를 제공합니다.
"""

from typing import Any, Callable, Dict

from .board import SudokuBoard


def create_console_step_callback() -> Callable[[Dict[str, Any]], None]:
    """
    step_by_step 모드에서 사용하는 콘솔 출력용 콜백 생성.
    """
    current_iteration = [0]

    def console_step_callback(event: Dict[str, Any]) -> None:
        event_type = event.get("event_type", "")
        tech = event.get("technique_name") or event_type
        message = event.get("message", "")
        board_state = event.get("board_state")
        candidates_state = event.get("candidates_state")

        def _print_board_snapshot() -> None:
            if not board_state:
                return
            preview_board = SudokuBoard(board_state)
            if candidates_state:
                for r in range(SudokuBoard.SIZE):
                    for c in range(SudokuBoard.SIZE):
                        preview_board.candidates[r][c] = candidates_state[r][c]
            print(preview_board)
            print("\n[현재 후보 상태]")
            print(preview_board.show_candidates())
            print("=" * 80)

        if event_type == "INITIAL_STATE":
            print("\n[초기 상태 - 각 칸의 가능한 후보들]")
            _print_board_snapshot()
        elif event_type == "SOLVED":
            print("\n[해결 완료]")
            _print_board_snapshot()
        elif event_type in {"CONTRADICTION", "ERROR"}:
            print(f"\n[{tech}] {message}")
        elif event_type.startswith("GUESS") or event_type.startswith("BACKTRACK"):
            indent = "  " * event.get("depth", 0)
            print(f"\n{indent}{message}")
            _print_board_snapshot()
        else:
            current_iteration[0] += 1
            print(f"\n[라운드 {current_iteration[0]}] {tech}:")
            _print_board_snapshot()

    return console_step_callback
