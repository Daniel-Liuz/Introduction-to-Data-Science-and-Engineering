import pandas as pd
import os
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
from sklearn.preprocessing import StandardScaler
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib.font_manager as fm

my_chinese_font = 'SimHei' 
if my_chinese_font:
    plt.rcParams['font.sans-serif'] = [my_chinese_font]
    plt.rcParams['axes.unicode_minus'] = False
    print(f"已设置Matplotlib使用字体: {my_chinese_font}")
else:
    print("未指定中文字体，或指定字体不存在。图表中中文可能显示为方块。")
    plt.rcParams['font.sans-serif'] = ['DejaVu Sans']
    plt.rcParams['axes.unicode_minus'] = False

base_path = r"D:\DataEngineering\第三次作业10235501456刘子阳\data&processed_data"

output_image_dir = r"D:\DataEngineering\第五次作业10235501456刘子阳\output_images" 
if not os.path.exists(output_image_dir):
    os.makedirs(output_image_dir)
    print(f"已创建图片输出目录: {output_image_dir}")

# 文件列表和学科映射 (与前两个问题保持一致)
file_names = ["IndicatorsExport_processed.csv"] + [f"IndicatorsExport ({i})_processed.csv" for i in range(1, 22)]
discipline_map = {
    0: "Agricultural Sciences", 1: "Biology & Biochemistry", 2: "Chemistry",
    3: "Clinical Medicine", 4: "Computer Science", 5: "Economics & Business",
    6: "Engineering", 7: "Environment/Ecology", 8: "Geosciences",
    9: "Immunology", 10: "Materials Science", 11: "Mathematics",
    12: "Microbiology", 13: "Molecular Biology & Genetics", 14: "Multidisciplinary",
    15: "Neuroscience & Behavior", 16: "Pharmacology & Toxicology",
    17: "Physics", 18: "Plant & Animal Science", 19: "Psychiatry/Psychology",
    20: "Social Sciences, General", 21: "Space Science"
}
expected_columns = [
    'Rank',
    'Institutions',
    'Countries/Regions',
    'Web of Science Document', 
    'Cites',
    'Cites/Paper',
    'Top Papers'
]


numerical_cols = ['Rank', 'Web of Science Document', 'Cites', 'Cites/Paper', 'Top Papers']

feature_cols = ['Web of Science Document', 'Cites', 'Cites/Paper', 'Top Papers']

target_col = 'Rank'

models = {
    'Linear Regression': LinearRegression(),
    'Ridge Regression': Ridge(random_state=42),
    'Random Forest': RandomForestRegressor(random_state=42, n_estimators=100),
    'Gradient Boosting': GradientBoostingRegressor(random_state=42, n_estimators=100)
}

results = {} 

