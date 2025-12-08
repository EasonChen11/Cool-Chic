這是一個非常好的專題方向。你的教授要求的 "Implement/improve/evaluate recent image compression methods" 完全符合你現在正在使用的 Cool-chic。

為什麼 Cool-chic 是一個完美的選擇？

Recent (近五年): Cool-chic 是非常新的技術（主要論文發表於 2023-2024，README 甚至提到了 2024 年底的 Wasserstein 論文），完全符合時效性。

Implement (實作): 你已經把環境架起來了，這部分已經完成了 80%。

Evaluate (評估): 它自帶 Evaluation code，你需要做的只是跟其他算法比較。

Improve (改進): 這是專題的核心。因為 Cool-chic 是 "Overfitted"（對單張圖過擬合）的架構，有很多參數可以調整來換取「速度 vs 畫質」的權衡。

以下我為你規劃一個具體的執行計畫，幫助你滿足教授的三點要求：

第一階段：Evaluate (建立基準線)

你不能只跑 Cool-chic，你必須證明它好（或不好）。你需要跟傳統算法（JPEG, WebP, BPG）比較。

我為你準備了一個 基準線比較腳本 (tools/benchmark_baseline.py)。這個腳本會自動計算同一張圖片在不同壓縮品質下的 JPEG 和 WebP 的 BPP 與 PSNR，產生的 CSV 格式跟你的 rd_curve.csv 一樣，方便你畫在同一張圖上。
Standard Codecs Benchmark
12月7日 下午5:15

如何執行 Evaluation:

跑一次你的 Cool-chic batch: ./run_coolchic.sh lena --batch

跑一次基準線: python tools/benchmark_baseline.py lena.png --out results/my_experiments/lena

現在你的資料夾裡會有 Cool-chic, JPEG, WebP 的數據，你可以修改 plot_rd.py 把這三條線畫在一起。這就是標準的學術 Evaluation。

第二階段：Improve (提出改進方案)

這部分是拿分的關鍵。既然你是用現成的 Code，"改進" 可以透過 Ablation Study (消融實驗) 或 Hyperparameter Tuning (超參數調整) 來達成。

你可以嘗試以下三個方向之一（選一個即可）：

方向 A：追求編碼速度 (Speed Improvement)

Cool-chic 最大的缺點是編碼很慢（因為要訓練）。你可以嘗試修改設定檔 cfg/enc/intra/fast_10k.cfg 來尋找「速度」與「畫質」的平衡點。

實驗： 減少 n_itr (迭代次數)。預設可能是 10000 次，試試看改成 5000 次或 2000 次，看 PSNR 掉多少？如果時間少一半，PSNR 只掉 0.1dB，那就是成功的改進（Trade-off）。

修改方式： 複製 fast_10k.cfg 為 fast_5k.cfg，修改裡面的 n_itr。

方向 B：追求更高壓縮率 (Model Complexity)

Cool-chic 的核心是 MLP (多層感知機)。你可以試著改變網路的大小。

實驗： 修改設定檔中的 layers 或 arm_size。

預設可能是 [24, 24] (兩層隱藏層，每層 24 個神經元)。

試試看更小的網路 [16, 16] (檔案會變小，解碼變快，但畫質可能變差)。

試試看更大的網路 [32, 32, 32]。

方向 C：使用最新的 Wasserstein Loss (論文提到的新東西)

你的 README 提到 4.2.0 版支援 --tune=wasserstein。

實驗： 比較原本的 MSE loss 和新的 Wasserstein loss。

修改方式： 修改 run_coolchic.sh，在 encode.py 的參數中加入一個變數來控制是否開啟 --tune=wasserstein。

第三階段：專題報告撰寫結構

當你做完上述實驗，你的報告結構應該如下：

Introduction: 介紹 Image Compression 和 Cool-chic (Overfitted neural network) 的原理。

Implementation: 描述你如何架設 Cool-chic 環境 (Hardware, Software stack)。

Proposed Improvement / Experiment: 描述你做了什麼改動 (例如：為了加速，我調整了 Learning Rate Scheduler 或迭代次數)。

Evaluation Results:

放一張 R-D Curve 圖：X軸是 BPP (Bitrate)，Y軸是 PSNR (Quality)。

圖上要有：Cool-chic (Default), Cool-chic (Modified), JPEG, WebP。

分析：在同樣的 BPP 下，Cool-chic 比 JPEG 高了多少 dB？你的改進版比原版快了多少？

Conclusion: 總結 Neural Codec 的潛力與限制 (雖然畫質好，但編碼時間長)。

建議的下一步

先執行我給你的 benchmark_baseline.py，把 JPEG/WebP 的數據跑出來。有了對照組，你做任何 Cool-chic 的實驗都會更有說服力。