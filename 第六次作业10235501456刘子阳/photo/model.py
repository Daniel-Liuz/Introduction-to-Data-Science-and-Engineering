import pandas as pd
import numpy as np
import os
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn.metrics import mean_squared_error, mean_absolute_percentage_error
import matplotlib.pyplot as plt

# 创建保存图片的目录
os.makedirs('plots', exist_ok=True)
print("图片将保存到 'plots' 目录")

# 设置设备
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print(f"Using device: {device}")

# 数据文件路径
base_path = r"D:\DataEngineering\第三次作业10235501456刘子阳\data&processed_data"

# 学科映射
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
    21: "Space Science"
}

# 读取数据并创建排名
def load_and_prepare_data():
    all_data = []
    
    for i, (disc_id, disc_name) in enumerate(discipline_map.items()):
        filename = f"IndicatorsExport_processed.csv" if i == 0 else f"IndicatorsExport ({i})_processed.csv"
        filepath = os.path.join(base_path, filename)
        
        try:
            df = pd.read_csv(filepath, encoding='latin-1')
            
            # 数据预处理
            for col in ['Web of Science Documents', 'Cites', 'Cites/Paper', 'Top Papers']:
                df[col] = df[col].astype(str).str.replace(',', '', regex=False)
                df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # 填充缺失值
            df = df.fillna(0)
            
            # 创建排名 (按Cites降序排列)
            df = df.sort_values('Cites', ascending=False).reset_index(drop=True)
            df['Rank'] = df.index + 1  # 排名从1开始
            df['Discipline'] = disc_name
            df['Discipline_ID'] = disc_id
            
            all_data.append(df)
            
        except FileNotFoundError:
            print(f"File not found: {filepath}")
        except Exception as e:
            print(f"Error reading {filepath}: {e}")
    
    # 合并所有数据
    combined_df = pd.concat(all_data, ignore_index=True)
    return combined_df

# 加载数据
data = load_and_prepare_data()
print(f"Total data points: {len(data)}")

# 特征工程
def create_features(df):
    # 选择特征列
    feature_cols = ['Web of Science Documents', 'Cites', 'Cites/Paper', 'Top Papers']
    
    # 创建额外特征
    df['Log_Documents'] = np.log1p(df['Web of Science Documents'])
    df['Log_Cites'] = np.log1p(df['Cites'])
    df['Log_Cites_Per_Paper'] = np.log1p(df['Cites/Paper'])
    df['Log_Top_Papers'] = np.log1p(df['Top Papers'])
    
    # 学科独热编码
    disc_dummies = pd.get_dummies(df['Discipline'], prefix='Disc')
    df = pd.concat([df, disc_dummies], axis=1)
    
    # 更新特征列
    feature_cols.extend(['Log_Documents', 'Log_Cites', 'Log_Cites_Per_Paper', 'Log_Top_Papers'])
    feature_cols.extend(disc_dummies.columns.tolist())
    
    return df, feature_cols

# 创建特征
data, feature_cols = create_features(data)
print(f"Number of features: {len(feature_cols)}")

# 数据集类
class RankingDataset(Dataset):
    def __init__(self, data, feature_cols, scaler=None, target_scaler=None, is_training=True):
        self.features = data[feature_cols].values
        self.targets = data['Rank'].values
        
        # 特征标准化
        if is_training:
            self.scaler = StandardScaler()
            self.features = self.scaler.fit_transform(self.features)
            
            # 目标标准化 (排名)
            self.target_scaler = MinMaxScaler(feature_range=(0, 1))
            self.targets = self.target_scaler.fit_transform(self.targets.reshape(-1, 1)).flatten()
        else:
            self.scaler = scaler
            self.target_scaler = target_scaler
            self.features = self.scaler.transform(self.features)
            self.targets = self.target_scaler.transform(self.targets.reshape(-1, 1)).flatten()
        
        # 转换为张量
        self.features = torch.FloatTensor(self.features)
        self.targets = torch.FloatTensor(self.targets)
    
    def __len__(self):
        return len(self.features)
    
    def __getitem__(self, idx):
        return self.features[idx], self.targets[idx]

# 分割训练集和测试集
train_data, test_data = train_test_split(data, test_size=0.2, random_state=42, stratify=data['Discipline'])

# 创建数据集
train_dataset = RankingDataset(train_data, feature_cols, is_training=True)
test_dataset = RankingDataset(test_data, feature_cols, 
                             scaler=train_dataset.scaler, 
                             target_scaler=train_dataset.target_scaler, 
                             is_training=False)

# 创建数据加载器
train_loader = DataLoader(train_dataset, batch_size=64, shuffle=True)
test_loader = DataLoader(test_dataset, batch_size=64, shuffle=False)

