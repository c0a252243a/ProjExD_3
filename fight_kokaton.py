import os
import random
import sys
import time
import pygame as pg
import math


WIDTH = 1100  # ゲームウィンドウの幅
HEIGHT = 650  # ゲームウィンドウの高さ
NUM_OF_BOMBS = 5  #爆弾の数
os.chdir(os.path.dirname(os.path.abspath(__file__)))


def check_bound(obj_rct: pg.Rect) -> tuple[bool, bool]:
    """
    オブジェクトが画面内or画面外を判定し，真理値タプルを返す関数
    引数：こうかとんや爆弾，ビームなどのRect
    戻り値：横方向，縦方向のはみ出し判定結果（画面内：True／画面外：False）
    """
    yoko, tate = True, True

    # 横方向に画面外へ出ているかを確認する
    if obj_rct.left < 0 or WIDTH < obj_rct.right:
        yoko = False

    # 縦方向に画面外へ出ているかを確認する
    if obj_rct.top < 0 or HEIGHT < obj_rct.bottom:
        tate = False

    return yoko, tate


class Bird:
    """
    ゲームキャラクター（こうかとん）に関するクラス
    """
    delta = {  # 押下キーと移動量の辞書
        pg.K_UP: (0, -5),
        pg.K_DOWN: (0, +5),
        pg.K_LEFT: (-5, 0),
        pg.K_RIGHT: (+5, 0),
    }

    # こうかとんの基本画像を読み込み，右向き・左向きの画像を用意する
    img0 = pg.transform.rotozoom(pg.image.load("fig/3.png"), 0, 0.9)
    img = pg.transform.flip(img0, True, False)  # デフォルトのこうかとん（右向き）

    imgs = {  # 0度から反時計回りに定義
        (+5, 0): img,  # 右
        (+5, -5): pg.transform.rotozoom(img, 45, 0.9),  # 右上
        (0, -5): pg.transform.rotozoom(img, 90, 0.9),  # 上
        (-5, -5): pg.transform.rotozoom(img0, -45, 0.9),  # 左上
        (-5, 0): img0,  # 左
        (-5, +5): pg.transform.rotozoom(img0, 45, 0.9),  # 左下
        (0, +5): pg.transform.rotozoom(img, -90, 0.9),  # 下
        (+5, +5): pg.transform.rotozoom(img, -45, 0.9),  # 右下
    }

    def __init__(self, xy: tuple[int, int]):
        """
        こうかとん画像Surfaceを生成する
        引数 xy：こうかとん画像の初期位置座標タプル
        """
        self.img = __class__.imgs[(+5, 0)]
        self.rct: pg.Rect = self.img.get_rect()
        self.rct.center = xy

        # ビームの発射方向に使うため，現在のこうかとんの向きを保存する
        self.dire = (+5, 0)

    def change_img(self, num: int, screen: pg.Surface):
        """
        こうかとん画像を切り替え，画面に転送する
        引数1 num：こうかとん画像ファイル名の番号
        引数2 screen：画面Surface
        """
        self.img = pg.transform.rotozoom(pg.image.load(f"fig/{num}.png"), 0, 0.9)
        screen.blit(self.img, self.rct)

    def update(self, key_lst: list[bool], screen: pg.Surface):
        """
        押下キーに応じてこうかとんを移動させる
        引数1 key_lst：押下キーの真理値リスト
        引数2 screen：画面Surface
        """
        sum_mv = [0, 0]

        # 押されている矢印キーを調べ，移動量を合計する
        for k, mv in __class__.delta.items():
            if key_lst[k]:
                sum_mv[0] += mv[0]
                sum_mv[1] += mv[1]

        # 合計した移動量に応じてこうかとんを移動させる
        self.rct.move_ip(sum_mv)

        # 画面外に出た場合は，直前の移動を取り消す
        if check_bound(self.rct) != (True, True):
            self.rct.move_ip(-sum_mv[0], -sum_mv[1])

        # 移動している場合だけ，向きと画像を更新する
        if not (sum_mv[0] == 0 and sum_mv[1] == 0):
            self.dire = tuple(sum_mv)
            self.img = __class__.imgs[self.dire]

        screen.blit(self.img, self.rct)


