import pandas as pd
import os
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
import matplotlib.pyplot as plt
import numpy as np

# 数据文件路径
base_path = r"D:\DataEngineering\第三次作业10235501456刘子阳\data&processed_data"

# 修正文件列表生成方式，确保有22个文件
# 根据您的描述，可能是：
# 一个没有括号的 IndicatorsExport_processed.csv
# 21个带括号的 IndicatorsExport (1)_processed.csv 到 IndicatorsExport (21)_processed.csv
# 注意：file_names[0] 将是 "IndicatorsExport_processed.csv"
# file_names[1] 将是 "IndicatorsExport (1)_processed.csv"
# ...
# file_names[21] 将是 "IndicatorsExport (21)_processed.csv"
file_names = ["IndicatorsExport_processed.csv"] + [f"IndicatorsExport ({i})_processed.csv" for i in range(1, 22)]

# 确认列表长度是22
print(f"将要处理的文件数量: {len(file_names)}") 

all_universities_data = {} 

for i, filename in enumerate(file_names):
    filepath = os.path.join(base_path, filename)
    try:
        # 确保使用latin-1编码
        df = pd.read_csv(filepath, encoding='latin-1')
        
        # *** 修正后的 discipline_map ***
        # 根据您提供的图片，将索引0对应到 "Agricultural Sciences"
        discipline_map = {
            0: "Agricultural Sciences",
            1: "Biology & Biochemistry",
            2: "Chemistry",
            3: "Clinical Medicine",
            4: "Computer Science",
            5: "Economics & Business",
            6: "Engineering",
            7: "Environment/Ecology",
            8: "Geosciences",
            9: "Immunology",
            10: "Materials Science",
            11: "Mathematics",
            12: "Microbiology",
            13: "Molecular Biology & Genetics",
            14: "Multidisciplinary",
            15: "Neuroscience & Behavior",
            16: "Pharmacology & Toxicology",
            17: "Physics",
            18: "Plant & Animal Science",
            19: "Psychiatry/Psychology",
            20: "Social Sciences, General",
            21: "Space Science" # 最后一个是 Space Science
        }

        discipline_name = discipline_map.get(i, f"Unknown_Discipline_{i}")
        
        # 预处理：处理缺失值，确保数值类型，先转为字符串再清理
        for col in ['Web of Science Documents', 'Cites', 'Cites/Paper', 'Top Papers']:
            # 尝试将列转换为字符串，如果值不是字符串，这会将其强制转换为字符串表示
            df[col] = df[col].astype(str).str.replace(',', '', regex=False)
            # 转换为数值，无法转换的变为 NaN
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # 将每个大学的指标存储起来
        for index, row in df.iterrows():
            uni_name = row['Institutions']
            if pd.isna(uni_name): # 检查uni_name是否为NaN
                continue # 如果大学名称是NaN，则跳过此行
            if uni_name not in all_universities_data:
                all_universities_data[uni_name] = {}
            
            # 确保在存储之前处理 NaN
            all_universities_data[uni_name][f'{discipline_name}_Documents'] = row['Web of Science Documents'] if pd.notna(row['Web of Science Documents']) else 0
            all_universities_data[uni_name][f'{discipline_name}_Cites'] = row['Cites'] if pd.notna(row['Cites']) else 0
            all_universities_data[uni_name][f'{discipline_name}_Cites/Paper'] = row['Cites/Paper'] if pd.notna(row['Cites/Paper']) else 0
            all_universities_data[uni_name][f'{discipline_name}_Top Papers'] = row['Top Papers'] if pd.notna(row['Top Papers']) else 0

    except FileNotFoundError:
        print(f"File not found: {filepath}")
        continue
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        continue

# 转换为DataFrame
df_universities = pd.DataFrame.from_dict(all_universities_data, orient='index')

# 填充缺失值 (例如，用0表示在该学科没有数据)
df_universities = df_universities.fillna(0)

# 特征选择：选择用于聚类的列
features = [col for col in df_universities.columns if any(s in col for s in ['Documents', 'Cites', 'Cites/Paper', 'Top Papers'])]
X = df_universities[features]

