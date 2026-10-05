# SPDX-FileCopyrightText: 2026 Benedict Harcourt <ben.harcourt@harcourtprogramming.co.uk>
#
# SPDX-License-Identifier: BSD-2-Clause

from __future__ import annotations as _future_annotations

from typing import Any, NamedTuple

import logging
import pathlib
import subprocess
import tempfile
import uuid

from .rules import ASPECT_RATIO, FRAMES_PER_SECOND, LANE_HEIGHT, LANE_WIDTH, Stone, Team
from .vector import VecTwo

FRAME_BASE = """
  <style>
    #tee { fill: white; }
    #c4ft { fill: green; }
    #c8ft { fill: white }
    #c12ft { fill: blue; }
    #lines { stroke: black; stroke-width: 0.25; }
    #guides { stroke: rgba(200, 0, 0, 0.3); stroke-width: 0.25; }
    #guides text { font: 2px sans-serif; stroke: none; }
  </style>

  <defs>
    <g id="yellow-stone">
      <circle cx="0" cy="0" r="1.40" stroke="#cccccc" fill="#aaaaaa" stroke-width="0.15" />
      <circle cx="0" cy="0" r="1.10" fill="yellow" stroke="#eedd00" stroke-width="0.15" />
      <rect x="-0.15" y="-0.15" width="1.5" rx="0.1" ry="0.1" height="0.3" fill="#b5a642" />
    </g>
    <g id="red-stone">
      <circle cx="0" cy="0" r="1.40" stroke="#cccccc" fill="#aaaaaa" stroke-width="0.1" />
      <circle cx="0" cy="0" r="1.10" fill="red" stroke="#ee0000" stroke-width="0.15" />
      <rect x="-0.15" y="-0.15" width="1.5" rx="0.1" ry="0.1" height="0.3" fill="#b5a642" />
    </g>
    <g id="human">
      <circle cx="0" cy="0" r="2.6" stroke="#000" fill="#444" stroke-width="0.2" />
    </g>
  </defs>

  <!-- Lane outline -->
  <rect x="0" y="0" width="445" height="48" fill="white" />
  <rect x="0" y="0" width="445" height="0.25" fill="#888" />
  <rect x="0" y="47.75" width="445" height="0.25" fill="#888" />

  <!-- Target Circles -->
  <circle id="c12ft" cx="48.8" cy="24" r="18.3" />
  <circle id="c8ft" cx="48.8" cy="24" r="12.2" />
  <circle id="c4ft" cx="48.8" cy="24" r="6.1" />
  <circle id="tee" cx="48.8" cy="24" r="1.55" />

  <g style="filter: opacity(0.8)">
    <circle id="c12ft" cx="396.2" cy="24" r="18.3" />
    <circle id="c8ft" cx="396.2" cy="24" r="12.2" />
    <circle id="c4ft" cx="396.2" cy="24" r="6.1" />
    <circle id="tee" cx="396.2" cy="24" r="1.55" />
  </g>

  <g id="lines">
    <path d="M48.8,0v48" id="centre-line" />
    <path d="M30.5,0v48" id="back-line" />
    <path d="M0,24h445" id="tee-line" />
    <path d="M112.8,0v48" id="hog-line" />
    <path d="M332.2,0v48" id="t-hog-line" />
    <path d="M396.2,0v48" id="t-tee-line" />
  </g>
"""


GUIDES = """
  <g id="guides">
    <text style="transform: rotate(90deg)" x="18" y="-20">Offset</text>
    <path d="M28,6h92" /><text x="23.6" y="6.6">-180</text>
    <path d="M28,12h92" /><text x="23.6" y="12.6">-120</text>
    <path d="M28,18h92" /><text x="24.8" y="18.6">-60</text>
    <path d="M28,30h92" /><text x="25.2" y="30.6">60</text>
    <path d="M28,36h92" /><text x="24" y="36.6">120</text>
    <path d="M28,42h92" /><text x="24" y="42.6">180</text>

    <text x="60" y="2">Speeds</text>
    <path d="M118.26,3v42" /><text x="116.5" y="47">350</text>
    <path d="M106.02,3v42" /><text x="104.4" y="47">360</text>
    <path d="M93.58,3v42" /><text x="91.75" y="47">370</text>
    <path d="M79.38,3v42" /><text x="77.6" y="47">380</text>
    <path d="M66.53,3v42" /><text x="64.9" y="47">390</text>
    <path d="M51.82,3v42" /><text x="50" y="47">400</text>
    <path d="M38.54,3v42" /><text x="36.9" y="47">410</text>
  </g>
"""


