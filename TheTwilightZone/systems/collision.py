from __future__ import annotations

import math

import pygame

from levels.cave_section import LevelElement


class CollisionSystem:
    """
    Handles collision between the player and solid level geometry.

    Walls and obstacles are represented as closed polygons.

    The collision system uses the exact same geometry that is stored in
    the level data, preventing visual and collision geometry from becoming
    inconsistent.
    """

    SOLID_TYPES = {
        "wall",
        "obstacle"
    }

    # Below this many degrees from a dead-on hit (straight into the wall's
    # normal), movement is too head-on to slide and should stop instead.
    SLIDE_DEADZONE_DEGREES = 10.0

    def __init__(self):
        self.solid_elements: list[LevelElement] = []

    def set_level_elements(
        self,
        elements: list[LevelElement]
    ) -> None:
        """
        Updates the collision geometry for the current level.
        """

        self.solid_elements = [
            element
            for element in elements
            if element.element_type in self.SOLID_TYPES
        ]

    def check_collision(
        self,
        rect: pygame.Rect
    ) -> bool:
        """
        Checks whether a rectangle overlaps any solid polygon.

        This first performs a fast bounding-box test and then checks
        polygon intersection.
        """

        for element in self.solid_elements:

            polygon = self._get_world_polygon(
                element
            )

            if len(polygon) < 3:
                continue

            polygon_rect = pygame.Rect(
                min(point.x for point in polygon),
                min(point.y for point in polygon),
                max(point.x for point in polygon)
                - min(point.x for point in polygon),
                max(point.y for point in polygon)
                - min(point.y for point in polygon)
            )

            if not polygon_rect.colliderect(rect):
                continue

            if self._polygon_intersects_rect(
                polygon,
                rect
            ):
                return True

        return False

    @staticmethod
    def _get_world_polygon(
        element: LevelElement
    ) -> list[pygame.Vector2]:
        """
        Returns an element's polygon in world coordinates.
        """

        return element.get_polygon()

    @staticmethod
    def _polygon_intersects_rect(
        polygon: list[pygame.Vector2],
        rect: pygame.Rect
    ) -> bool:
        """
        Performs a simple polygon-vs-rectangle collision test.

        This method checks:
            1. Polygon vertices inside the rectangle.
            2. Rectangle corners inside the polygon.
            3. Polygon edges intersecting rectangle edges.
        """

        rectangle_points = [
            pygame.Vector2(rect.topleft),
            pygame.Vector2(rect.topright),
            pygame.Vector2(rect.bottomright),
            pygame.Vector2(rect.bottomleft)
        ]

        # Check polygon vertices inside rectangle.
        for point in polygon:
            if rect.collidepoint(
                round(point.x),
                round(point.y)
            ):
                return True

        # Check rectangle corners inside polygon.
        for point in rectangle_points:
            if CollisionSystem._point_in_polygon(
                point,
                polygon
            ):
                return True

        # Check polygon edges against rectangle edges.
        rectangle_edges = list(
            zip(
                rectangle_points,
                rectangle_points[1:]
                + rectangle_points[:1]
            )
        )

        polygon_edges = list(
            zip(
                polygon,
                polygon[1:] + polygon[:1]
            )
        )

        for polygon_start, polygon_end in polygon_edges:
            for rect_start, rect_end in rectangle_edges:

                if CollisionSystem._line_segments_intersect(
                    polygon_start,
                    polygon_end,
                    rect_start,
                    rect_end
                ):
                    return True

        return False

    def get_slide_vector(
        self,
        rect: pygame.Rect,
        movement: pygame.Vector2,
        search_radius: int = 48
    ) -> pygame.Vector2:
        """
        Returns a movement vector that follows the nearest wall surface.

        Rather than stopping dead when pushing into a wall, this finds the
        closest wall edge to the rect and keeps only the component of the
        intended movement that runs tangent to that edge. Because curved
        walls are stored as many short polygon segments, the nearest edge
        (and therefore the slide direction) changes continuously as the
        player moves along the curve, producing an "Among Us"-style
        wall-following slide instead of a hard stop.
        """

        if movement.length_squared() == 0:
            return pygame.Vector2()

        center = pygame.Vector2(rect.center)
        search_rect = rect.inflate(search_radius * 2, search_radius * 2)

        closest_edge: tuple[pygame.Vector2, pygame.Vector2] | None = None
        closest_distance: float | None = None

        for element in self.solid_elements:

            polygon = element.get_polygon()

            if len(polygon) < 2:
                continue

            polygon_rect = pygame.Rect(
                min(point.x for point in polygon),
                min(point.y for point in polygon),
                max(point.x for point in polygon)
                - min(point.x for point in polygon),
                max(point.y for point in polygon)
                - min(point.y for point in polygon)
            )

            if not polygon_rect.colliderect(search_rect):
                continue

            edges = list(
                zip(
                    polygon,
                    polygon[1:] + polygon[:1]
                )
            )

            for edge_start, edge_end in edges:

                closest_point = self._closest_point_on_segment(
                    center,
                    edge_start,
                    edge_end
                )

                distance = (closest_point - center).length()

                if closest_distance is None or distance < closest_distance:
                    closest_distance = distance
                    closest_edge = (edge_start, edge_end)

        if closest_edge is None:
            return pygame.Vector2()

        edge_start, edge_end = closest_edge
        edge_direction = edge_end - edge_start

        if edge_direction.length_squared() == 0:
            return pygame.Vector2()

        edge_direction = edge_direction.normalize()
        move_direction = movement.normalize()

        # Angle between the movement and the wall's tangent line. 0 means
        # movement runs parallel to the wall (an easy slide); 90 means it
        # runs straight into the wall's normal (a dead-on hit).
        alignment = min(1.0, abs(move_direction.dot(edge_direction)))
        angle_from_tangent = math.degrees(math.acos(alignment))
        angle_from_normal = 90.0 - angle_from_tangent

        if angle_from_normal < self.SLIDE_DEADZONE_DEGREES:
            # Too close to a head-on hit to meaningfully slide.
            return pygame.Vector2()

        # Keep only the part of the movement that runs along the wall.
        tangential_amount = movement.dot(edge_direction)

        return edge_direction * tangential_amount

    @staticmethod
    def _closest_point_on_segment(
        point: pygame.Vector2,
        segment_start: pygame.Vector2,
        segment_end: pygame.Vector2
    ) -> pygame.Vector2:
        """
        Returns the closest point on a line segment to the given point.
        """

        segment_vector = segment_end - segment_start

        if segment_vector.length_squared() == 0:
            return pygame.Vector2(segment_start)

        t = (
            (point - segment_start).dot(segment_vector)
            / segment_vector.length_squared()
        )

        t = max(0.0, min(1.0, t))

        return segment_start + segment_vector * t

    @staticmethod
    def _point_in_polygon(
        point: pygame.Vector2,
        polygon: list[pygame.Vector2]
    ) -> bool:
        """
        Uses the ray-casting algorithm to determine whether a point
        is inside a polygon.
        """

        inside = False

        j = len(polygon) - 1

        for i in range(len(polygon)):

            xi = polygon[i].x
            yi = polygon[i].y

            xj = polygon[j].x
            yj = polygon[j].y

            intersects = (
                (yi > point.y)
                != (yj > point.y)
            ) and (
                point.x
                <
                (
                    (xj - xi)
                    * (point.y - yi)
                    / (yj - yi)
                    + xi
                )
            )

            if intersects:
                inside = not inside

            j = i

        return inside

    @staticmethod
    def _line_segments_intersect(
        p1: pygame.Vector2,
        p2: pygame.Vector2,
        q1: pygame.Vector2,
        q2: pygame.Vector2
    ) -> bool:
        """
        Determines whether two line segments intersect.
        """

        def orientation(
            a: pygame.Vector2,
            b: pygame.Vector2,
            c: pygame.Vector2
        ) -> float:

            return (
                (b.y - a.y)
                * (c.x - b.x)
                -
                (b.x - a.x)
                * (c.y - b.y)
            )

        o1 = orientation(p1, p2, q1)
        o2 = orientation(p1, p2, q2)
        o3 = orientation(q1, q2, p1)
        o4 = orientation(q1, q2, p2)

        return (
            (o1 > 0) != (o2 > 0)
            and
            (o3 > 0) != (o4 > 0)
        )