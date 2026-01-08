# 安装必要的库
# !pip install torchmetrics pytorch-lightning scikit-learn pandas numpy matplotlib

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

# 重新设计数据集类，适应PatchTST
class RankingDatasetV2(Dataset):
    def __init__(self, data, feature_cols, seq_len=8, stride=1):
        self.features = data[feature_cols].values
        self.targets = data['Rank'].values
        self.seq_len = seq_len
        self.stride = stride
        
        # 标准化
        self.scaler = StandardScaler()
        self.features = self.scaler.fit_transform(self.features)
        
        self.target_scaler = MinMaxScaler(feature_range=(0, 1))
        self.targets = self.target_scaler.fit_transform(self.targets.reshape(-1, 1)).flatten()
        
        # 创建序列数据
        self.sequences = []
        self.targets_seq = []
        
        for i in range(0, len(self.features) - seq_len + 1, stride):
            self.sequences.append(self.features[i:i+seq_len])
            self.targets_seq.append(self.targets[i+seq_len-1])
    
    def __len__(self):
        return len(self.sequences)
    
    def __getitem__(self, idx):
        return torch.FloatTensor(self.sequences[idx]), torch.FloatTensor([self.targets_seq[idx]])

# 修复的PatchEmbedding层
class PatchEmbedding(nn.Module):
    def __init__(self, input_dim, patch_size, embed_dim):
        super().__init__()
        self.patch_size = patch_size
        self.embed_dim = embed_dim
        
        # 计算实际的patch数量，与unfold的行为一致
        if input_dim < patch_size:
            self.num_patches = 0 # Should be caught by the min(4, input_dim) in train_patchtst_model
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
        # Note: self.pos_embed should be on the same device as x due to LightningModule's .to(device)
        x = self.proj(x) + self.pos_embed[:, :actual_num_patches, :]
        
        # 重塑回原始形状
        x = x.reshape(batch_size, seq_len, actual_num_patches, self.embed_dim)
        
        return x

# 修复的PatchTST模型
class PatchTSTModel(pl.LightningModule):
    def __init__(self, input_dim, seq_len, patch_size=4, embed_dim=64, num_heads=4, 
                 num_layers=3, dropout=0.3, learning_rate=1e-3):
        super().__init__()
        self.save_hyperparameters()
        
        # Calculate num_patches consistently
        if input_dim < patch_size:
            _num_patches_calc = 0
        else:
            _num_patches_calc = (input_dim - patch_size) // patch_size + 1
            
        self.num_patches = _num_patches_calc
        
        if self.num_patches == 0:
            raise ValueError(f"PatchTSTModel init: Calculated 0 patches with input_dim={input_dim}, patch_size={patch_size}. Cannot proceed.")
            
        self.patch_embedding = PatchEmbedding(input_dim, patch_size, embed_dim)
        
        # 计算输入到Transformer的维度
        self.transformer_input_dim = self.num_patches * embed_dim
        
        # 添加线性层来匹配Transformer的d_model
        self.projection = nn.Linear(self.transformer_input_dim, embed_dim)
        
        # Transformer编码器
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=embed_dim,
            nhead=num_heads,
            dim_feedforward=embed_dim * 4,
            dropout=dropout,
            batch_first=True
        )
        self.transformer_encoder = nn.TransformerEncoder(encoder_layer, num_layers=num_layers)
        
        # 预测头
        self.fc = nn.Sequential(
            nn.Linear(seq_len * embed_dim, 128),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Linear(64, 1),
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
        
        # 获取实际的patch数量
        # actual_num_patches = x.size(2) # Not strictly needed here, self.num_patches should be consistent
        
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
        x, y = batch
        y_hat = self(x)
        loss = self.criterion(y_hat, y)
        
        self.train_mse(y_hat, y)
        self.log('train_loss', loss, prog_bar=True)
        self.log('train_mse', self.train_mse, prog_bar=True)
        
        return loss
    
    def validation_step(self, batch, batch_idx):
        x, y = batch
        y_hat = self(x)
        loss = self.criterion(y_hat, y)
        
        self.val_mse(y_hat, y)
        self.log('val_loss', loss, prog_bar=True)
        self.log('val_mse', self.val_mse, prog_bar=True)
    
    def test_step(self, batch, batch_idx):
        x, y = batch
        y_hat = self(x)
        loss = self.criterion(y_hat, y)
        
        self.test_mse(y_hat, y)
        self.test_mape(y_hat, y)
        
        self.log('test_loss', loss)
        self.log('test_mse', self.test_mse)
        self.log('test_mape', self.test_mape)
    
    def configure_optimizers(self):
        optimizer = torch.optim.Adam(self.parameters(), lr=self.hparams.learning_rate)
        scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
            optimizer, 'min', patience=5, factor=0.5
        )
        return {
            'optimizer': optimizer,
            'lr_scheduler': {
                'scheduler': scheduler,
                'monitor': 'val_loss'
            }
        }

