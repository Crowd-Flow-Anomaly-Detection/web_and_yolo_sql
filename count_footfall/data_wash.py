import os

def filter_labels(label_dir, keep_ids=[0]):
    for txt_file in os.listdir(label_dir):
        if not txt_file.endswith(".txt"):
            continue

        path = os.path.join(label_dir, txt_file)
        with open(path, 'r') as f:
            lines = f.readlines()

        # 僅保留指定類別（如 person 類別的 class_id == 0）
        new_lines = [line for line in lines if int(line.split()[0]) in keep_ids]

        with open(path, 'w') as f:
            f.writelines(new_lines)

# 路徑替換為你的實際資料夾
filter_labels("/Data/Project/feature_optimal/datasets/coco/labels/train2017")
filter_labels("/Data/Project/feature_optimal/datasets/coco/labels/val2017")