class Bomb:
    """
    爆弾に関するクラス
    """
    def __init__(self, color: tuple[int, int, int], rad: int):
        """
        引数に基づき爆弾円Surfaceを生成する
        引数1 color：爆弾円の色タプル
        引数2 rad：爆弾円の半径
        """
        self.img = pg.Surface((2*rad, 2*rad))
        pg.draw.circle(self.img, color, (rad, rad), rad)
        self.img.set_colorkey((0, 0, 0))
        self.rct = self.img.get_rect()

        # 爆弾の初期位置は画面内のランダムな位置にする
        self.rct.center = random.randint(0, WIDTH), random.randint(0, HEIGHT)

        # 爆弾の移動速度を設定する
        self.vx, self.vy = +5, +5

    def update(self, screen: pg.Surface):
        """
        爆弾を速度ベクトルself.vx, self.vyに基づき移動させる
        引数 screen：画面Surface
        """
        yoko, tate = check_bound(self.rct)

        # 横方向に画面外へ出た場合は，横方向の速度を反転させる
        if not yoko:
            self.vx *= -1

        # 縦方向に画面外へ出た場合は，縦方向の速度を反転させる
        if not tate:
            self.vy *= -1

        self.rct.move_ip(self.vx, self.vy)
        screen.blit(self.img, self.rct)

    
class Beam:
    """
    ビームに関するクラス
    """

    def __init__(self, bird: Bird):
        """
        こうかとんの向きに応じたビームを生成する
        bird: ビームを発射するこうかとん
        """
        # こうかとんが現在向いている方向を，ビームの速度として利用する
        vx, vy = bird.dire
        self.vx = vx
        self.vy = vy

        # ビーム画像をこうかとんの向きに合わせて回転
        img = pg.image.load("fig/beam.png")
        angle = math.degrees(math.atan2(-vy, vx))
        self.img = pg.transform.rotozoom(img, angle, 1.0)

        self.rct = self.img.get_rect()

        # こうかとんの向いている方向にビームを配置
        self.rct.centerx = bird.rct.centerx + bird.rct.width * vx / 5
        self.rct.centery = bird.rct.centery + bird.rct.height * vy / 5

    def update(self, screen: pg.Surface):
        """
        ビームを移動させ、画面に描画する
        screen: ゲーム画面
        """
        # 画面外に出たビームは描画せず，後でリストから削除する
        if check_bound(self.rct) != (True, True):
            return

        self.rct.move_ip(self.vx, self.vy)
        screen.blit(self.img, self.rct)


class Score:
    """
    スコアを表示するクラス
    """

    def __init__(self):
        # フォントを設定
        self.fonto = pg.font.Font(None, 50)

        # 文字色を青に設定
        self.color = (0, 0, 255)

        # 初期値
        self.value = 0

        # 文字列の生成
        self.img = self.fonto.render(f"Score: {self.value}", True, self.color)
        self.rct = self.img.get_rect()

        # 画面左下に配置
        self.rct.center = 100, HEIGHT - 50

    def update(self, screen: pg.Surface):
        """
        現在のスコアを画面に表示する
        """
        # 現在のスコア値をもとに，毎フレーム表示文字列を作り直す
        self.img = self.fonto.render(f"Score: {self.value}", True, self.color)
        screen.blit(self.img, self.rct)