# 数据准备
def prepare_data_for_patchtst(data, feature_cols, seq_len=8, test_size=0.2):
    # 按学科分组创建序列数据
    train_datasets = []
    test_datasets = []
    
    for discipline in data['Discipline'].unique():
        disc_data = data[data['Discipline'] == discipline].copy()
        
        # 按引用数排序
        disc_data = disc_data.sort_values('Cites', ascending=False).reset_index(drop=True)
        
        # 分割训练测试集
        train_size = int(len(disc_data) * (1 - test_size))
        train_disc_data = disc_data.iloc[:train_size]
        test_disc_data = disc_data.iloc[train_size:]
        
        # 创建数据集
        train_dataset = RankingDatasetV2(train_disc_data, feature_cols, seq_len=seq_len)
        test_dataset = RankingDatasetV2(test_disc_data, feature_cols, seq_len=seq_len)
        
        train_datasets.append(train_dataset)
        test_datasets.append(test_dataset)
    
    # 合并数据集
    train_dataset = ConcatDataset(train_datasets)
    test_dataset = ConcatDataset(test_datasets)
    
    return train_dataset, test_dataset, train_datasets[0].scaler, train_datasets[0].target_scaler

# 训练PatchTST模型
def train_patchtst_model(data, feature_cols, seq_len=8, batch_size=32, max_epochs=50):
    # 准备数据
    train_dataset, test_dataset, scaler, target_scaler = prepare_data_for_patchtst(
        data, feature_cols, seq_len=seq_len
    )
    
    # 创建数据加载器
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True, num_workers=4, persistent_workers=True)
    test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False, num_workers=4, persistent_workers=True)
    
    # 创建模型
    input_dim = len(feature_cols)
    print(f"Input dimension: {input_dim}")
    
    # 计算合适的patch大小
    patch_size = min(4, input_dim)  # 如果输入维度小于4，使用输入维度作为patch大小
    print(f"Using patch size: {patch_size}")
    
    model = PatchTSTModel(
        input_dim=input_dim,
        seq_len=seq_len,
        patch_size=patch_size,
        embed_dim=64,
        num_heads=4,
        num_layers=3,
        dropout=0.3,
        learning_rate=1e-3
    )
    
    # 回调函数
    checkpoint_callback = ModelCheckpoint(
        monitor='val_loss',
        mode='min',
        save_top_k=1,
        dirpath='checkpoints/',
        filename='patchtst-best'
    )
    
    early_stopping = EarlyStopping(
        monitor='val_loss',
        patience=10,
        mode='min'
    )
    
    # 训练器
    trainer = pl.Trainer(
        max_epochs=max_epochs,
        callbacks=[checkpoint_callback, early_stopping],
        accelerator='auto',  # 自动检测GPU
        devices='auto',
        logger=True,
        log_every_n_steps=10,
        enable_model_summary=True
    )
    
    # 训练模型
    trainer.fit(model, train_loader, test_loader)
    
    # 测试模型 - 这会加载最佳模型权重到 'model' 实例
    trainer.test(model, test_loader, ckpt_path='best')
    
    # model实例在trainer.test后应该已经加载了最佳权重并位于正确的设备上。
    # 但为了确保万无一失，此处不作修改，依赖于Lightning的默认行为。
    
    return model, scaler, target_scaler, trainer

