# HK节点SSH连接优化指南

## 问题诊断结果 (2026-03-12)

### 症状
- SSH连接经常超时
- 连接频繁断开
- 响应很慢/卡顿
- 传输文件中断

### 根本原因
**网络路径不稳定**：本地到HK节点(103.59.103.85)的直连路径中间存在不稳定的网络节点/防火墙，导致TCP连接建立失败。

### 解决方案
**使用跳板模式**：通过阿里云节点(139.224.42.111)中转，绕过有问题的网络段。

---

## 使用方式

### ⭐ 推荐方式：跳板连接（最稳定）

```bash
# 通过阿里云跳板连接到HK节点
ssh hk-jump

# 或者使用别名
ssh hk-stable
```

**优点**：
- 连接成功率接近100%
- 适合长时间操作
- 适合大文件传输

**缺点**：
- 多一跳，延迟增加约10-20ms
- 需要阿里云节点可达

### 备用方式：直连（不稳定）

```bash
# 直接连接HK节点（可能超时）
ssh hk
```

**仅适用于**：
- 跳板机不可用时
- 简单快速操作

---

## 已应用的优化

所有HK节点连接已应用以下优化：

| 参数 | 原值 | 新值 | 说明 |
|------|------|------|------|
| ServerAliveInterval | 30秒 | 10秒 | 心跳间隔缩短，快速检测断线 |
| ServerAliveCountMax | 3次 | 5次 | 增加容忍度，避免误判 |
| ControlPersist | 10分钟 | 60分钟 | 连接复用保持更久，减少重连 |

---

## 常用操作示例

### 1. 常规登录

```bash
# 使用跳板模式（推荐）
ssh hk-jump

# 直连（不稳定）
ssh hk
```

### 2. 文件传输

```bash
# 上传文件
scp local-file.txt hk-jump:/root/destination/

# 下载文件
scp hk-jump:/root/source.txt ./

# 上传目录
scp -r local-dir/ hk-jump:/root/destination/

# 使用rsync（更可靠）
rsync -avz --progress local-dir/ hk-jump:/root/destination/
```

### 3. 长时间操作

```bash
# 使用screen保持会话
ssh hk-jump
screen -S work-session
# 执行长时间操作...
# Ctrl+A+D 分离会话

# 重新连接
ssh hk-jump
screen -r work-session
```

### 4. 调试命令

```bash
# 测试连接
ssh hk-jump "uptime"

# 查看服务器状态
ssh hk-jump "free -h && df -h"

# 查看最近的错误日志
ssh hk-jump "journalctl -xe -n 50"
```

---

## 故障排查

### 问题：跳板连接失败

**原因**：阿里云节点不可达

**解决方案**：
1. 检查网络连接
2. 尝试直连 `ssh hk`
3. 检查阿里云节点状态

### 问题：连接中断

**原因**：网络波动

**解决方案**：
1. 使用screen/tmux保持会话
2. 使用autossh自动重连：
   ```bash
   autossh -M 0 hk-jump
   ```

### 问题：文件传输慢

**解决方案**：
1. 使用rsync而不是scp
2. 启用压缩：
   ```bash
   scp -C file.txt hk-jump:/root/
   rsync -avzz src/ hk-jump:/dst/
   ```

---

## 测试脚本

运行连接性测试：

```bash
cd /Users/kjonekong/Documents/cb-Business
./scripts/ssh-connectivity-test.sh
```

---

## 配置文件位置

- SSH配置: `~/.ssh/config`
- 备份配置: `~/.ssh/config.backup.*`
- 优化配置: `~/.ssh/config.cb-business-optimized`

---

## 技术细节

### 网络诊断数据

| 指标 | 数值 |
|------|------|
| 目标IP | 103.59.103.85 |
| 跳板IP | 139.224.42.111 |
| 平均延迟 | ~35ms |
| 丢包率 | ~3% |
| 延迟波动 | ±8ms |

### Traceroute分析

```
本地 → 网关 → ISP节点 → ... → [多个超时节点] → HK节点
                                    ↑
                              问题区域
```

跳板路径：
```
本地 → 阿里云节点 → HK节点
          ↑           ↑
       稳定路径     稳定路径
```

---

*最后更新: 2026-03-12*
