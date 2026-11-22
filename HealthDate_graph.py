import glob
import gzip
import json
import os
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
import numpy as np

# フォルダを指定
directory_path = r"20261114"


file_paths = sorted(glob.glob(os.path.join(directory_path, "*.ndjson.gz")) + 
                    glob.glob(os.path.join(directory_path, "*.ndjson")))

print(f"見つかったファイル数: {len(file_paths)} 個")

acc_records = []
hr_records = []


for file_path in file_paths:
  try:
    with gzip.open(file_path, "rt", encoding="utf-8") as f:
      for line in f:
        if line.strip():
          data = json.loads(line)
          
          if "t" in data:
            base_t = data["t"]
            
            # --- 心拍数(HR)データの取得 (1Hz) ---
            if "hr" in data:
              hr_val = data["hr"]
              if hr_val > 0:
                hr_records.append({
                    "timestamp_ms": base_t, 
                    "hr": hr_val
                })

            # --- 加速度データの取得 (50Hz) ---
            if "x" in data and "y" in data and "z" in data:
              for i, (xi, yi, zi) in enumerate(zip(data["x"], data["y"], data["z"])):
                acc_records.append({
                    "timestamp_ms": base_t + (i * 20),
                    "acc_x": xi,
                    "acc_y": yi,
                    "acc_z": zi
                })
                
  except gzip.BadGzipFile:
    try:
      with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
          if line.strip():
            data = json.loads(line)
            if "t" in data:
              base_t = data["t"]
              if "hr" in data and data["hr"] > 0:
                hr_records.append({"timestamp_ms": base_t, "hr": data["hr"]})
              if "x" in data and "y" in data and "z" in data:
                for i, (xi, yi, zi) in enumerate(zip(data["x"], data["y"], data["z"])):
                  acc_records.append({"timestamp_ms": base_t + (i * 20), "acc_x": xi, "acc_y": yi, "acc_z": zi})
    except Exception as e:
       print(f"テキスト読み込みエラー ({os.path.basename(file_path)}): {e}")
  except Exception as e:
    print(f"ファイル読み込みエラー ({os.path.basename(file_path)}): {e}")


if acc_records:
  df_acc = pd.DataFrame(acc_records)
  

  df_acc['datetime'] = pd.to_datetime(df_acc['timestamp_ms'], unit='ms') + pd.Timedelta(hours=9)
  df_acc = df_acc.sort_values("datetime").reset_index(drop=True)
  
  # 活動量の計算
  df_acc['activity'] = np.maximum(np.sqrt(df_acc['acc_x']**2 + df_acc['acc_y']**2 + df_acc['acc_z']**2) - 9.80665, 0)
  
  df_hr = pd.DataFrame(hr_records)
  if not df_hr.empty:

    df_hr['datetime'] = pd.to_datetime(df_hr['timestamp_ms'], unit='ms') + pd.Timedelta(hours=9)
    df_hr = df_hr.sort_values("datetime").reset_index(drop=True)

  print(f"加速度データ: {len(df_acc)}件, 有効な心拍データ: {len(df_hr)}件")

  fig, axes = plt.subplots(5, 1, figsize=(14, 15), sharex=True)
  plt.rcParams['font.family'] = 'sans-serif'

  # 加速度 X
  axes[0].plot(df_acc['datetime'], df_acc['acc_x'], color="indianred", linewidth=2)
 
  axes[0].set_ylabel("Acc X\n(m/s²)")
  axes[0].grid(True, linestyle="--", alpha=0.6)

  # 加速度 Y
  axes[1].plot(df_acc['datetime'], df_acc['acc_y'], color="forestgreen", linewidth=2)
  axes[1].set_ylabel("Acc Y\n(m/s²)")
  axes[1].grid(True, linestyle="--", alpha=0.6)

  # 加速度 Z
  axes[2].plot(df_acc['datetime'], df_acc['acc_z'], color="royalblue", linewidth=2)
  axes[2].set_ylabel("Acc Z\n(m/s²)")
  axes[2].grid(True, linestyle="--", alpha=0.6)
  
  # 活動量
  axes[3].plot(df_acc['datetime'], df_acc['activity'], color="#ee7b00", linewidth=2)
  axes[3].set_ylabel("Activity\n(m/s²)")
  axes[3].grid(True, linestyle="--", alpha=0.6)

  # 心拍数 HR
  if not df_hr.empty:
    axes[4].plot(df_hr['datetime'], df_hr['hr'], color="purple", marker=".", markersize=4, linewidth=1.0)
    axes[4].set_ylabel("Heart Rate\n(bpm)")
  else:
    axes[4].text(0.5, 0.5, "No valid HR data (> 0)", ha='center', va='center', transform=axes[4].transAxes)
    axes[4].set_ylabel("Heart Rate")
    
  axes[4].set_xlabel("Time (JST)")
  axes[4].grid(True, linestyle="--", alpha=0.6)
  

  axes[4].xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
  fig.autofmt_xdate()

  plt.tight_layout()
  folder_name = os.path.basename(os.path.normpath(directory_path))
  output_image_path = os.path.join(directory_path, f"{folder_name}_graph.png")
  plt.savefig(output_image_path, dpi=300)
  print(f"グラフを保存しました: {output_image_path}")

  export_columns = ["datetime", "acc_x", "acc_y", "acc_z", "activity"]
  df_export = df_acc[export_columns].copy()
  if not df_hr.empty:
    df_export = df_export.merge(df_hr[["datetime", "hr"]], on="datetime", how="outer")
    df_export = df_export.sort_values("datetime").reset_index(drop=True)
  else:
    df_export["hr"] = np.nan

  output_csv_path = os.path.join(directory_path, f"{folder_name}.csv")
  df_export.to_csv(output_csv_path, index=False, encoding="utf-8-sig")
  print(f"データを保存しました: {output_csv_path}")
  
  plt.show()
else:
  print("有効なデータが読み込まれませんでした。")