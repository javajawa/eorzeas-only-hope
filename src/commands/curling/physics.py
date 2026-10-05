# SPDX-FileCopyrightText: 2026 Benedict Harcourt <ben.harcourt@harcourtprogramming.co.uk>
#
# SPDX-License-Identifier: BSD-2-Clause

from __future__ import annotations as _future_annotations

from typing import NamedTuple

import json
import logging
import math
import pathlib
import uuid

from .animation import Human, Player, ThrowLog
from .rules import (
    BACKLINE,
    CENTER_LINE,
    FRAMES_PER_SECOND,
    HACK_POINT,
    HOG_LINE,
    LANE_HEIGHT,
    SIX_FEET,
    STONE_DIAMETER,
    STONE_RADIUS,
    TEE_LINE,
    THROW_LINE,
    TIME_STEP,
    TOTAL_STONES,
    Stone,
    Team,
)
from .vector import VecTwo

# Tuned to feel plausible in a rendered end rather than to match a
# full curling mechanical model.
SLIDING_FRICTION = 2.8  # dm/s^2
CURL_ACCELERATION = 0.012  # dm/s^2 per dm/s of stone speed
SPIN_DECAY = 0.02  # 1/s
COLLISION_RESTITUTION = 0.88
TANGENTIAL_DAMPING = 0.9
COLLISION_SOLVER_PASSES = 6
DISCARD_SPEED = 1


class WrongTeamError(Exception):
    pass


class Score(NamedTuple):
    score: int
    team: Team
    players: set[Player]