# 模型评估函数
def evaluate_model_performance(model, test_loader, target_scaler):
    model.eval()
    all_predictions = []
    all_targets = []
    
    with torch.no_grad():
        for x, y in test_loader:
            x = x.to(device) # Ensure input is on the device
            y_pred = model(x)
            
            # 反标准化
            predictions = target_scaler.inverse_transform(y_pred.cpu().numpy())
            true_targets = target_scaler.inverse_transform(y.cpu().numpy())
            
            all_predictions.extend(predictions.flatten())
            all_targets.extend(true_targets.flatten())
    
    # 计算评估指标
    from sklearn.metrics import mean_squared_error, mean_absolute_percentage_error
    mse = mean_squared_error(all_targets, all_predictions)
    rmse = np.sqrt(mse)
    mape = mean_absolute_percentage_error(all_targets, all_predictions) * 100
    
    # 计算排名准确率
    rank_errors = np.abs(np.array(all_predictions) - np.array(all_targets))
    accuracy_top10 = np.mean(rank_errors <= 10) * 100
    accuracy_top50 = np.mean(rank_errors <= 50) * 100
    
    print(f"\nModel Performance Evaluation:")
    print(f"MSE: {mse:.2f}")
    print(f"RMSE: {rmse:.2f}")
    print(f"MAPE: {mape:.2f}%")
    print(f"Top-10 Accuracy: {accuracy_top10:.2f}%")
    print(f"Top-50 Accuracy: {accuracy_top50:.2f}%")
    
    return {
        'mse': mse,
        'rmse': rmse,
        'mape': mape,
        'accuracy_top10': accuracy_top10,
        'accuracy_top50': accuracy_top50,
        'predictions': all_predictions,
        'targets': all_targets
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
            # 训练PatchTST模型
            print("Training PatchTST model...")
            patchtst_model, scaler, target_scaler, trainer = train_patchtst_model(
                data, feature_cols, seq_len=8, batch_size=32, max_epochs=50
            )
            
            # --- FIX: 显式地将模型移动到正确的设备 ---
            # 尽管PyTorch Lightning在trainer.test后应该会将模型留在GPU上
            # 但为了避免潜在的设备切换问题，在进行最终评估前再次确保模型在CUDA设备上。
            if torch.cuda.is_available():
                patchtst_model = patchtst_model.to(device)
                print(f"Model explicitly moved to device: {next(patchtst_model.parameters()).device}")
            # --- END FIX ---

            # 准备测试数据
            _, test_dataset, _, _ = prepare_data_for_patchtst(data, feature_cols, seq_len=8)
            test_loader = DataLoader(test_dataset, batch_size=32, shuffle=False, num_workers=4)
            
            # 评估模型性能
            print("Evaluating model performance...")
            performance_metrics = evaluate_model_performance(patchtst_model, test_loader, target_scaler)
            
            # 保存模型和相关对象
            print("Saving model and related objects...")
            torch.save({
                'model_state_dict': patchtst_model.state_dict(),
                'scaler': scaler,
                'target_scaler': target_scaler,
                'feature_cols': feature_cols,
                'discipline_map': discipline_map,
                'performance_metrics': performance_metrics
            }, 'patchtst_ranking_model.pth')
            
            print("PatchTST model trained and saved successfully!")
        else:
            print("No features created. Please check your feature engineering code.")
    else:
        print("No data available for training.")