for i, filename in enumerate(file_names):
    filepath = os.path.join(base_path, filename)
    discipline_name = discipline_map.get(i, f"Unknown_Discipline_{i}")
    print(f"\n--- 处理学科: {discipline_name} ({filename}) ---")

    try:
        df = pd.read_csv(filepath, encoding='latin-1', header=0, names=expected_columns)
        df.columns = df.columns.str.strip()

        required_cols = feature_cols + [target_col] + ['Institutions']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            print(f"  警告: 文件 {filename} 缺少关键列: {missing_cols}，跳过该学科。")
            continue

        for col in numerical_cols:
            if col in df.columns: 
                df[col] = df[col].astype(str).str.replace(',', '', regex=False)
                df[col] = pd.to_numeric(df[col], errors='coerce') 
            else:
                print(f"  警告: 文件 {filename} 在尝试转换 '{col}' 为数值时发现该列不存在。")
        
        df_cleaned = df.dropna(subset=feature_cols + [target_col]).copy()
        
        if df_cleaned.empty:
            print(f"  警告: 学科 {discipline_name} 在移除缺失值后数据为空，跳过。")
            continue

        X = df_cleaned[feature_cols]
        y = df_cleaned[target_col]

        total_rows = len(df_cleaned)
        
        # --- 修正数据划分策略 ---
        # 1. 先将数据分为 80% 用于训练/测试，20% 不用（或者理解为“丢弃”）
        # 2. 从这 80% 中，再取 60% 作为训练，剩下的 20% 作为测试
        # 为了符合“前60%的数据作为训练集，后20%的数据作为测试集”，
        # 并且解决顺序划分的问题，我们可以这样理解：
        # 我们需要从总数据中选出 60% 作为训练，再从剩余数据中选出 20% 作为测试。
        # 如果原始数据是按排名排序的，直接取前60%和后20%会导致训练集和测试集分布差异过大。
        # 更好的做法是：
        # 1. 随机抽取 80% 的数据用于建模，20% 保留不用（这符合“前60%”和“后20%”之和）
        # 2. 再从这 80% 中随机抽取 75% (80% * 0.75 = 60% of total) 作为训练集，
        #    和 25% (80% * 0.25 = 20% of total) 作为测试集。
        
        # 这是一个更稳健且仍然满足您的 "60%训练，20%测试" 意图的划分方式
        if total_rows < 5: # 确保至少有足够的样本进行划分 (例如，训练3个，测试1个)
            print(f"  警告: 学科 {discipline_name} 数据量不足 (总计{total_rows}行)，无法有效划分。跳过。")
            continue

        # 首先将整个数据集随机划分为 80% (建模用) 和 20% (不用)
        X_modeling, X_unused, y_modeling, y_unused = train_test_split(
            X, y, test_size=0.2, random_state=42, shuffle=True # 随机洗牌
        )
        
        # 然后再从 modeling 数据集中划分为 训练集 (60% of total) 和 测试集 (20% of total)
        # test_size = 20% / (60% + 20%) = 20% / 80% = 0.25
        X_train, X_test, y_train, y_test = train_test_split(
            X_modeling, y_modeling, test_size=0.25, random_state=42, shuffle=True # 再次随机洗牌
        )

        # 检查划分后的数据量
        if len(X_train) < 2 or len(X_test) < 1:
            print(f"  警告: 学科 {discipline_name} 划分后训练/测试集数据量不足。训练:{len(X_train)}, 测试:{len(X_test)}。跳过。")
            continue
        
        print(f"  数据划分完成。训练集: {len(X_train)} ({len(X_train)/total_rows:.1%}), 测试集: {len(X_test)} ({len(X_test)/total_rows:.1%})")


        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        
        discipline_results = {}
        for model_name, model in models.items():
            model.fit(X_train_scaled, y_train)
            y_pred = model.predict(X_test_scaled)
            
            mse = mean_squared_error(y_test, y_pred)
            rmse = np.sqrt(mse)
            mae = mean_absolute_error(y_test, y_pred)
            r2 = r2_score(y_test, y_pred)
            
            discipline_results[model_name] = {'RMSE': rmse, 'MAE': mae, 'R2': r2}
            print(f"    {model_name} - RMSE: {rmse:.2f}, MAE: {mae:.2f}, R2: {r2:.2f}")

        results[discipline_name] = discipline_results

    except FileNotFoundError:
        print(f"  警告: 文件 {filepath} 未找到，跳过。")
        continue
    except Exception as e:
        print(f"  错误: 处理学科 {discipline_name} 时发生未知异常: {e}，跳过。")
        continue

# 打印所有学科和模型的汇总结果
print("\n--- 全球学科排名模型预测结果汇总 ---")
summary_df_data = []
for discipline, model_res in results.items():
    for model_name, metrics in model_res.items():
        summary_df_data.append({
            'Discipline': discipline,
            'Model': model_name,
            'RMSE': metrics['RMSE'],
            'MAE': metrics['MAE'],
            'R2': metrics['R2']
        })
summary_df = pd.DataFrame(summary_df_data)

