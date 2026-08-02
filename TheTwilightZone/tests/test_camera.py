import pygame

from systems.camera import Camera


def test_camera_follows_target_horizontally_without_right_boundary_clamp():
    camera = Camera(screen_width=800, screen_height=600)
    world_bounds = pygame.Rect(0, 0, 2000, 2000)

    camera.update(pygame.Vector2(2000, 1000), world_bounds)

    assert camera.position.x == 1600
    assert camera.position.y == 700


def test_camera_still_clamps_to_left_boundary_and_vertical_bounds():
    camera = Camera(screen_width=800, screen_height=600)
    world_bounds = pygame.Rect(100, 50, 2000, 2000)

    camera.update(pygame.Vector2(0, 0), world_bounds)

    assert camera.position.x == 100
    assert camera.position.y == 50