class Player(NamedTuple):
    id: str
    name: str
    mention: str

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Player):
            return NotImplemented

        return other.id == self.id

    def __hash__(self) -> int:
        return hash(self.id)

    def __str__(self) -> str:
        return self.name


class Human(NamedTuple):
    position: VecTwo[float]
    rotation: float


class FrameStoneState(NamedTuple):
    colour: Team
    number: int
    position: VecTwo[float]
    rotation: float


class FrameState(NamedTuple):
    tracked_position: VecTwo[float]
    human: Human
    stones: tuple[FrameStoneState, ...]


class ThrowLog:
    @classmethod
    def from_json(cls, logger: logging.Logger, data: dict[str, Any]) -> ThrowLog:
        out = cls(logger, Player(*data["player"]))
        out.id = data["id"]
        out.messages = data["messages"]

        for frame in data["frames"]:
            tracked, human, stones = frame

            out.frames.append(
                FrameState(
                    VecTwo(tracked),
                    Human(VecTwo(human[0]), human[1]),
                    tuple(FrameStoneState(Team(t), n, VecTwo(p), r) for t, n, p, r in stones),
                ),
            )

        return out

    logger: logging.Logger

    id: str
    player: Player
    messages: list[str]
    frames: list[FrameState]

    def __init__(self, logger: logging.Logger, player: Player) -> None:
        self.id = uuid.uuid4().hex
        self.logger = logger
        self.player = player
        self.messages = []
        self.frames = []

    def record_message(self, message: str, *args: object) -> None:
        record = self.logger.makeRecord(
            self.logger.name,
            logging.INFO,
            "curling",
            len(self.frames),
            message,
            args,
            exc_info=None,
        )
        self.messages.append(record.getMessage())
        self.logger.handle(record)

    def record_frame(self, tracked_stone: Stone, human: Human, stones: set[Stone]) -> None:
        self.frames.append(
            FrameState(
                tracked_stone.position.copy(),
                Human(human.position.copy(), human.rotation),
                tuple(
                    FrameStoneState(x.colour, x.number, x.position.copy(), x.rotation)
                    for x in stones
                ),
            ),
        )

    def _generate_frame(self, state: FrameState, *, guides: bool = False) -> str:
        view_width = LANE_HEIGHT * ASPECT_RATIO
        max_x_pos = LANE_WIDTH - view_width

        x_pos = state.tracked_position.x - (view_width / 2)
        x_pos = max(min(x_pos, max_x_pos), 0)

        frame_data = (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<svg xmlns="http://www.w3.org/2000/svg" '
            f'viewBox="{x_pos} 0 {view_width} {LANE_HEIGHT}">\n'
        )
        frame_data += FRAME_BASE

        if guides:
            frame_data += GUIDES

        frame_data += f'  <use x="0" y="0" href="#human" style="{css_transform(state.human)}" />\n'

        for stone in state.stones:
            frame_data += (
                f'  <use x="0" y="0" href="#{stone.colour.name.lower()}-stone"'
                f' style="{css_transform(stone)}" />\n'
            )

        frame_data += "</svg>\n"

        return frame_data

    def generate_animated_svg(self, path: pathlib.Path) -> None:  # noqa: C901,PLR0912,PLR0915
        view_box = LANE_HEIGHT * ASPECT_RATIO
        max_x_pos = LANE_WIDTH - view_box

        animated_frames = len(self.frames)
        last_frame = self.frames[-1]
        last_frame_position = {(s.colour, s.number): s.position for s in last_frame.stones}

        view_port_offset: list[tuple[int, float]] = []
        human_offset: list[tuple[int, Human]] = []

        x_pos = self.frames[0].tracked_position.x - (view_box / 2)
        x_pos = max(min(x_pos, max_x_pos), 0)
        view_port_offset.append((0, x_pos))

        human_offset.append((0, self.frames[0].human))

        # Identify all stones that actually move
        tracked_stones: dict[tuple[Team, int], list[FrameStoneState]] = {}
        for stone in self.frames[0].stones:
            key = stone.colour, stone.number
            if last_frame_position[key] != stone.position:
                tracked_stones[key] = [
                    FrameStoneState(stone.colour, 0, stone.position, stone.rotation),
                ]

        # Calculate all the animate key frames for all stones that move
        for idx, frame in enumerate(self.frames):
            x_pos = frame.tracked_position.x - (view_box / 2)
            x_pos = max(min(x_pos, max_x_pos), 0)
            last_update, last_pos = view_port_offset[0]
            if last_pos != x_pos and (idx - last_update > 3):
                view_port_offset.insert(0, (idx, x_pos))

            last_update, last_human = human_offset[0]
            if (
                last_human.position != frame.human.position
                or last_human.rotation != frame.human.rotation
            ):
                human_offset.insert(0, (idx, frame.human))

            for stone in frame.stones:
                key = stone.colour, stone.number
                if key not in tracked_stones:
                    continue

                last = tracked_stones[key][0]
                if last.position == stone.position and last.rotation == stone.rotation:
                    continue

                tracked_stones[key].insert(
                    0,
                    FrameStoneState(stone.colour, idx, stone.position, stone.rotation),
                )

        with path.open("w") as svg_buffer:
            anim_timer = animated_frames / FRAMES_PER_SECOND

            svg_buffer.write(
                '<?xml version="1.0" encoding="UTF-8"?>\n'
                '<svg xmlns="http://www.w3.org/2000/svg" '
                f'viewBox="0 0 {view_box} {LANE_HEIGHT}">\n',
            )

            # Write the animation <style> block
            svg_buffer.write("  <style>\n")

            svg_buffer.write("    @keyframes view-port {\n")
            for frame_id, x_pos in reversed(view_port_offset):
                timing = 100.0 * frame_id / animated_frames
                svg_buffer.write(
                    f"      {timing:.2f}% {{ transform: translate({-x_pos:.1f}px, 0); }}\n",
                )
            svg_buffer.write("      100% { transform: translate(0, 0); }\n")
            svg_buffer.write("    }\n")

            svg_buffer.write("    @keyframes human {\n")
            for frame_id, human in reversed(human_offset):
                timing = 100.0 * frame_id / animated_frames
                svg_buffer.write(
                    f"      {timing:.2f}% {{ {css_transform(human)} }}\n",
                )
            svg_buffer.write("    }\n")

            for key, frames in tracked_stones.items():
                svg_buffer.write(f"    @keyframes {key[0].name.lower()}-{key[1]} {{\n")
                for fram in reversed(frames):
                    timing = 100.0 * fram.number / animated_frames
                    svg_buffer.write(
                        f"      {timing:.2f}% {{ {css_transform(fram)} }}\n",
                    )
                svg_buffer.write(
                    f"      100% {{ {css_transform(frames[0])} }}\n",
                )
                svg_buffer.write("    }\n")
            svg_buffer.write("  </style>\n")

            svg_buffer.write(f'<g style="animation: view-port {anim_timer:.2f}s linear;">\n')

            svg_buffer.write(FRAME_BASE)

            svg_buffer.write(
                f'  <use x="0" y="0" href="#human" style="'
                f"animation: human {anim_timer:.2f}s linear;"
                f' {css_transform(human_offset[0][1])}" />\n',
            )

            # Write the stones
            for stone in self.frames[0].stones:
                key = stone.colour, stone.number
                if key not in tracked_stones:
                    svg_buffer.write(
                        f'  <use x="0" y="0" href="#{stone.colour.name.lower()}-stone"'
                        f' style="{css_transform(stone)}" />\n',
                    )
                else:
                    final = tracked_stones[key][0]
                    svg_buffer.write(
                        f'  <use x="0" y="0" href="#{stone.colour.name.lower()}-stone" style="'
                        f"animation: {key[0].name.lower()}-{key[1]} {anim_timer:.2f}s linear;"
                        f"{css_transform(final)}"
                        f'" />\n',
                    )

            svg_buffer.write("</g>\n</svg>\n")

    def generate_video(self, path: pathlib.Path) -> None:
        t = tempfile.TemporaryDirectory()

        if not self.frames:
            raise ValueError

        with t as temp_dir:
            temp = pathlib.Path(temp_dir)

            for index, frame in enumerate(self.frames):
                file = temp / f"{index+1:05d}.svg"
                file.write_text(self._generate_frame(frame), "utf-8")

            # Put the final frame as the first for preview purposes
            file = temp / f"{0:05d}.svg"
            file.write_text(self._generate_frame(self.frames[-1]), "utf-8")

            subprocess.check_call(  # noqa: S603
                [
                    "/usr/bin/ffmpeg",
                    "-y",  # Overwrite automatically
                    "-loglevel",
                    "16",
                    "-width",
                    str(550),
                    "-height",
                    str(int(550 / ASPECT_RATIO)),
                    "-keep_ar",
                    "0",
                    "-framerate",
                    str(FRAMES_PER_SECOND),
                    "-pattern_type",
                    "glob",
                    "-i",
                    "*.svg",
                    "-lossless",
                    "1",
                    path.absolute(),
                ],
                stdin=subprocess.DEVNULL,
                cwd=temp_dir,
            )

    def generate_gif(self, path: pathlib.Path) -> None:
        t = tempfile.TemporaryDirectory()

        if not self.frames:
            raise ValueError

        with t as temp_dir:
            temp = pathlib.Path(temp_dir)
            palette = temp / "palette.png"

            for index, frame in enumerate(self.frames):
                file = temp / f"{index+1:05d}.svg"
                file.write_text(self._generate_frame(frame), "utf-8")

            # Put the final frame as the first for preview purposes
            file = temp / f"{0:05d}.svg"
            file.write_text(self._generate_frame(self.frames[-1]), "utf-8")

            subprocess.check_call(  # noqa: S603
                [
                    "/usr/bin/ffmpeg",
                    "-y",  # Overwrite automatically
                    "-loglevel",
                    "16",
                    "-width",
                    str(550),
                    "-height",
                    str(int(550 / ASPECT_RATIO)),
                    "-keep_ar",
                    "0",
                    "-framerate",
                    str(FRAMES_PER_SECOND),
                    "-pattern_type",
                    "glob",
                    "-i",
                    "*.svg",
                    "-vf",
                    "palettegen",
                    palette.absolute(),
                ],
                stdin=subprocess.DEVNULL,
                cwd=temp_dir,
            )
            subprocess.check_call(  # noqa: S603
                [
                    "/usr/bin/ffmpeg",
                    "-y",  # Overwrite automatically
                    "-loglevel",
                    "16",
                    "-width",
                    str(550),
                    "-height",
                    str(int(550 / ASPECT_RATIO)),
                    "-keep_ar",
                    "0",
                    "-framerate",
                    str(FRAMES_PER_SECOND),
                    "-pattern_type",
                    "glob",
                    "-i",
                    "*.svg",
                    "-i",
                    palette,
                    "-filter_complex",
                    f"[0:v]fps={FRAMES_PER_SECOND},scale=550:-1[x];[x][1:v]paletteuse",
                    "-loop",
                    "0",
                    path.absolute(),
                ],
                stdin=subprocess.DEVNULL,
                cwd=temp_dir,
            )

    def generate_state_image(self, path: pathlib.Path) -> None:
        t = tempfile.TemporaryDirectory()

        if not self.frames:
            raise ValueError

        with t as temp_dir:
            (pathlib.Path(temp_dir) / "state.svg").write_text(
                self._generate_frame(self.frames[-1], guides=True),
            )

            subprocess.check_call(  # noqa: S603
                [
                    "/usr/bin/ffmpeg",
                    "-y",  # Overwrite automatically
                    "-loglevel",
                    "16",
                    "-width",
                    str(550),
                    "-height",
                    str(int(550 / ASPECT_RATIO)),
                    "-keep_ar",
                    "0",
                    "-i",
                    "state.svg",
                    "-lossless",
                    "1",
                    path.absolute(),
                ],
                stdin=subprocess.DEVNULL,
                cwd=temp_dir,
            )


def css_transform(stone: FrameStoneState | Human) -> str:
    return (
        f"transform: translate({stone.position.x:.1f}px, {stone.position.y:.1f}px) "
        f"rotate({stone.rotation:.1f}deg);"
    )
