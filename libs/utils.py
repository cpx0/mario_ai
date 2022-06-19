#!/usr/bin/env python
# -*- coding: utf-8 -*-

# 日本語版追加：訓練後の様子
import gym
from IPython import display
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
from matplotlib import animation

from gym.wrappers import FrameStack
from nes_py.wrappers import JoypadSpace
import gym_super_mario_bros

from envs import SkipFrame, GrayScaleObservation, ResizeObservation
from libs.agents import agent_factory

# checkpoint_dir = Path("checkpoints") / "2022-06-18T16-35-14"
# chkpt_name = "mario_net_8.chkpt"

# カラー画像表示用の環境
def display_color_image(cfg: dict, checkpoint_dir: Path, chkpt_name: str):

    env = gym_super_mario_bros.make(cfg.stage_name)
    env = JoypadSpace(env, cfg.movement)

    # 環境にWrapperを適用
    env = SkipFrame(env, skip=cfg.skip_numb)
    env = GrayScaleObservation(env)
    env = ResizeObservation(env, shape=cfg.resize_shape)
    env = FrameStack(env, num_stack=cfg.stack_frame_numb)

    state = env.reset()

    # マリオ環境の場合、初期状態にランダム性がないので、独立用意で良いですが、
    # クリボーの初期位置などが毎回ランダムに変わる場合は、envとenv_colorの整合性をきちんと取る必要があります
    # 今回は、これで問題ありません。
    env_color = gym_super_mario_bros.make(cfg.stage_name)
    env_color = JoypadSpace(env_color, cfg.movement)

    # 環境と状態を初期化します
    state_color = env_color.reset()
    state = env.reset()

    # 動画作成用の画像を溜めるリスト
    img = []
    img_color=[]

    # step数
    num_step = 0

    mario = agent_factory[cfg.agent_type](state_dim=(cfg.stack_frame_numb, cfg.resize_shape, cfg.resize_shape), action_dim=env.action_space.n, save_dir=None, cfg=cfg)

    chkpt_path = checkpoint_dir / chkpt_name
    mario.load_target(chkpt_path=chkpt_path)

    # ゲーム開始！
    while True:
        # 現在の状態に対するエージェントの行動を決める
        # action = mario.act(state)
        action = mario.act(state)
        # エージェントが行動を実行
        next_state, reward, done, info = env.step(action)
        
        # 記憶
        mario.cache(state, next_state, action, reward, done)
        # # 訓練
        # q, loss = mario.learn()
        # # ログ保存
        # logger.log_step(reward, loss, q)
        # 動画化に毎step描画を追加
        display.clear_output(wait=True)
        # grayscaleの画像をRGBの画像に変換
        rgb_img = np.stack((state[0],)*3,axis=0).transpose(1,2,0)
        img.append(rgb_img)
        # カラー画像用（4 skipしているので4回同じ行動をします）
        for i in range(4):
            next_state_color, _, done, _ = env_color.step(action)
            if done:
                break
        
        display.clear_output(wait=True)
        rgb_img_color = np.stack(state_color,axis=0)
        img_color.append(rgb_img_color)
        state_color = next_state_color
        # 状態の更新
        state = next_state
        num_step+=1
        # ゲームが終了したかどうかを確認
        if done or info["flag_get"]:
            break
    #logger.log_episode()
    #logger.record(episode=e, epsilon=mario.exploration_rate, step=mario.curr_step)
    print("num_step:", num_step)
    # 実行によっては、短時間で失敗するので、このセルを何回か実行してみる。 
    return img, img_color


# 白黒での学習に使用した画像による、動画を表示
def display_grayscale_movie(img: list, cfg: dict, save_dir: Path, chkpt_name: str):
    dpi = 72
    interval = 50 # ms
    plt.figure(figsize=(240/dpi,256/dpi),dpi=dpi)  # 修正

    patch = plt.imshow(img[0])
    plt.axis=('off')
    animate = lambda i: patch.set_data(img[i])
    ani = animation.FuncAnimation(plt.gcf(),animate,frames=len(img),interval=interval)
    ani.save(save_dir / ("action_" + chkpt_name.replace('.chkpt', '') + "_stage-" + \
        cfg.stage_name.replace('SuperMarioBros-', '') + "_grayscale.gif"), writer='pillow')
    # display.HTML(ani.to_jshtml())
    plt.close()


# カラーでの動画を表示
def display_color_movie(img_color: list, cfg: dict, save_dir: Path, chkpt_name: str):
    dpi = 72
    interval = 50 # ms

    plt.figure(figsize=(240/dpi,256/dpi),dpi=dpi)  # 修正
    patch = plt.imshow(img_color[0])
    plt.axis=('off')
    animate = lambda i: patch.set_data(img_color[i])
    ani = animation.FuncAnimation(plt.gcf(),animate,frames=len(img_color),interval=interval)
    ani.save(save_dir / ("action_" + chkpt_name.replace('.chkpt', '') + "_stage-" + \
        cfg.stage_name.replace('SuperMarioBros-', '') + "_color.gif"), writer='pillow')
    # display.HTML(ani.to_jshtml())
    plt.close()