# 排名预测模型
class RankingModel(nn.Module):
    def __init__(self, input_dim):
        super(RankingModel, self).__init__()
        self.network = nn.Sequential(
            nn.Linear(input_dim, 256),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.BatchNorm1d(256),
            
            nn.Linear(256, 128),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.BatchNorm1d(128),
            
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.BatchNorm1d(64),
            
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.BatchNorm1d(32),
            
            nn.Linear(32, 1),
            nn.Sigmoid()  # 输出在0-1之间，对应标准化后的排名
        )
    
    def forward(self, x):
        return self.network(x)

# 初始化模型
input_dim = len(feature_cols)
model = RankingModel(input_dim).to(device)

# 损失函数和优化器
criterion = nn.MSELoss()
optimizer = optim.Adam(model.parameters(), lr=0.001, weight_decay=1e-5)

# 学习率调度器
scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, 'min', patience=5, factor=0.5)

# 训练函数
def train_model(model, train_loader, criterion, optimizer, device, epoch):
    model.train()
    total_loss = 0
    
    for batch_idx, (data, targets) in enumerate(train_loader):
        data = data.to(device)
        targets = targets.to(device).unsqueeze(1)
        
        # 前向传播
        outputs = model(data)
        loss = criterion(outputs, targets)
        
        # 反向传播和优化
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        
        total_loss += loss.item()
        
        if batch_idx % 100 == 0:
            print(f'Epoch [{epoch}], Batch [{batch_idx}/{len(train_loader)}], Loss: {loss.item():.6f}')
    
    return total_loss / len(train_loader)

# 评估函数
def evaluate_model(model, test_loader, criterion, device, target_scaler):
    model.eval()
    total_loss = 0
    all_predictions = []
    all_targets = []
    
    with torch.no_grad():
        for data, targets in test_loader:
            data = data.to(device)
            targets = targets.to(device).unsqueeze(1)
            
            outputs = model(data)
            loss = criterion(outputs, targets)
            
            total_loss += loss.item()
            
            # 反标准化预测值和目标值
            predictions = target_scaler.inverse_transform(outputs.cpu().numpy())
            true_targets = target_scaler.inverse_transform(targets.cpu().numpy())
            
            all_predictions.extend(predictions.flatten())
            all_targets.extend(true_targets.flatten())
    
    # 计算评估指标
    mse = mean_squared_error(all_targets, all_predictions)
    rmse = np.sqrt(mse)
    mape = mean_absolute_percentage_error(all_targets, all_predictions) * 100
    
    # 计算排名准确率 (预测排名与真实排名的绝对误差)
    rank_errors = np.abs(np.array(all_predictions) - np.array(all_targets))
    accuracy_top10 = np.mean(rank_errors <= 10) * 100  # 前10名准确率
    accuracy_top50 = np.mean(rank_errors <= 50) * 100  # 前50名准确率
    
    return {
        'loss': total_loss / len(test_loader),
        'mse': mse,
        'rmse': rmse,
        'mape': mape,
        'accuracy_top10': accuracy_top10,
        'accuracy_top50': accuracy_top50,
        'predictions': all_predictions,
        'targets': all_targets,
        'rank_errors': rank_errors
    }

# 训练模型
num_epochs = 50
best_rmse = float('inf')
train_losses = []
test_losses = []
all_test_metrics = []

for epoch in range(num_epochs):
    train_loss = train_model(model, train_loader, criterion, optimizer, device, epoch)
    test_metrics = evaluate_model(model, test_loader, criterion, device, train_dataset.target_scaler)
    
    train_losses.append(train_loss)
    test_losses.append(test_metrics['loss'])
    all_test_metrics.append(test_metrics)
    
    print(f'\nEpoch [{epoch}], Train Loss: {train_loss:.6f}, Test Loss: {test_metrics["loss"]:.6f}')
    print(f'Test MSE: {test_metrics["mse"]:.2f}, RMSE: {test_metrics["rmse"]:.2f}, MAPE: {test_metrics["mape"]:.2f}%')
    print(f'Top-10 Accuracy: {test_metrics["accuracy_top10"]:.2f}%, Top-50 Accuracy: {test_metrics["accuracy_top50"]:.2f}%')
    
    # 学习率调度
    scheduler.step(test_metrics['loss'])
    
    # 保存最佳模型
    if test_metrics['rmse'] < best_rmse:
        best_rmse = test_metrics['rmse']
        torch.save(model.state_dict(), 'best_ranking_model.pth')
        print(f"Best model saved with RMSE: {best_rmse:.2f}")

# 保存训练过程中的指标
np.save('plots/train_losses.npy', np.array(train_losses))
np.save('plots/test_losses.npy', np.array(test_losses))

