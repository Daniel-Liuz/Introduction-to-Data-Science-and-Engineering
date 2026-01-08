# 安装必要的库
# !pip install torchmetrics pytorch-lightning scikit-learn pandas numpy matplotlib seaborn

import pandas as pd
import numpy as np
import os
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader, ConcatDataset
import pytorch_lightning as pl
from pytorch_lightning.callbacks import ModelCheckpoint, EarlyStopping
from torchmetrics import MeanSquaredError, MeanAbsolutePercentageError
from sklearn.preprocessing import StandardScaler, MinMaxScaler
import matplotlib.pyplot as plt # 新增导入
import seaborn as sns # 新增导入

# 设置设备
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print(f"Using device: {device}")

# 设置TensorFloat-32精度
torch.set_float32_matmul_precision('medium')

# 数据文件路径 - 请根据您的实际路径修改
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
    if all_data:
        combined_df = pd.concat(all_data, ignore_index=True)
        return combined_df
    else:
        print("No data loaded. Please check your file paths.")
        return None

# 特征工程
def create_features(df):
    if df is None:
        return None, []
    
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

# 改进的数据集类：接受预训练的scaler，并对目标进行log1p转换
class ImprovedRankingDataset(Dataset):
    def __init__(self, data_features_np, data_targets_np, discipline_names_np, 
                 feature_scaler, target_scaler, seq_len=8, stride=1):
        # 使用传入的scaler进行特征标准化
        self.features = feature_scaler.transform(data_features_np)
        
        # 对原始目标进行log1p转换，然后使用传入的target_scaler进行MinMaxScaler转换
        # target_scaler 是针对 log1p 后的目标进行fit的
        self.targets_raw = data_targets_np # 保存原始目标，方便后续反转换
        self.targets_scaled_log = target_scaler.transform(np.log1p(data_targets_np).reshape(-1, 1)).flatten()
        
        self.discipline_names = discipline_names_np # 保存学科名称
        
        self.feature_scaler = feature_scaler
        self.target_scaler = target_scaler # 保存target_scaler用于反转换
        
        self.seq_len = seq_len
        self.stride = stride
        
        # 创建序列数据
        self.sequences = []
        self.targets_seq = []
        self.disciplines_seq = [] # 存储对应序列的学科
        
        for i in range(0, len(self.features) - seq_len + 1, stride):
            self.sequences.append(self.features[i:i+seq_len])
            self.targets_seq.append(self.targets_scaled_log[i+seq_len-1])
            self.disciplines_seq.append(self.discipline_names[i+seq_len-1]) # 对应目标值的学科
    
    def __len__(self):
        return len(self.sequences)
    
    def __getitem__(self, idx):
        return torch.FloatTensor(self.sequences[idx]), \
               torch.FloatTensor([self.targets_seq[idx]]), \
               self.disciplines_seq[idx] # 返回学科名称

# PatchEmbedding层 (与之前一致，只为确保num_patches计算正确)
class PatchEmbedding(nn.Module):
    def __init__(self, input_dim, patch_size, embed_dim):
        super().__init__()
        self.patch_size = patch_size
        self.embed_dim = embed_dim
        
        # 计算实际的patch数量，与unfold的行为一致
        if input_dim < patch_size:
            self.num_patches = 0
        else:
            self.num_patches = (input_dim - patch_size) // patch_size + 1
        
        if self.num_patches == 0:
            raise ValueError(f"Calculated 0 patches for input_dim={input_dim}, patch_size={patch_size}. Adjust patch_size or input_dim.")

        # 线性投影层
        self.proj = nn.Linear(patch_size, embed_dim)
        
        # 位置嵌入
        self.pos_embed = nn.Parameter(torch.zeros(1, self.num_patches, embed_dim))
    
    def forward(self, x):
        # x: (batch_size, seq_len, input_dim)
        batch_size, seq_len, input_dim = x.size()
        
        # 分割成patch
        # 使用unfold创建滑动窗口
        x = x.unfold(2, self.patch_size, self.patch_size)  # (batch_size, seq_len, num_patches, patch_size)
        
        # 获取实际的patch数量（应与self.num_patches一致）
        actual_num_patches = x.size(2)
        
        # 展平patch维度
        x = x.reshape(batch_size * seq_len, actual_num_patches, self.patch_size)
        
        # 投影和位置嵌入
        x = self.proj(x) + self.pos_embed[:, :actual_num_patches, :]
        
        # 重塑回原始形状
        x = x.reshape(batch_size, seq_len, actual_num_patches, self.embed_dim)
        
        return x