# 数据标准化
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# 确定最佳聚类数量 K (肘部法则和轮廓系数)
# 肘部法则
sse = []
for k in range(2, 11): # 尝试 2 到 10 个聚类
    kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
    kmeans.fit(X_scaled)
    sse.append(kmeans.inertia_)

plt.figure(figsize=(8, 5))
plt.plot(range(2, 11), sse, marker='o')
plt.xlabel('Number of clusters (K)')
plt.ylabel('SSE')
plt.title('Elbow Method for Optimal K')
plt.show() # 可以添加 block=True 确保图表在关闭前程序暂停

# 轮廓系数
silhouette_scores = []
for k in range(2, 11):
    kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
    cluster_labels = kmeans.fit_predict(X_scaled)
    silhouette_avg = silhouette_score(X_scaled, cluster_labels)
    silhouette_scores.append(silhouette_avg)

plt.figure(figsize=(8, 5))
plt.plot(range(2, 11), silhouette_scores, marker='o')
plt.xlabel('Number of clusters (K)')
plt.ylabel('Silhouette Score')
plt.title('Silhouette Score for Optimal K')
plt.show() # 可以添加 block=True 确保图表在关闭前程序暂停

# 假设根据上述分析，我们选择了最佳的 K 值 (例如 K=4)
optimal_k = 4 # 根据您的图表观察和业务理解

kmeans_model = KMeans(n_clusters=optimal_k, random_state=42, n_init=10)
df_universities['Cluster'] = kmeans_model.fit_predict(X_scaled)

# 分析每个聚类的特征
cluster_summary = df_universities.groupby('Cluster')[features].mean()
print("\nCluster Summary (Mean values for each feature):\n", cluster_summary)

# 找出与华东师大类似的高校
east_china_normal_uni = "EAST CHINA NORMAL UNIVERSITY"
if east_china_normal_uni in df_universities.index:
    ecnu_cluster = df_universities.loc[east_china_normal_uni, 'Cluster']
    print(f"\nEAST CHINA NORMAL UNIVERSITY belongs to Cluster: {ecnu_cluster}")

    # 找出同一聚类中的其他高校
    similar_universities = df_universities[df_universities['Cluster'] == ecnu_cluster].index.tolist()
    if east_china_normal_uni in similar_universities: # 再次检查以防万一
        similar_universities.remove(east_china_normal_uni) # 排除自己
    
    if similar_universities:
        print(f"Universities in the same cluster as EAST CHINA NORMAL UNIVERSITY:\n{similar_universities}")

        # 可以进一步计算与华东师大最接近的高校 (在同一个聚类中)
        # 获取华东师大的标准化特征向量
        ecnu_features_scaled = scaler.transform(df_universities.loc[[east_china_normal_uni], features])

        # 获取同一聚类中其他高校的标准化特征向量
        # 确保有其他高校可以进行比较
        other_uni_df = df_universities.loc[similar_universities, features]
        if not other_uni_df.empty:
            other_uni_in_cluster_scaled = scaler.transform(other_uni_df)

            from sklearn.metrics.pairwise import euclidean_distances
            distances = euclidean_distances(ecnu_features_scaled, other_uni_in_cluster_scaled)
            # 将距离与大学名称关联
            distance_map = dict(zip(similar_universities, distances[0]))
            
            # 按照距离升序排序
            sorted_similar_unis = sorted(distance_map.items(), key=lambda item: item[1])
            print(f"\nTop 5 most similar universities to EAST CHINA NORMAL UNIVERSITY in the same cluster:\n{sorted_similar_unis[:5]}")
        else:
            print(f"WARN: No other universities in Cluster {ecnu_cluster} for similarity comparison (after removing ECNU).")
    else:
        print(f"WARN: No other universities found in Cluster {ecnu_cluster} (after removing ECNU).")

else:
    print(f"EAST CHINA NORMAL UNIVERSITY not found in the dataset.")