# 绘制训练曲线并保存
plt.figure(figsize=(12, 4))
plt.subplot(1, 2, 1)
plt.plot(train_losses, label='Train Loss')
plt.plot(test_losses, label='Test Loss')
plt.xlabel('Epoch')
plt.ylabel('Loss')
plt.title('Training and Test Loss')
plt.legend()
plt.grid(True, alpha=0.3)

# 绘制预测值vs真实值
plt.subplot(1, 2, 2)
plt.scatter(test_metrics['targets'], test_metrics['predictions'], alpha=0.5)
plt.plot([min(test_metrics['targets']), max(test_metrics['targets'])], 
         [min(test_metrics['targets']), max(test_metrics['targets'])], 
         'r--', label='Perfect Prediction')
plt.xlabel('True Rank')
plt.ylabel('Predicted Rank')
plt.title('True vs Predicted Rank')
plt.legend()
plt.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('plots/training_results.png', dpi=300, bbox_inches='tight')
plt.close()
print("训练结果图表已保存到 plots/training_results.png")

# 绘制排名误差分布
plt.figure(figsize=(10, 6))
plt.hist(test_metrics['rank_errors'], bins=50, alpha=0.7, color='skyblue', edgecolor='black')
plt.axvline(np.mean(test_metrics['rank_errors']), color='red', linestyle='--', 
           label=f'Mean Error: {np.mean(test_metrics["rank_errors"]):.2f}')
plt.axvline(10, color='green', linestyle='--', label='Top-10 Threshold')
plt.axvline(50, color='orange', linestyle='--', label='Top-50 Threshold')
plt.xlabel('Rank Error')
plt.ylabel('Frequency')
plt.title('Distribution of Rank Errors')
plt.legend()
plt.grid(True, alpha=0.3)
plt.savefig('plots/rank_error_distribution.png', dpi=300, bbox_inches='tight')
plt.close()
print("排名误差分布图已保存到 plots/rank_error_distribution.png")

# 绘制各学科的预测性能
disciplines = test_data['Discipline'].unique()
discipline_rmse = []
discipline_mape = []

for disc in disciplines:
    disc_mask = test_data['Discipline'] == disc
    disc_predictions = np.array(test_metrics['predictions'])[disc_mask]
    disc_targets = np.array(test_metrics['targets'])[disc_mask]
    
    if len(disc_predictions) > 0:
        disc_rmse = np.sqrt(mean_squared_error(disc_targets, disc_predictions))
        disc_mape = mean_absolute_percentage_error(disc_targets, disc_predictions) * 100
        
        discipline_rmse.append((disc, disc_rmse))
        discipline_mape.append((disc, disc_mape))

# 按RMSE排序
discipline_rmse.sort(key=lambda x: x[1])
disc_names, disc_errors = zip(*discipline_rmse)

plt.figure(figsize=(14, 8))
bars = plt.barh(range(len(disc_names)), disc_errors, color='lightcoral')
plt.yticks(range(len(disc_names)), disc_names)
plt.xlabel('RMSE')
plt.ylabel('Discipline')
plt.title('Prediction Performance by Discipline (RMSE)')
plt.grid(True, alpha=0.3, axis='x')

# 在柱状图上添加数值标签
for i, bar in enumerate(bars):
    width = bar.get_width()
    plt.text(width + 0.5, bar.get_y() + bar.get_height()/2, 
             f'{disc_errors[i]:.1f}', ha='left', va='center')

plt.tight_layout()
plt.savefig('plots/discipline_performance_rmse.png', dpi=300, bbox_inches='tight')
plt.close()
print("学科性能分析图已保存到 plots/discipline_performance_rmse.png")

# 绘制评估指标趋势图
plt.figure(figsize=(15, 10))

# RMSE趋势
plt.subplot(2, 2, 1)
rmse_values = [metrics['rmse'] for metrics in all_test_metrics]
plt.plot(rmse_values, marker='o', linestyle='-', color='blue')
plt.xlabel('Epoch')
plt.ylabel('RMSE')
plt.title('RMSE Trend During Training')
plt.grid(True, alpha=0.3)

# MAPE趋势
plt.subplot(2, 2, 2)
mape_values = [metrics['mape'] for metrics in all_test_metrics]
plt.plot(mape_values, marker='s', linestyle='-', color='red')
plt.xlabel('Epoch')
plt.ylabel('MAPE (%)')
plt.title('MAPE Trend During Training')
plt.grid(True, alpha=0.3)

# Top-10准确率趋势
plt.subplot(2, 2, 3)
top10_acc = [metrics['accuracy_top10'] for metrics in all_test_metrics]
plt.plot(top10_acc, marker='^', linestyle='-', color='green')
plt.xlabel('Epoch')
plt.ylabel('Top-10 Accuracy (%)')
plt.title('Top-10 Accuracy Trend During Training')
plt.grid(True, alpha=0.3)