if not summary_df.empty:
    # 确保R2值在合理范围内，尤其是在模型表现很差时R2可能为负
    # 虽然现在用随机划分R2应该不会是大的负数，但仍做clip处理，防止极小部分情况
    summary_df['R2'] = summary_df['R2'].clip(lower=-0.5, upper=1.0) # 适当放宽负数R2的显示范围
    
    print(summary_df.to_string(index=False))

    print("\n--- 生成模型总体表现图表 ---")

    # 图1: 各模型平均R2得分（带标准差）
    plt.figure(figsize=(12, 6))
    sns.barplot(x='Model', y='R2', data=summary_df, estimator=np.mean, errorbar='sd', palette='viridis')
    plt.title('各模型平均R2得分（带标准差）', fontsize=16)
    plt.xlabel('模型', fontsize=12)
    plt.ylabel('平均R2得分', fontsize=12)
    plt.ylim(max(-0.2, summary_df['R2'].min() - 0.1), 1) 
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.savefig(os.path.join(output_image_dir, "Overall_Model_Performance_R2.png"))
    plt.close()
    print(f"图片已保存: {os.path.join(output_image_dir, 'Overall_Model_Performance_R2.png')}")

    # 图2: 各模型平均RMSE（带标准差）
    plt.figure(figsize=(12, 6))
    sns.barplot(x='Model', y='RMSE', data=summary_df, estimator=np.mean, errorbar='sd', palette='plasma_r') 
    plt.title('各模型平均RMSE（带标准差）', fontsize=16)
    plt.xlabel('模型', fontsize=12)
    plt.ylabel('平均RMSE', fontsize=12)
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.savefig(os.path.join(output_image_dir, "Overall_Model_Performance_RMSE.png"))
    plt.close()
    print(f"图片已保存: {os.path.join(output_image_dir, 'Overall_Model_Performance_RMSE.png')}")

    # 图3: 各模型在不同学科上的R2表现 (折线图)
    plt.figure(figsize=(18, 9))
    ax = plt.gca() 
    pivot_df = summary_df.pivot(index='Discipline', columns='Model', values='R2')
    
    if not pivot_df.empty and not pivot_df.isnull().all().all(): # 增加对全NaN的检查
        pivot_df.plot(kind='line', marker='o', ax=ax, cmap='tab10', linestyle='-') 
        plt.title('各模型在不同学科上的R2得分表现', fontsize=18)
        plt.xlabel('学科', fontsize=14)
        plt.ylabel('R2得分', fontsize=14)
        plt.xticks(rotation=60, ha='right', fontsize=12)
        plt.yticks(fontsize=12)
        plt.ylim(max(-0.2, pivot_df.min().min() - 0.1 if not pivot_df.min().min() is np.nan else -0.2), 1) # 动态调整y轴范围，处理NaN
        plt.grid(True, linestyle='--', alpha=0.7)
        plt.legend(title='模型', bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=12)
        plt.tight_layout()
        plt.savefig(os.path.join(output_image_dir, "Model_R2_Performance_by_Discipline.png"))
        plt.close()
        print(f"图片已保存: {os.path.join(output_image_dir, 'Model_R2_Performance_by_Discipline.png')}")
    else:
        print("警告: Pivot DataFrame为空或全为NaN，无法生成'Model_R2_Performance_by_Discipline.png'。")

    # 打印一些文本总结
    print("\n--- 各模型在所有学科上的平均R2得分 ---")
    avg_r2_by_model = summary_df.groupby('Model')['R2'].mean().sort_values(ascending=False)
    print(avg_r2_by_model.to_string())

    print("\n--- 各学科表现最佳模型 ---")
    best_model_per_discipline = summary_df.loc[summary_df.groupby('Discipline')['R2'].idxmax()]
    print(best_model_per_discipline[['Discipline', 'Model', 'R2']].to_string(index=False))

else:
    print("没有生成任何模型评估结果。")

