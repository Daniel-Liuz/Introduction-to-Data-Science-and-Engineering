import pandas as pd
import os
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
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

df_all_disciplines = pd.DataFrame() 

print("--- 正在整合所有学科数据 ---")

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
metrics_for_plot = ['Rank', 'Web of Science Document', 'Cites', 'Cites/Paper', 'Top Papers']


for i, filename in enumerate(file_names):
    filepath = os.path.join(base_path, filename)
    discipline_name = discipline_map.get(i, f"Unknown_Discipline_{i}")
    try:
        df = pd.read_csv(filepath, encoding='latin-1', header=0, names=expected_columns)
        
        df.columns = df.columns.str.strip()

        missing_cols_after_read = [col for col in expected_columns if col not in df.columns]
        if missing_cols_after_read:
            print(f"  警告: 文件 {filename} 在指定列名后仍缺少关键列: {missing_cols_after_read}，跳过。")
            continue

        for col in numerical_cols:
            if col in df.columns: 
                df[col] = df[col].astype(str).str.replace(',', '', regex=False)
                df[col] = pd.to_numeric(df[col], errors='coerce') 
            else:
                print(f"  警告: 文件 {filename} 在尝试转换 '{col}' 为数值时发现该列不存在。")


        df['Discipline'] = discipline_name
        df_all_disciplines = pd.concat([df_all_disciplines, df], ignore_index=True)
        print(f"  已成功处理 {discipline_name} ({filename})")
    except FileNotFoundError:
        print(f"  警告: 文件 {filepath} 未找到，跳过。")
        continue
    except Exception as e: 
        print(f"  错误: 读取或处理文件 {filepath} 时发生未知异常: {e}，跳过。")
        continue

print(f"\n所有学科数据整合完成。总记录数: {len(df_all_disciplines)}")

east_china_normal_uni = "EAST CHINA NORMAL UNIVERSITY"
if 'Institutions' not in df_all_disciplines.columns or df_all_disciplines['Institutions'].empty:
    print("\n错误: 整合后的数据中没有'Institutions'列或该列为空，无法进行华东师范大学的分析。")
    ecnu_data = pd.DataFrame() 
else:
    ecnu_data = df_all_disciplines[df_all_disciplines['Institutions'] == east_china_normal_uni].copy() 

