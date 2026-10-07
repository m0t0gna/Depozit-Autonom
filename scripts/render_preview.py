"""Capturi reproductibile pentru UI si plansele pixel art, fara fereastra."""
import os
from pathlib import Path


def main():
    os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
    os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
    import pygame
    from fleet import Fleet
    from grid import Grid
    from fleet_ui import DepotUI, draw, window_size
    from pixel_art import PAPER, TEAL, MUTED, NAMES, robot_sprite, tile_sprite, pixel_text
    target = Path(__file__).resolve().parent / 'artifacts'
    target.mkdir(exist_ok=True)
    pygame.init()
    try:
        font = pygame.font.SysFont('consolas', 15)
        for count in (3, 5, 8):
            fleet = Fleet(robot_count=count, grid=Grid(30, 20), pickups=[])
            ui = DepotUI(fleet)
            screen = pygame.Surface(window_size(fleet.grid))
            draw(screen, font, fleet, message=ui.commands.message, now=1800, animation=ui.animation)
            pygame.image.save(screen, target / f'fleet-{count}.png')
            if count == 5:
                draw(screen, font, fleet, now=1800, show_help=True)
                pygame.image.save(screen, target / 'retro-help.png')
                for y in range(3, 9):
                    fleet.edit((18, y))
                ui.place_box((20, 12))
                for tick in range(3):
                    ui.advance(tick * 120)
                ui.select_robot(next(r.id for r in fleet.robots if r.task_id))
                draw(screen, font, fleet, selected=ui.selected, show_paths=ui.show_paths,
                     message=ui.commands.message, now=360, animation=ui.animation)
                pygame.image.save(screen, target / 'selected-route.png')

        # Secventa demonstrativa de viraj; doar fixture vizual, nu comenzi in simulator.
        demo = Fleet(robot_count=1, grid=Grid(30, 20), pickups=[], starts=[(3, 3)])
        demo_ui = DepotUI(demo)
        demo.robots[0].pos = (4, 3)
        demo_ui.animation.capture(demo, 200, 120)
        demo.robots[0].pos = (4, 4)
        demo_ui.animation.capture(demo, 200, 240)
        strip = pygame.Surface((710, 194))
        strip.fill(PAPER)
        strip.blit(pixel_text('PRAF LA VIRAJ', 2, TEAL), (16, 12))
        for i, now in enumerate((240, 280, 360, 500, 710)):
            frame = pygame.Surface(window_size(demo.grid))
            draw(frame, font, demo, now=now, animation=demo_ui.animation)
            strip.blit(frame, (16 + i * 138, 39), pygame.Rect(100, 158, 130, 120))
            strip.blit(font.render(f'{now - 240} ms', False, MUTED), (16 + i * 138, 170))
        pygame.image.save(strip, target / 'turn-dust.png')

        sheet = pygame.Surface((840, 444))
        sheet.fill(PAPER)
        sheet.blit(pixel_text('MICUL DEPOZIT / PIXEL ATLAS', 3, TEAL), (24, 20))
        for i, name in enumerate(NAMES):
            x = 20 + i * 102
            sheet.blit(robot_sprite(i, 5), (x, 65))
            sheet.blit(pixel_text(name, 2), (x + 5, 150))
            sheet.blit(robot_sprite(i, 5, carrying=True), (x, 190))
        for i, kind in enumerate(('floor', 'wall', 'pickup', 'dropoff', 'home')):
            x = 24 + i * 162
            sheet.blit(tile_sprite(kind, scale=4), (x, 310))
            label = ('PODEA', 'PERETE', 'PRELUARE', 'LIVRARE', 'BAZA')[i]
            sheet.blit(pixel_text(label, 2), (x, 384))
        sheet.blit(font.render('Originale, definite in cod. Grila 15x15 / scalare fara netezire.', False, MUTED), (24, 419))
        pygame.image.save(sheet, target / 'pixel-sprites.png')
        print(f'Capturi salvate in {target}')
    finally:
        pygame.quit()


if __name__ == '__main__':
    main()