# 简化版PatchTST模型
class SimplifiedPatchTSTModel(pl.LightningModule):
    def __init__(self, input_dim, seq_len, patch_size=3, embed_dim=32, num_heads=2, 
                 num_layers=2, dropout=0.2, learning_rate=1e-3):
        super().__init__()
        self.save_hyperparameters() # 保存超参数
        
        self.patch_embedding = PatchEmbedding(input_dim, patch_size, embed_dim)
        self.num_patches = self.patch_embedding.num_patches
        
        # 计算输入到Transformer的维度
        self.transformer_input_dim = self.num_patches * embed_dim
        
        # 添加线性层来匹配Transformer的d_model
        self.projection = nn.Linear(self.transformer_input_dim, embed_dim)
        
        # 简化的Transformer结构
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=embed_dim,
            nhead=num_heads,
            dim_feedforward=embed_dim * 2,  # 减少前馈网络规模
            dropout=dropout,
            batch_first=True
        )
        self.transformer_encoder = nn.TransformerEncoder(encoder_layer, num_layers=num_layers)
        
        # 简化的预测头
        self.fc = nn.Sequential(
            nn.Linear(seq_len * embed_dim, 64),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Linear(32, 1),
            nn.Sigmoid()
        )
        
        # 损失函数和指标
        self.train_mse = MeanSquaredError()
        self.val_mse = MeanSquaredError()
        self.test_mse = MeanSquaredError()
        self.test_mape = MeanAbsolutePercentageError()
        
        self.criterion = nn.MSELoss()
    
    def forward(self, x):
        # x: (batch_size, seq_len, input_dim)
        batch_size, seq_len, input_dim = x.size()
        
        # Patch嵌入
        x = self.patch_embedding(x)  # (batch_size, seq_len, num_patches, embed_dim)
        
        # 合并patch和embed维度
        x = x.reshape(batch_size, seq_len, -1)  # (batch_size, seq_len, num_patches * embed_dim)
        
        # 投影到Transformer的d_model维度
        x = self.projection(x)  # (batch_size, seq_len, embed_dim)
        
        # Transformer编码
        x = self.transformer_encoder(x)  # (batch_size, seq_len, embed_dim)
        
        # 展平seq_len和特征维度
        x = x.reshape(batch_size, -1)  # (batch_size, seq_len * embed_dim)
        
        # 预测
        return self.fc(x)
    
    def training_step(self, batch, batch_idx):
        x, y_scaled_log, _ = batch # 解包，忽略学科
        y_hat = self(x)
        loss = self.criterion(y_hat, y_scaled_log)
        
        self.train_mse(y_hat, y_scaled_log)
        self.log('train_loss', loss, prog_bar=True)
        self.log('train_mse', self.train_mse, prog_bar=True)
        
        return loss
    
    def validation_step(self, batch, batch_idx):
        x, y_scaled_log, _ = batch # 解包，忽略学科
        y_hat = self(x)
        loss = self.criterion(y_hat, y_scaled_log)
        
        self.val_mse(y_hat, y_scaled_log)
        self.log('val_loss', loss, prog_bar=True)
        self.log('val_mse', self.val_mse, prog_bar=True)
    
    def test_step(self, batch, batch_idx):
        x, y_scaled_log, _ = batch # 解包，忽略学科
        y_hat = self(x)
        loss = self.criterion(y_hat, y_scaled_log)
        
        self.test_mse(y_hat, y_scaled_log)
        self.test_mape(y_hat, y_scaled_log) # MAPE这里是基于缩放的对数目标
        
        self.log('test_loss', loss)
        self.log('test_mse', self.test_mse)
        self.log('test_mape', self.test_mape)
    
    # 改进的优化器配置
    def configure_optimizers(self):
        optimizer = torch.optim.AdamW(self.parameters(), lr=self.hparams.learning_rate, weight_decay=1e-5)
        scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
            optimizer, T_max=self.trainer.max_epochs, eta_min=1e-6 # T_max设为最大epoch数
        )
        return {
            'optimizer': optimizer,
            'lr_scheduler': scheduler
        }