if not ecnu_data.empty:
    print(f"\n--- 学科画像：{east_china_normal_uni} ---")
    
    ranked_disciplines = ecnu_data['Discipline'].dropna().tolist()
    print(f"1. 华东师范大学有排名的学科数量: {len(ranked_disciplines)} / {len(discipline_map)}")
    print(f"   有排名的学科列表: {', '.join(ranked_disciplines)}")
    
    all_discipline_names = list(discipline_map.values())
    unranked_disciplines = [d for d in all_discipline_names if d not in ranked_disciplines]
    if unranked_disciplines:
        print(f"   没有排名的学科列表: {', '.join(unranked_disciplines)}")
    else:
        print("   华东师范大学在所有学科都有排名！")

    plot_data_ecnu = ecnu_data.dropna(subset=['Rank']).sort_values(by='Rank', ascending=True)

    if not plot_data_ecnu.empty:
        plt.figure(figsize=(14, 7))
        sns.barplot(x='Discipline', y='Rank', hue='Discipline', data=plot_data_ecnu, palette='coolwarm_r', legend=False) 
        plt.title(f'{east_china_normal_uni} 各学科排名表现', fontsize=16)
        plt.xlabel('学科', fontsize=12)
        plt.ylabel('排名', fontsize=12)
        plt.xticks(rotation=60, ha='right', fontsize=10) # 移除 ha 参数
        plt.yticks(fontsize=10)
        plt.grid(axis='y', linestyle='--', alpha=0.7)
        plt.tight_layout()
        plt.savefig(os.path.join(output_image_dir, f"{east_china_normal_uni}_Discipline_Rank.png")) # 保存图片
        plt.close() 
        print(f"图片已保存: {os.path.join(output_image_dir, f'{east_china_normal_uni}_Discipline_Rank.png')}")

        fig, axes = plt.subplots(nrows=2, ncols=2, figsize=(18, 12))
        fig.suptitle(f'{east_china_normal_uni} 各学科科研产出与影响力', fontsize=18)

        plot_data_ecnu_sorted_docs = plot_data_ecnu.sort_values(by='Web of Science Document', ascending=False)
        sns.barplot(x='Discipline', y='Web of Science Document', hue='Discipline', data=plot_data_ecnu_sorted_docs, ax=axes[0, 0], palette='viridis', legend=False)
        axes[0, 0].set_title('Web of Science 文献数量', fontsize=14)
        axes[0, 0].set_xlabel('学科', fontsize=12)
        axes[0, 0].set_ylabel('文献数量', fontsize=12)
        axes[0, 0].tick_params(axis='x', rotation=60, labelsize=10) 
        axes[0, 0].tick_params(axis='y', labelsize=10)

        plot_data_ecnu_sorted_cites = plot_data_ecnu.sort_values(by='Cites', ascending=False)
        sns.barplot(x='Discipline', y='Cites', hue='Discipline', data=plot_data_ecnu_sorted_cites, ax=axes[0, 1], palette='plasma', legend=False)
        axes[0, 1].set_title('总引用次数', fontsize=14)
        axes[0, 1].set_xlabel('学科', fontsize=12)
        axes[0, 1].set_ylabel('引用次数', fontsize=12)
        axes[0, 1].tick_params(axis='x', rotation=60, labelsize=10) 
        axes[0, 1].tick_params(axis='y', labelsize=10)

        plot_data_ecnu_sorted_cites_paper = plot_data_ecnu.sort_values(by='Cites/Paper', ascending=False)
        sns.barplot(x='Discipline', y='Cites/Paper', hue='Discipline', data=plot_data_ecnu_sorted_cites_paper, ax=axes[1, 0], palette='magma', legend=False)
        axes[1, 0].set_title('篇均引用次数', fontsize=14)
        axes[1, 0].set_xlabel('学科', fontsize=12)
        axes[1, 0].set_ylabel('篇均引用', fontsize=12)
        axes[1, 0].tick_params(axis='x', rotation=60, labelsize=10) 
        axes[1, 0].tick_params(axis='y', labelsize=10)

        plot_data_ecnu_sorted_top_papers = plot_data_ecnu.sort_values(by='Top Papers', ascending=False)
        sns.barplot(x='Discipline', y='Top Papers', hue='Discipline', data=plot_data_ecnu_sorted_top_papers, ax=axes[1, 1], palette='cividis', legend=False)
        axes[1, 1].set_title('顶尖论文数量', fontsize=14)
        axes[1, 1].set_xlabel('学科', fontsize=12)
        axes[1, 1].set_ylabel('顶尖论文数量', fontsize=12)
        axes[1, 1].tick_params(axis='x', rotation=60, labelsize=10) 
        axes[1, 1].tick_params(axis='y', labelsize=10)

        plt.tight_layout(rect=[0, 0.03, 1, 0.95])
        plt.savefig(os.path.join(output_image_dir, f"{east_china_normal_uni}_Scientific_Output_and_Impact.png")) 
        plt.close()
        print(f"图片已保存: {os.path.join(output_image_dir, f'{east_china_normal_uni}_Scientific_Output_and_Impact.png')}")

    else:
        print("华东师范大学在任何学科中都没有有效的排名数据以供可视化。")

    print("\n3. 华东师范大学各项指标与全球平均水平的比较 (正值表示高于平均水平):")
    global_avg_metrics = df_all_disciplines.groupby('Discipline')[metrics_for_plot].mean().reset_index()
    
    comparison_df = pd.merge(ecnu_data[['Discipline'] + metrics_for_plot], 
                             global_avg_metrics, 
                             on='Discipline', 
                             suffixes=('_ECNU', '_Global_Avg'))
    
    for metric in metrics_for_plot:
        comparison_df[f'{metric}_Difference'] = comparison_df[f'{metric}_ECNU'] - comparison_df[f'{metric}_Global_Avg']
    
    display_diff_cols = [f'{m}_Difference' for m in metrics_for_plot if m != 'Rank']
    print(comparison_df[['Discipline'] + display_diff_cols].set_index('Discipline'))

    plot_diff_df = comparison_df[['Discipline'] + display_diff_cols].set_index('Discipline').dropna()

    if not plot_diff_df.empty:
        plt.figure(figsize=(16, 8))
        sns.barplot(x=plot_diff_df.index, y=plot_diff_df[display_diff_cols[0]], color='skyblue', label=display_diff_cols[0], ax=plt.gca()) # 绘制第一个指标
        for col_idx in range(1, len(display_diff_cols)): 
             sns.barplot(x=plot_diff_df.index, y=plot_diff_df[display_diff_cols[col_idx]], color='lightcoral' if col_idx % 2 == 0 else 'lightgreen', label=display_diff_cols[col_idx], ax=plt.gca())
        
        plt.title(f'{east_china_normal_uni} 各学科指标与全球平均水平的差异', fontsize=16)
        plt.ylabel('差异值 (华东师大 - 全球平均)', fontsize=12)
        plt.xlabel('学科', fontsize=12)
        plt.xticks(rotation=60, ha='right', fontsize=10) 
        plt.yticks(fontsize=10)
        plt.axhline(0, color='gray', linestyle='--', linewidth=1)
        plt.grid(axis='y', linestyle='--', alpha=0.7)
        plt.legend(title='指标差异', bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.tight_layout()
        plt.savefig(os.path.join(output_image_dir, f"{east_china_normal_uni}_Global_Average_Difference.png")) 
        plt.close()
        print(f"图片已保存: {os.path.join(output_image_dir, f'{east_china_normal_uni}_Global_Average_Difference.png')}")

    else:
        print("没有足够的华东师范大学与全球平均水平的比较数据以供可视化。")

    print("\n4. 优势/劣势学科详细统计:")
    
    if 'Rank' in ecnu_data.columns:
        ranked_summary = ecnu_data.dropna(subset=['Rank'])
        if not ranked_summary.empty:
            print("\n   有排名学科的排名概况:")
            print(ranked_summary[['Discipline', 'Rank']].sort_values(by='Rank').to_string(index=False))

            top_ranked = ranked_summary[ranked_summary['Rank'] <= 100]
            if not top_ranked.empty:
                print(f"\n   进入全球前100的学科 ({len(top_ranked)}个):")
                print(top_ranked[['Discipline', 'Rank', 'Cites/Paper', 'Top Papers']].to_string(index=False))
            else:
                print("\n   没有学科进入全球前100。")
            
            global_q3_cites_paper = df_all_disciplines['Cites/Paper'].quantile(0.75)
            global_q3_top_papers = df_all_disciplines['Top Papers'].quantile(0.75)

            potential_strength_disciplines = ranked_summary[
                (ranked_summary['Cites/Paper'] > global_q3_cites_paper) |
                (ranked_summary['Top Papers'] > global_q3_top_papers)
            ].sort_values(by='Cites/Paper', ascending=False)

            if not potential_strength_disciplines.empty:
                print(f"\n   篇均引用或顶尖论文显著高于全球75分位的学科 ({len(potential_strength_disciplines)}个):")
                print("(可能表示高质量研究产出，即使排名不特别高)")
                print(potential_strength_disciplines[['Discipline', 'Rank', 'Cites/Paper', 'Top Papers']].to_string(index=False))
            else:
                print("\n   没有学科在篇均引用或顶尖论文方面显著高于全球75分位。")

        else:
            print("\n   华东师范大学没有任何有排名的学科。")
    else:
        print("\n   数据中没有'Rank'列。")

    if unranked_disciplines:
        print(f"\n   没有排名的学科 ({len(unranked_disciplines)}个):")
        print(f"   {', '.join(unranked_disciplines)}")
    else:
        print("\n   华东师范大学在所有学科均有排名。")
    
    print("\n5. 科研质量与顶尖产出关系探索 (以所有有排名的学科为例):")
    if not plot_data_ecnu.empty:
        plt.figure(figsize=(12, 8))
        sns.scatterplot(x='Cites/Paper', y='Top Papers', hue='Discipline', size='Web of Science Document', 
                        sizes=(50, 800), alpha=0.7, data=plot_data_ecnu, palette='tab20', legend='full')
        
        for line in range(0, plot_data_ecnu.shape[0]):
            plt.text(plot_data_ecnu['Cites/Paper'].iloc[line]*1.01, 
                     plot_data_ecnu['Top Papers'].iloc[line]*1.01, 
                     plot_data_ecnu['Discipline'].iloc[line], 
                     horizontalalignment='left', size='small', color='black', weight='semibold')

        plt.title(f'{east_china_normal_uni} 各学科篇均引用与顶尖论文关系 (气泡大小表示文献数量)', fontsize=16)
        plt.xlabel('篇均引用次数 (Cites/Paper)', fontsize=12)
        plt.ylabel('顶尖论文数量 (Top Papers)', fontsize=12)
        plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', title='学科')
        plt.grid(True, linestyle='--', alpha=0.6)
        plt.tight_layout()
        plt.savefig(os.path.join(output_image_dir, f"{east_china_normal_uni}_Research_Quality_and_Top_Output.png")) # 保存图片
        plt.close()
        print(f"图片已保存: {os.path.join(output_image_dir, f'{east_china_normal_uni}_Research_Quality_and_Top_Output.png')}")

    else:
        print("没有足够的学科数据来分析指标之间的关系。")

else:
    print(f"EAST CHINA NORMAL UNIVERSITY not found in any discipline data or no data was loaded.")