class Explosion:
    """
    爆発エフェクトに関するクラス
    """

    def __init__(self, bomb: Bomb):
        """
        爆発画像を読み込み、爆弾の位置に配置する
        bomb: 爆発した爆弾
        """
        img = pg.image.load("fig/explosion.gif")

        # 通常画像と反転画像を交互に表示し，爆発しているように見せる
        self.imgs = [
            img,
            pg.transform.flip(img, True, True),
        ]

        self.rct = self.imgs[0].get_rect()

        # 爆発エフェクトは，撃ち落とされた爆弾の中心位置に表示する
        self.rct.center = bomb.rct.center

        # 爆発を表示する時間
        self.life = 20

    def update(self, screen: pg.Surface):
        """
        爆発画像を交互に表示する
        """
        # lifeを毎フレーム減らし，0になったら表示を終了する
        self.life -= 1
        if self.life > 0:
            screen.blit(self.imgs[self.life % 2], self.rct)


def main():
    pg.display.set_caption("たたかえ！こうかとん")
    screen = pg.display.set_mode((WIDTH, HEIGHT))    
    bg_img = pg.image.load("fig/pg_bg.jpg")

    # ゲーム内で使う各オブジェクトを生成する
    bird = Bird((300, 200))
    bombs = [Bomb((255, 0, 0), 10) for _ in range(NUM_OF_BOMBS)]
    # beam = None  # ゲーム初期化時にはビームは存在しない
    beams = []
    score = Score()
    explosions = []

    clock = pg.time.Clock()
    tmr = 0

    while True:
        # イベント処理：終了操作やスペースキー押下を確認する
        for event in pg.event.get():
            if event.type == pg.QUIT:
                return

            if event.type == pg.KEYDOWN and event.key == pg.K_SPACE:
                # スペースキー押下でBeamクラスのインスタンス生成
                beams.append(Beam(bird))

        # 背景を毎フレーム描画し直す
        screen.blit(bg_img, [0, 0])
        
        # こうかとんと爆弾の衝突判定
        for bomb in bombs:
            if bird.rct.colliderect(bomb.rct):
                # ゲームオーバー時に，こうかとん画像を切り替え，1秒間表示させる
                bird.change_img(8, screen)

                # ゲームオーバーの文字を画面中央付近に表示する
                fonto = pg.font.Font(None, 80)
                txt = fonto.render("Game Over", True, (255, 0, 0))
                screen.blit(txt, [WIDTH // 2 - 150, HEIGHT // 2])
                
                pg.display.update()
                time.sleep(1)
                return

        # 現在押されているキー情報を取得する
        key_lst = pg.key.get_pressed()

        # 複数のビームと複数の爆弾の衝突判定
        for j, beam in enumerate(beams):
            if beam is None:
                continue

            for i, bomb in enumerate(bombs):
                if bomb is None:
                    continue

                if beam.rct.colliderect(bomb.rct):
                    score.value += 1  # 爆弾を撃ち落としたらスコアを1増やす
                    bird.change_img(6, screen)  # こうかとんを喜ぶ画像に変更
                    explosions.append(Explosion(bomb))  # 爆発エフェクトを追加 

                    # 衝突したビームと爆弾をNoneにして，後でリストから削除する
                    beams[j] = None
                    bombs[i] = None
                    break
        
        # Noneになったビームと爆弾をリストから取り除く
        beams = [beam for beam in beams if beam is not None]
        bombs = [bomb for bomb in bombs if bomb is not None]

        # こうかとん，爆弾，ビームをそれぞれ更新・描画する
        bird.update(key_lst, screen)
        # beam.update(screen)   

        for bomb in bombs:
            bomb.update(screen)

        for beam in beams:
            beam.update(screen)
        
        # 画面外に出たビームと，表示時間が終わった爆発エフェクトを削除する
        beams = [beam for beam in beams if check_bound(beam.rct) == (True, True)]
        explosions = [explosion for explosion in explosions if explosion.life > 0]

        # 爆発エフェクトを描画する
        for explosion in explosions:
            explosion.update(screen)
        
        # スコアを最後に描画し，ほかの画像に隠れにくくする
        score.update(screen)
        
        pg.display.update()
        tmr += 1
        clock.tick(50)


if __name__ == "__main__":
    pg.init()
    main()
    pg.quit()
    sys.exit()