# 改进的数据准备函数：实现全局标准化
def prepare_data_for_patchtst_global_scaling(data, feature_cols, seq_len=8, test_size=0.2):
    
    aggregated_train_features = []
    aggregated_train_targets_raw = []
    
    # 用于存储按学科划分的未缩放的训练和测试数据 (包含学科名称)
    train_data_by_discipline = []
    test_data_by_discipline = []

    for discipline in data['Discipline'].unique():
        disc_data = data[data['Discipline'] == discipline].copy()
        disc_data = disc_data.sort_values('Cites', ascending=False).reset_index(drop=True)
        
        train_size = int(len(disc_data) * (1 - test_size))
        train_disc_data = disc_data.iloc[:train_size]
        test_disc_data = disc_data.iloc[train_size:]
        
        # 收集所有训练数据，用于fit全局scaler
        aggregated_train_features.append(train_disc_data[feature_cols].values)
        aggregated_train_targets_raw.append(train_disc_data['Rank'].values)

        # 存储未缩放的特征、目标和学科名称数组
        train_data_by_discipline.append((train_disc_data[feature_cols].values, train_disc_data['Rank'].values, train_disc_data['Discipline'].values))
        test_data_by_discipline.append((test_disc_data[feature_cols].values, test_disc_data['Rank'].values, test_disc_data['Discipline'].values))

    # Fit 全局特征Scaler
    global_feature_scaler = StandardScaler()
    global_feature_scaler.fit(np.vstack(aggregated_train_features))

    # Fit 全局目标Scaler (对log1p后的目标进行MinMax缩放)
    global_target_scaler = MinMaxScaler(feature_range=(0, 1))
    global_target_scaler.fit(np.log1p(np.concatenate(aggregated_train_targets_raw)).reshape(-1, 1))

    # 使用全局scaler创建最终的Dataset实例
    final_train_datasets = []
    final_test_datasets = []

    for features, targets, disciplines in train_data_by_discipline:
        final_train_datasets.append(
            ImprovedRankingDataset(features, targets, disciplines, global_feature_scaler, global_target_scaler, seq_len=seq_len)
        )
    for features, targets, disciplines in test_data_by_discipline:
        final_test_datasets.append(
            ImprovedRankingDataset(features, targets, disciplines, global_feature_scaler, global_target_scaler, seq_len=seq_len)
        )

    # 合并数据集
    train_dataset = ConcatDataset(final_train_datasets)
    test_dataset = ConcatDataset(final_test_datasets)
    
    return train_dataset, test_dataset, global_feature_scaler, global_target_scaler

# 改进的训练PatchTST模型函数
def train_improved_patchtst(data, feature_cols, seq_len=8, batch_size=64, max_epochs=100):
    # 准备数据，使用全局标准化
    train_dataset, test_dataset, scaler, target_scaler = prepare_data_for_patchtst_global_scaling(
        data, feature_cols, seq_len=seq_len
    )
    
    # 创建数据加载器
    # 确保num_workers在Windows上运行时设置为0或根据您的系统和数据量进行调整以避免问题
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True, num_workers=2, persistent_workers=True)
    test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False, num_workers=2, persistent_workers=True)
    
    # 创建模型
    input_dim = len(feature_cols)
    print(f"Input dimension: {input_dim}")
    
    # 使用更小的patch size
    patch_size = min(3, input_dim)  # 如果输入维度小于3，使用输入维度作为patch大小
    print(f"Using patch size: {patch_size}")
    
    model = SimplifiedPatchTSTModel( # 使用简化模型
        input_dim=input_dim,
        seq_len=seq_len,
        patch_size=patch_size,
        embed_dim=32,       # 减小嵌入维度
        num_heads=2,        # 减小注意力头数
        num_layers=2,       # 减小Transformer层数
        dropout=0.2,        # 调整dropout
        learning_rate=5e-4  # 使用更小的学习率
    )
    
    # 回调函数
    checkpoint_callback = ModelCheckpoint(
        monitor='val_loss',
        mode='min',
        save_top_k=1,
        dirpath='checkpoints/',
        filename='improved-patchtst-best' # 修改文件名
    )
    
    # 调整early stopping参数
    early_stopping = EarlyStopping(
        monitor='val_loss',
        patience=20,    # 增加耐心
        mode='min',
        min_delta=1e-5  # 更小的变化阈值
    )
    
    # 训练器
    trainer = pl.Trainer(
        max_epochs=max_epochs,
        callbacks=[checkpoint_callback, early_stopping],
        accelerator='auto',  # 自动检测GPU
        devices='auto',
        logger=True,
        log_every_n_steps=10,
        enable_model_summary=True,
        gradient_clip_val=1.0,  # 添加梯度裁剪
        # limit_train_batches=0.01, # For quick testing, uncomment this
        # limit_val_batches=0.01,   # For quick testing, uncomment this
        # limit_test_batches=0.01   # For quick testing, uncomment this
    )
    
    # 训练模型
    trainer.fit(model, train_loader, test_loader)
    
    # 测试模型 - 这会加载最佳模型权重到 'model' 实例
    trainer.test(model, test_loader, ckpt_path='best')
    
    return model, scaler, target_scaler, trainer # 返回全局scaler和target_scaler

