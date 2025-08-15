# Military FCS (Fire Control System) Simulator
# 軍事火器管制システムシミュレーター

## 概要 / Overview

高度な軍事火器管制システム（FCS）のWebベースシミュレーターです。リアルタイムレーダー表示、目標追跡、弾道計算、射撃ソリューションを備えた本格的なタクティカルインターフェースを提供します。

A sophisticated web-based military Fire Control System (FCS) simulator featuring real-time radar display, target tracking, ballistic calculations, and firing solutions with an authentic tactical interface.

## 機能 / Features

### レーダーシステム / Radar System
- リアルタイムレーダースイープアニメーション / Real-time radar sweep animation
- 複数目標の同時追跡 / Multiple target tracking
- 調整可能なレーダー範囲（5-50km） / Adjustable radar range (5-50km)
- 目標の移動ベクトル表示 / Target movement vectors
- クリックによる目標選択 / Click-to-select targets

### 目標情報 / Target Information
- 目標ID、距離、方位、仰角 / Target ID, distance, bearing, elevation
- 速度と種類の表示 / Speed and type display
- 脅威レベル評価システム / Threat level assessment
- 自動脅威優先順位付け / Automatic threat prioritization

### 弾道計算 / Ballistic Calculation
- 4種類の弾薬タイプ / 4 ammunition types:
  - APFSDS (装甲貫通フィン安定徹甲弾)
  - HEAT (対戦車榴弾)
  - HE (榴弾)
  - SMOKE (発煙弾)
- 環境要因の考慮 / Environmental factors:
  - 風速・風向 / Wind speed and direction
  - 気温 / Temperature
  - 重力落下補正 / Gravity drop compensation
- リードアングル計算 / Lead angle calculation
- 射撃時間予測 / Time-to-target prediction

### ユーザーインターフェース / User Interface
- ミリタリーグリーンのタクティカルデザイン / Military green tactical design
- グロー効果とアニメーション / Glow effects and animations
- リアルタイムシステムクロック / Real-time system clock
- システムログ表示 / System log display
- レスポンシブデザイン / Responsive design

## 使用方法 / How to Use

### 起動方法 / Getting Started
1. `index.html`をWebブラウザで開く / Open `index.html` in a web browser
2. システムが自動的に初期化されます / System will initialize automatically
3. レーダー上に目標が表示されます / Targets will appear on radar

### 操作方法 / Controls

#### 目標の選択 / Target Selection
- レーダー上の目標をクリックして選択 / Click on targets on radar to select
- 「ACQUIRE TARGET」ボタンで最高脅威目標を自動選択 / Use "ACQUIRE TARGET" to auto-select highest threat

#### 射撃手順 / Firing Procedure
1. 目標を選択 / Select a target
2. 「CALCULATE」で弾道計算 / Click "CALCULATE" for ballistic solution
3. 「LOCK TARGET」で目標をロック / Click "LOCK TARGET" to lock target
4. 「FIRE」で射撃 / Click "FIRE" to engage

#### パラメータ調整 / Parameter Adjustment
- レーダー範囲：+/- ボタンで調整 / Radar range: Adjust with +/- buttons
- 弾薬種類：ドロップダウンから選択 / Ammunition: Select from dropdown
- 環境条件：数値入力フィールドで設定 / Environmental: Set in input fields

## 技術仕様 / Technical Specifications

### 使用技術 / Technologies Used
- HTML5 Canvas (レーダー表示 / Radar display)
- CSS3 (アニメーション・エフェクト / Animations and effects)
- Vanilla JavaScript (ロジック実装 / Logic implementation)

### ブラウザ要件 / Browser Requirements
- モダンブラウザ推奨 / Modern browsers recommended
- Chrome, Firefox, Safari, Edge対応 / Works on Chrome, Firefox, Safari, Edge
- JavaScript有効化必須 / JavaScript must be enabled

## ファイル構成 / File Structure
```
/workspace/
├── index.html      # メインHTMLファイル / Main HTML file
├── styles.css      # スタイルシート / Stylesheet
├── script.js       # JavaScriptロジック / JavaScript logic
└── README.md       # このファイル / This file
```

## 注意事項 / Notes
- このシミュレーターは教育・エンターテインメント目的です / This simulator is for educational and entertainment purposes
- 実際の軍事システムとは異なります / Not representative of actual military systems
- 弾道計算は簡略化されています / Ballistic calculations are simplified

## ライセンス / License
Educational Use Only - 教育目的限定

---

Developed as a military FCS training simulator with emphasis on visual design and user experience.
軍事FCS訓練シミュレーターとして、ビジュアルデザインとユーザー体験を重視して開発されました。