import Phaser from 'phaser';
import { BattleScene } from './scenes/BattleScene';
import './styles.css';

export const game = new Phaser.Game({
  type: Phaser.AUTO,
  parent: 'game',
  width: 1120,
  height: 640,
  backgroundColor: '#121820',
  scene: [BattleScene],
  // The original uses fixed logical pixels: a 48px battlefield cell and
  // fixed-size unit art. Do not fit/stretch the canvas with the browser.
  scale: { mode: Phaser.Scale.NONE, autoCenter: Phaser.Scale.NO_CENTER }
});

if(import.meta.env.DEV)Object.assign(window,{battleGame:game});