# 模型评估函数（增强版，包含可视化和误差分析）
def evaluate_model_performance(model, test_loader, target_scaler, output_dir='plots', discipline_map=None):
    model.eval()
    all_predictions = []
    all_targets = []
    all_disciplines = [] # 新增：存储所有学科名称
    
    with torch.no_grad():
        for x, y_scaled_log, disciplines in test_loader: # 解包时获取学科
            x = x.to(device) # Ensure input is on the device
            y_pred_scaled_log = model(x) # 模型预测的是 log1p 后的缩放值
            
            # 将预测值和真实值从GPU移到CPU，并转换为numpy
            y_pred_scaled_log_np = y_pred_scaled_log.cpu().numpy()
            y_scaled_log_np = y_scaled_log.cpu().numpy() # 原始代码中变量名是y，现在是y_scaled_log
            
            # 反标准化和反log1p转换
            predictions = np.expm1(target_scaler.inverse_transform(y_pred_scaled_log_np)).flatten()
            true_targets = np.expm1(target_scaler.inverse_transform(y_scaled_log_np)).flatten()
            
            all_predictions.extend(predictions)
            all_targets.extend(true_targets)
            all_disciplines.extend(disciplines) # 扩展学科名称列表
    
    # 将列表转换为numpy数组以便后续计算
    all_predictions = np.array(all_predictions)
    all_targets = np.array(all_targets)
    all_disciplines = np.array(all_disciplines)

    # 计算评估指标
    from sklearn.metrics import mean_squared_error, mean_absolute_percentage_error
    mse = mean_squared_error(all_targets, all_predictions)
    rmse = np.sqrt(mse)
    
    # MAPE需要原始值，避免0除
    # 注意：sklearn的mape会报错如果存在0，所以需要确保target_scaler.inverse_transform返回的值不会有0
    # 通常情况下，排名从1开始，所以不会是0。
    mape = mean_absolute_percentage_error(all_targets, all_predictions) * 100
    
    # 计算排名准确率
    rank_errors = np.abs(all_predictions - all_targets) # 直接使用numpy数组
    accuracy_top10 = np.mean(rank_errors <= 10) * 100
    accuracy_top50 = np.mean(rank_errors <= 50) * 100
    
    print(f"\nModel Performance Evaluation:")
    print(f"MSE: {mse:.2f}")
    print(f"RMSE: {rmse:.2f}")
    print(f"MAPE: {mape:.2f}%")
    print(f"Top-10 Accuracy: {accuracy_top10:.2f}%")
    print(f"Top-50 Accuracy: {accuracy_top50:.2f}%")

    # --- 新增：可视化预测结果 ---
    print(f"\nGenerating prediction plots in {output_dir}...")
    os.makedirs(output_dir, exist_ok=True) # 确保输出目录存在

    plt.figure(figsize=(10, 8))
    sns.scatterplot(x=all_targets, y=all_predictions, alpha=0.6, hue=all_disciplines, s=20) # 添加学科区分
    plt.plot([min(all_targets), max(all_targets)], [min(all_targets), max(all_targets)], 'r--', lw=2, label='Perfect Prediction')
    plt.xlabel("True Rank")
    plt.ylabel("Predicted Rank")
    plt.title("True vs. Predicted Ranks (by Discipline)")
    plt.legend()
    plt.grid(True)
    plt.savefig(os.path.join(output_dir, 'true_vs_predicted_ranks.png'))
    plt.close()
    print(f"Plot saved: {os.path.join(output_dir, 'true_vs_predicted_ranks.png')}")

    # --- 新增：分析最大误差样本 ---
    print("\nAnalyzing samples with largest absolute errors (Top 10):")
    error_df = pd.DataFrame({
        'True_Rank': all_targets,
        'Predicted_Rank': all_predictions,
        'Absolute_Error': rank_errors,
        'Discipline': all_disciplines
    })
    error_df_sorted = error_df.sort_values(by='Absolute_Error', ascending=False)
    print(error_df_sorted.head(10).round(2).to_string()) # 四舍五入到小数点后两位并打印

    # 新增：分段 RMSE 分析 (可选，您可以取消注释查看)
    # print("\nSegmented RMSE Analysis:")
    # rank_bins = [0, 100, 500, 1000, np.inf]
    # rank_labels = ['1-100', '101-500', '501-1000', '1001+']
    # error_df['Rank_Bin'] = pd.cut(error_df['True_Rank'], bins=rank_bins, labels=rank_labels, right=True)
    #
    # for r_bin in rank_labels:
    #     subset = error_df[error_df['Rank_Bin'] == r_bin]
    #     if len(subset) > 0:
    #         bin_rmse = np.sqrt(mean_squared_error(subset['True_Rank'], subset['Predicted_Rank']))
    #         print(f"  RMSE for True Ranks {r_bin}: {bin_rmse:.2f} (N={len(subset)})")
    #     else:
    #         print(f"  No data for True Ranks {r_bin}")

    return {
        'mse': mse,
        'rmse': rmse,
        'mape': mape,
        'accuracy_top10': accuracy_top10,
        'accuracy_top50': accuracy_top50,
        'predictions': all_predictions, # 返回预测值
        'targets': all_targets,       # 返回真实值
        'disciplines': all_disciplines # 返回对应学科
    }

