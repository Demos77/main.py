import random
import time
import arcade
import arcade.gui
from dataclasses import dataclass
from array import array
import arcade.gl
import pers


W = 1600
H = 900

GRAVITY = (0, -1250)
DAMPING = 0.9
IGROK_MOVE_GROUND = 10000
MASS_IGROK = 1
FRICTION_IGROK = 0.8
IG_MAX_VERTICAL_SPEED = 2000
IG_MAX_HORIZANTAL_SPEED = 200
IGROK_JUMP_FORCE = 40000
WALL_FRICTION = 0.8


@dataclass
class Chasti:
    buffer: arcade.gl.Buffer
    vao: arcade.gl.Geometry
    start_time: float


class Igra1GlavaViev(arcade.View):
    def __init__(self):
        super().__init__()
        arcade.set_background_color((255, 182, 193))

        # Переменные для частиц
        self.chasti_list = []
        self.program = self.window.ctx.load_program(vertex_shader='shederi_igra/ver_shad_tl_ogon.glsl',
                                                    fragment_shader='shederi_igra/frag_shad_tl_ogon.glsl')
        self.window.ctx.enable_only(self.window.ctx.BLEND)

        self.igrok = None

        self.vrag_list = None

        self.walls_list = None
        self.platforms_list = None
        self.object = None

        self.fizika = None

        self.kamera = None

        # Переменные True, либо False
        self.levo = False
        self.pravo = False
        self.beg = False

        self.s = 0
        self.s1 = 0

        self.t_main_patch = (':resources:images/tiles/')

    def setup(self):
        self.kamera = arcade.Camera(W, H)

        self.vrag_list = arcade.SpriteList()

        self.igrok = pers.BetaMaster(self.vrag_list)

        vrag = pers.Vrag(self.igrok, self.object, True)
        vrag.position = 500, 400
        self.vrag_list.append(vrag)

        self.igrok.sprite_list = self.vrag_list

        self.walls_list = arcade.SpriteList()
        for x in range(-64, 10000, 128):
            wall = arcade.Sprite(f'{self.t_main_patch}grassMid.png')
            wall.position = x, 64
            self.walls_list.append(wall)

        for x in range(192, 3000, 128):
            wall = arcade.Sprite(f'{self.t_main_patch}grassMid.png')
            wall.position = x, 192
            self.walls_list.append(wall)

        self.fizika = arcade.PymunkPhysicsEngine(GRAVITY, DAMPING)
        self.fizika.add_sprite(self.igrok, MASS_IGROK, FRICTION_IGROK, max_vertical_velocity=IG_MAX_VERTICAL_SPEED,
                               max_horizontal_velocity=IG_MAX_HORIZANTAL_SPEED,
                               moment=arcade.PymunkPhysicsEngine.MOMENT_INF, damping=0.9, collision_type='player')
        self.fizika.add_sprite_list(self.walls_list, friction=WALL_FRICTION,
                                    body_type=arcade.PymunkPhysicsEngine.STATIC, collision_type='wall')
        for vrag in self.vrag_list:
            self.fizika.add_sprite(vrag, 200, 0.8, max_vertical_velocity=IG_MAX_VERTICAL_SPEED,
                                   max_horizontal_velocity=IG_MAX_HORIZANTAL_SPEED,
                                   moment=arcade.PymunkPhysicsEngine.MOMENT_INF, damping=0.9)

    def on_draw(self):
        self.kamera.use()
        self.center_kamera_za_igrok()
        self.clear()

        self.walls_list.draw()
        self.vrag_list.draw()

        self.igrok.draw()
        self.igrok.update_animation()

    def on_update(self, delta_time: float):
        for vrag in self.vrag_list:
            x = vrag.return_force('x')
            y = vrag.return_force('y')

            if y > 0:
                self.s += 1
            if self.s > 2 and not vrag.is_on_ground:
                y = 0

            self.fizika.apply_force(vrag, (x, y))
            self.fizika.set_friction(vrag, 0.5)

            if y == 0 and self.s >= 2:
                self.s = 0

        if self.pravo and not self.levo:
            if self.beg:
                self.fizika.set_horizontal_velocity(self.igrok, 500)
            else:
                force = (IGROK_MOVE_GROUND, 0)
                self.fizika.apply_force(self.igrok, force)
                self.fizika.set_friction(self.igrok, 0.5)
        elif not self.pravo and self.levo:
            if self.beg:
                self.fizika.set_horizontal_velocity(self.igrok, -500)
            else:
                force = (-IGROK_MOVE_GROUND, 0)
                self.fizika.apply_force(self.igrok, force)
                self.fizika.set_friction(self.igrok, 0.5)
        else:
            self.fizika.set_friction(self.igrok, 1)

        if self.igrok.molniya.udar and self.s1 == 0 and self.igrok.molniya.s_kd >= 300:
            self.s1 += 1
            poz = self.igrok.molniya.koordinati()
            if poz != (0, 0):
                self.fizika.set_position(self.igrok, poz)

        self.fizika.step()

    def on_key_press(self, symbol: int, modifiers: int):
        if symbol == arcade.key.NUM_2:
            self.igrok.streliPeruna.udar = True
            print(1)

        if symbol == arcade.key.NUM_0:
            self.igrok.molniya.udar = True
            self.s1 = 0

        if symbol == arcade.key.NUM_1:
            self.igrok.gnev_Tora.udar = True

        if symbol == arcade.key.D or symbol == arcade.key.RIGHT:
            self.pravo = True
        elif symbol == arcade.key.A or symbol == arcade.key.LEFT:
            self.levo = True

        if symbol == arcade.key.W or symbol == arcade.key.UP:
            if self.igrok.is_on_ground:
                force = (0, IGROK_JUMP_FORCE)
                self.fizika.apply_force(self.igrok, force)

        if symbol == arcade.key.RSHIFT:
            self.beg = True

    def on_key_release(self, _symbol: int, _modifiers: int):
        if _symbol == arcade.key.RSHIFT:
            self.beg = False

        if _symbol == arcade.key.D or _symbol == arcade.key.RIGHT:
            self.pravo = False
        elif _symbol == arcade.key.A or _symbol == arcade.key.LEFT:
            self.levo = False

    def center_kamera_za_igrok(self, x=False, y=False):
        ekran_center_x = self.igrok.center_x - self.kamera.viewport_width / 3
        ekran_center_y = self.igrok.center_y - self.kamera.viewport_height / 5

        self.kamera.move_to((ekran_center_x, ekran_center_y), 0.5)

        if x:
            return ekran_center_x
        if y:
            return ekran_center_y


win = arcade.Window(W, H)
viev1 = Igra1GlavaViev()
viev1.setup()
win.show_view(viev1)

arcade.run()