# Top-50准确率趋势
plt.subplot(2, 2, 4)
top50_acc = [metrics['accuracy_top50'] for metrics in all_test_metrics]
plt.plot(top50_acc, marker='d', linestyle='-', color='purple')
plt.xlabel('Epoch')
plt.ylabel('Top-50 Accuracy (%)')
plt.title('Top-50 Accuracy Trend During Training')
plt.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('plots/evaluation_metrics_trends.png', dpi=300, bbox_inches='tight')
plt.close()
print("评估指标趋势图已保存到 plots/evaluation_metrics_trends.png")

# 加载最佳模型进行最终评估
model.load_state_dict(torch.load('best_ranking_model.pth'))
final_metrics = evaluate_model(model, test_loader, criterion, device, train_dataset.target_scaler)

print("\nFinal Model Evaluation:")
print(f"MSE: {final_metrics['mse']:.2f}")
print(f"RMSE: {final_metrics['rmse']:.2f}")
print(f"MAPE: {final_metrics['mape']:.2f}%")
print(f"Top-10 Accuracy: {final_metrics['accuracy_top10']:.2f}%")
print(f"Top-50 Accuracy: {final_metrics['accuracy_top50']:.2f}%")

# 保存最终评估结果到文件
with open('plots/final_evaluation.txt', 'w') as f:
    f.write("Final Model Evaluation Results:\n")
    f.write(f"MSE: {final_metrics['mse']:.2f}\n")
    f.write(f"RMSE: {final_metrics['rmse']:.2f}\n")
    f.write(f"MAPE: {final_metrics['mape']:.2f}%\n")
    f.write(f"Top-10 Accuracy: {final_metrics['accuracy_top10']:.2f}%\n")
    f.write(f"Top-50 Accuracy: {final_metrics['accuracy_top50']:.2f}%\n")
print("最终评估结果已保存到 plots/final_evaluation.txt")

# 学科排名预测函数
def predict_rank(model, university_data, discipline, feature_cols, scaler, target_scaler, device):
    """预测大学在特定学科的排名"""
    model.eval()
    
    # 创建特征向量
    features = np.zeros(len(feature_cols))
    
    # 填充基础特征
    features[feature_cols.index('Web of Science Documents')] = university_data.get('Web of Science Documents', 0)
    features[feature_cols.index('Cites')] = university_data.get('Cites', 0)
    features[feature_cols.index('Cites/Paper')] = university_data.get('Cites/Paper', 0)
    features[feature_cols.index('Top Papers')] = university_data.get('Top Papers', 0)
    
    # 填充对数特征
    features[feature_cols.index('Log_Documents')] = np.log1p(university_data.get('Web of Science Documents', 0))
    features[feature_cols.index('Log_Cites')] = np.log1p(university_data.get('Cites', 0))
    features[feature_cols.index('Log_Cites_Per_Paper')] = np.log1p(university_data.get('Cites/Paper', 0))
    features[feature_cols.index('Log_Top_Papers')] = np.log1p(university_data.get('Top Papers', 0))
    
    # 填充学科独热编码
    disc_col = f'Disc_{discipline}'
    if disc_col in feature_cols:
        features[feature_cols.index(disc_col)] = 1
    
    # 标准化特征
    features_scaled = scaler.transform([features])
    
    # 转换为张量并预测
    with torch.no_grad():
        features_tensor = torch.FloatTensor(features_scaled).to(device)
        prediction_scaled = model(features_tensor)
        prediction = target_scaler.inverse_transform(prediction_scaled.cpu().numpy())
    
    return int(round(prediction[0][0]))

# 示例：预测华东师范大学在计算机科学的排名
ecnu_cs_data = {
    'Web of Science Documents': 1500,
    'Cites': 25000,
    'Cites/Paper': 16.67,
    'Top Papers': 150
}

predicted_rank = predict_rank(model, ecnu_cs_data, 'Computer Science', 
                             feature_cols, train_dataset.scaler, 
                             train_dataset.target_scaler, device)
print(f"\nPredicted rank for ECNU in Computer Science: {predicted_rank}")

# 保存模型和相关对象
import pickle
with open('model_objects.pkl', 'wb') as f:
    pickle.dump({
        'model_state_dict': model.state_dict(),
        'scaler': train_dataset.scaler,
        'target_scaler': train_dataset.target_scaler,
        'feature_cols': feature_cols,
        'discipline_map': discipline_map
    }, f)

print("\nModel and related objects saved successfully!")
print("\n所有图片文件已保存到 'plots' 目录:")
print("1. training_results.png - 训练曲线和预测结果散点图")
print("2. rank_error_distribution.png - 排名误差分布图")
print("3. discipline_performance_rmse.png - 各学科性能分析图")
print("4. evaluation_metrics_trends.png - 评估指标趋势图")
print("5. final_evaluation.txt - 最终评估结果文本文件")