class CurlingGame:
    @classmethod
    def load(cls, logger: logging.Logger, file: pathlib.Path) -> CurlingGame:
        with file.open("rb") as infile:
            data = json.load(infile)

        out = cls(logger)
        out.id = data["id"]

        stones: dict[tuple[Team, int], Stone] = {}
        for stone_data in data["stones"]:
            team = Team(stone_data["colour"])
            number = stone_data["number"]

            stone = Stone(team, number)
            stone.position = VecTwo(stone_data["position"])
            stone.velocity = VecTwo(stone_data["velocity"])
            stone.rotation = stone_data["rotation"]
            stone.spin = stone_data["spin"]

            stones[(team, number)] = stone

        out.stones = set(stones.values())
        out.active_stones = {stones[tuple(x)] for x in data["active_stones"]}
        out.discarding_stones = {stones[tuple(x)] for x in data["discarding_stones"]}
        out.discarded_stones = {stones[tuple(x)] for x in data["discarded_stones"]}
        out.to_throw = {stones[tuple(x)] for x in data["to_throw"]}

        for team_id, players in data["players"].items():
            team = Team(int(team_id))
            for player in players:
                out.players[team].add(Player(*player))

        for turn in data["turns"]:
            out.turns.append(ThrowLog.from_json(logger, turn))

        return out

    logger: logging.Logger

    id: str
    stones: set[Stone]  # All stones in this game
    active_stones: set[Stone]  # Stones in the house (either moving or still)
    discarding_stones: set[Stone]  # Stones that are moving to discard
    discarded_stones: set[Stone]  # Stones that have been discarded
    to_throw: set[Stone]  # Stones yet to be thrown

    players: dict[Team, set[Player]]
    turns: list[ThrowLog]

    def __init__(self, logger: logging.Logger) -> None:
        self.id = uuid.uuid4().hex
        self.stones = set()
        self.turns = []
        self.logger = logger
        self.players = {team: set() for team in Team}

        for team in Team:
            for stone in range(TOTAL_STONES):
                self.stones.add(Stone(team, stone + 1))

        self.to_throw = self.stones.copy()
        self.active_stones = set()
        self.discarded_stones = set()
        self.discarding_stones = set()

    def save(self, location: pathlib.Path) -> None:
        def stone_ids(stones: set[Stone]) -> list[list[int]]:
            return sorted([s.colour, s.number] for s in stones)

        data = {
            "id": self.id,
            "stones": sorted(self.stones),
            "active_stones": stone_ids(self.active_stones),
            "discarding_stones": stone_ids(self.discarding_stones),
            "discarded_stones": stone_ids(self.discarded_stones),
            "to_throw": stone_ids(self.to_throw),
            "players": self.players,
            "turns": self.turns,
        }

        with location.open("w") as outfile:
            json.dump(data, outfile, cls=JsonEncoder, indent=2)

    def play_turn(  # noqa: PLR0913,PLR0917
        self,
        player: Player,
        center_offset: float,
        speed: float,
        spin: float,
        target: float,
        release_time: float,
    ) -> ThrowLog:
        stone = min(self.to_throw)

        already_played = {team for team in self.players if player in self.players[team]}
        if already_played and already_played != {stone.colour}:
            raise WrongTeamError

        throw = ThrowLog(self.logger, player)
        self.players[stone.colour].add(player)
        self.turns.append(throw)

        self.to_throw.discard(stone)
        throw.record_message("Player %s steps up to throw %s", player, stone)

        # Initial angle calculation
        angle = math.atan2(target - center_offset, HACK_POINT - TEE_LINE)

        # Put the stone on the hack line with the provided parameters
        stone.position = VecTwo((HACK_POINT, CENTER_LINE + center_offset))
        stone.velocity = VecTwo((-speed * math.cos(angle), speed * math.sin(angle)))
        stone.rotation = 180 * angle / math.pi
        stone.spin = spin

        human = Human(stone.position - (stone.velocity.normalized() * 2), stone.rotation)

        # Frame 0 is the release of the stone.
        # NOTE: The simulation assumes the stone instantly accelerates and spins
        throw.record_message("Stone %s starts moving", stone)
        self.active_stones.add(stone)

        # Initial frame: stone is at the hack line
        throw.record_frame(stone, human, self.stones)

        # Run the throw up until release
        while self._run_pre_throw(stone, human, release_time):
            throw.record_frame(stone, human, self.stones)

        # Whilst there are still moving stones, we have
        active = True
        while active:
            self._run_movement()
            self._check_collisions(throw)
            self._drift_discarded_stones()
            active = self._check_dead_stones(throw, strict=False)
            throw.record_frame(stone, human, self.stones)

        self._check_dead_stones(throw, strict=True)
        while self.discarding_stones:
            self._drift_discarded_stones()
            throw.record_frame(stone, human, self.stones)

        # Build the animation to return to the user
        throw.record_message("Simulation completed after %d frames", len(throw.frames))
        return throw

    def score(self) -> list[Score]:
        center = VecTwo((TEE_LINE, CENTER_LINE))

        if not self.active_stones:
            return [Score(0, team, self.players[team]) for team in Team]

        order = sorted(self.active_stones, key=lambda stone: float(stone.position - center))
        winner = order[0].colour
        score = 0
        for stone in order:
            if stone.colour != winner:
                break
            if float(stone.position - center) >= SIX_FEET + SIX_FEET + STONE_RADIUS:
                break

            score += 1

        return [Score(score if team == winner else 0, team, self.players[team]) for team in Team]

    def _run_pre_throw(self, stone: Stone, human: Human, release_time: float) -> bool:
        steps = (stone.position.x - THROW_LINE) / -stone.velocity.x

        if steps < release_time:
            return False

        stone.position += stone.velocity * TIME_STEP
        human.position.__iadd__(stone.velocity * TIME_STEP)  # pylint: disable=C2801
        return True

    def _run_movement(self) -> None:
        # Integrate stone motion with a fixed timestep so the animation is
        # independent of the render frame rate.
        for stone in self.active_stones:
            speed = float(stone.velocity)
            if speed == 0:
                continue

            curl_mag = max(-1.0, min(1.0, stone.spin / 120.0)) / 10
            curl_direction = VecTwo((stone.velocity.y, stone.velocity.x)) * curl_mag
            stone.velocity += curl_direction * (CURL_ACCELERATION * speed * TIME_STEP)

            # Calculate speed loss to fiction
            drag = SLIDING_FRICTION * TIME_STEP
            stone.velocity *= 0 if speed <= drag else (speed - drag) / speed

            # Update the stones position:
            # NOTE: we do this after updating the velocity so that
            #       _check_collisions can unwind when overlap happened
            stone.position += stone.velocity * TIME_STEP
            stone.rotation += stone.spin * TIME_STEP

            # The stone loses rotation steadily as the pebble slows it down.
            stone.spin *= math.exp(-SPIN_DECAY * TIME_STEP)

    def _check_collisions(self, throw: ThrowLog) -> None:
        # Resolve a couple of passes so chain reactions settle without doing
        # expensive continuous collision detection.

        iteration = 0
        collided = True
        exclude: set[tuple[Stone, Stone]] = set()

        while collided and iteration < COLLISION_SOLVER_PASSES:
            collided = False
            iteration += 1

            # We want to process only moving stones in reverse throw order,
            # because statistically a later throw is likely to be further
            # from the backline. Although everything is symmetric, for log
            # purposes we want the collisions to be recorded in that direction.
            moving_stones = sorted(s for s in self.active_stones if s.velocity > 0)

            for moving_stone in moving_stones:
                # The set of things we can *not* collide into are:
                #   - Stones not currently on the field
                #   - Ourselves
                #   - Stones we have already collided into this frame

                potential_targets = self.active_stones.copy()
                potential_targets.discard(moving_stone)
                potential_targets.difference_update(
                    (s1 if s2 == moving_stone else s2 if s1 == moving_stone else None)
                    for s1, s2 in exclude
                )

                targets = {
                    (t, float(t.position - moving_stone.position))
                    for t in potential_targets
                    if float(t.position - moving_stone.position) <= STONE_DIAMETER
                }

                for impact_target, distance in sorted(targets, key=lambda x: x[1]):
                    # Basic collision check -- ignore stones that aren't touching
                    # (or are somehow super-imposed because that *breaks the maths*)
                    if distance > STONE_DIAMETER or distance == 0:
                        continue

                    # Check the stones are moving relative to each other
                    relative_velocity = impact_target.velocity - moving_stone.velocity

                    if float(relative_velocity) == 0:
                        continue

                    throw.record_message("Stone %s hits %s", moving_stone, impact_target)
                    exclude.add((moving_stone, impact_target))
                    collided = True

                    self._process_collision(moving_stone, impact_target, relative_velocity)

    def _process_collision(
        self,
        moving_stone: Stone,
        impact_target: Stone,
        relative_velocity: VecTwo[float],
    ) -> None:
        # Calculate when in the frame the overlap occurred
        current_overlap = STONE_DIAMETER - float(impact_target.position - moving_stone.position)
        sub_frame_offset = current_overlap / (float(relative_velocity) / FRAMES_PER_SECOND)

        # Roll back stones to the collision position
        moving_stone.position -= moving_stone.velocity * sub_frame_offset / FRAMES_PER_SECOND
        impact_target.position -= impact_target.velocity * sub_frame_offset / FRAMES_PER_SECOND

        # Calculate the properties of the collision, using the rolled back positions
        offset = impact_target.position - moving_stone.position
        normal = offset.normalized()
        approach_speed = relative_velocity.dot(normal)

        # Equal-mass impulse along the collision normal, with a
        # little energy loss to keep the end from feeling bouncy.
        impulse = -(1 + COLLISION_RESTITUTION) * approach_speed / 2
        moving_stone.velocity -= normal * impulse
        impact_target.velocity += normal * impulse

        # Light tangential damping keeps glancing hits from
        # behaving too perfectly elastic.
        tangential = relative_velocity - (normal * approach_speed)
        tangential *= (1 - TANGENTIAL_DAMPING) / 2
        moving_stone.velocity += tangential
        impact_target.velocity -= tangential

        # Finish this frame's movement from the collision position
        moving_stone.position += moving_stone.velocity * (1 - sub_frame_offset) / FRAMES_PER_SECOND
        impact_target.velocity += (
            impact_target.velocity * (1 - sub_frame_offset) / FRAMES_PER_SECOND
        )

    def _check_dead_stones(self, throw: ThrowLog, *, strict: bool) -> bool:
        # Remove dead stones
        have_active_stone = False

        back_factor = 1 if strict else 3
        side_factor = 1 if strict else -1

        for stone in self.active_stones.copy():
            if stone.velocity == VecTwo((0.0, 0.0)):
                continue

            if stone.position.x < BACKLINE - STONE_RADIUS / back_factor:
                throw.record_message(
                    "Discarding moving stone %s that is beyond the backline",
                    stone,
                )
                self._discard_stone(stone, flow=True)

            elif (
                stone.position.y < STONE_RADIUS / side_factor
                or stone.position.y > LANE_HEIGHT - STONE_RADIUS / side_factor
            ):
                throw.record_message(
                    "Discarding moving stone %s that has left the lane",
                    stone,
                )
                self._discard_stone(stone)

            elif float(stone.velocity) < 0.1:
                throw.record_message("Stone %s stops moving", stone)
                if stone.position.x > HOG_LINE:
                    throw.record_message("Stone %s is before the hog line, removing", stone)
                    self._discard_stone(stone)
                stone.velocity = VecTwo((0.0, 0.0))

            else:
                have_active_stone = True

        return have_active_stone

    def _discard_stone(self, stone: Stone, *, flow: bool = False) -> None:
        self.active_stones.discard(stone)

        discards = self.discarded_stones.union(self.discarding_stones)
        discard_number = len([None for s in discards if s.colour == stone.colour])

        if flow:
            stone.velocity = stone.discard_position(discard_number)
            self.discarding_stones.add(stone)
        else:
            stone.position = stone.discard_position(discard_number)
            stone.velocity = VecTwo((0.0, 0.0))
            self.discarded_stones.add(stone)

    def _drift_discarded_stones(self) -> None:
        for stone in self.discarding_stones.copy():
            vector = stone.velocity - stone.position

            if float(vector) > DISCARD_SPEED:
                stone.position += vector.normalized() * DISCARD_SPEED
                continue

            stone.position = stone.velocity
            stone.velocity = VecTwo((0.0, 0.0))
            self.discarding_stones.discard(stone)
            self.discarded_stones.add(stone)


class JsonEncoder(json.JSONEncoder):
    def default(self, o: object) -> object:
        if isinstance(o, Team):
            return o.name
        if isinstance(o, (tuple, set)):
            return list(o)
        if isinstance(o, VecTwo):
            return [o.x, o.y]
        if isinstance(o, Stone):
            return {
                "colour": o.colour,
                "number": o.number,
                "position": o.position,
                "velocity": o.velocity,
                "rotation": o.rotation,
                "spin": o.spin,
            }
        if isinstance(o, ThrowLog):
            return {"id": o.id, "player": o.player, "messages": o.messages, "frames": o.frames}

        return super().default(o)