# 使用改进后的模型
if __name__ == "__main__":
    # 创建必要的目录
    os.makedirs('checkpoints', exist_ok=True)
    os.makedirs('plots', exist_ok=True)
    
    # 加载和预处理数据
    print("Loading and preparing data...")
    data = load_and_prepare_data()
    
    if data is not None and len(data) > 0:
        print(f"Loaded {len(data)} data points")
        
        # 创建特征
        print("Creating features...")
        data, feature_cols = create_features(data)
        print(f"Created {len(feature_cols)} features")
        
        if len(feature_cols) > 0:
            # 训练改进的PatchTST模型
            print("Training Improved PatchTST model...")
            # 注意 prepare_data_for_patchtst_global_scaling 的返回参数
            patchtst_model, feature_scaler, target_scaler, trainer = train_improved_patchtst(
                data, feature_cols, seq_len=8, batch_size=64, max_epochs=100
            )
            
            # 显式地将模型移动到正确的设备，以防trainer.test之后设备状态发生变化
            if torch.cuda.is_available():
                patchtst_model = patchtst_model.to(device)
                print(f"Model explicitly moved to device: {next(patchtst_model.parameters()).device}")

            # 准备测试数据，确保使用全局scaler
            # 注意：prepare_data_for_patchtst_global_scaling 返回的 test_dataset 已经封装了 global_feature_scaler 和 global_target_scaler
            _, test_dataset_for_eval, _, _ = prepare_data_for_patchtst_global_scaling(data, feature_cols, seq_len=8)
            # 在这里，我们再次创建test_loader，以确保它可以正确地迭代，并且 num_workers 等设置是用于评估的。
            test_loader_for_eval = DataLoader(test_dataset_for_eval, batch_size=64, shuffle=False, num_workers=2)
            
            # 评估模型性能
            print("Evaluating model performance...")
            performance_metrics = evaluate_model_performance(patchtst_model, test_loader_for_eval, target_scaler, 
                                                             output_dir='plots', discipline_map=discipline_map) # 传入discipline_map
            
            # 保存模型和相关对象
            print("Saving model and related objects...")
            torch.save({
                'model_state_dict': patchtst_model.state_dict(),
                'feature_scaler': feature_scaler, # 保存全局特征scaler
                'target_scaler': target_scaler,   # 保存全局目标scaler
                'feature_cols': feature_cols,
                'discipline_map': discipline_map,
                'performance_metrics': performance_metrics
            }, 'improved_patchtst_ranking_model.pth')
            
            print("Improved PatchTST model trained and saved successfully!")
        else:
            print("No features created. Please check your feature engineering code.")
    else:
        print("No data available for training.")
