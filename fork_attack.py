import random
import time
import hashlib
from tqdm import tqdm

# 区块类：包含哈希计算与挖矿逻辑
class Block:
    def __init__(self, index, prev_hash, timestamp, data, nonce=0):
        self.index = index                  # 区块在链中的索引位置
        self.prev_hash = prev_hash          # 前一个区块的哈希值
        self.timestamp = timestamp          # 区块创建时间
        self.data = data                    # 区块存储的数据（如 "Honest" 或 "Malicious"）
        self.nonce = nonce                  # 挖矿过程中的随机数，用于改变哈希输出
        self.hash = self.calculate_hash()   # 计算初始哈希值

    def calculate_hash(self):
        # 计算当前区块的 SHA-256 哈希值
        block_string = f"{self.index}{self.prev_hash}{self.timestamp}{self.data}{self.nonce}"
        return hashlib.sha256(block_string.encode('utf-8')).hexdigest()

    def mine(self, difficulty):
        # 执行工作量证明：找到哈希前缀为 '0'*difficulty 的 nonce
        target = '0' * difficulty
        while not self.hash.startswith(target):
            self.nonce += 1
            self.hash = self.calculate_hash()
        return self.hash

# 诚实节点类
class HonestNode:
    def __init__(self, mine_success_rate):
        self.mine_success_rate = mine_success_rate  # 每轮挖矿成功概率
        self.chain = [self.create_genesis_block()]  # 初始化链，包含创世区块

    def create_genesis_block(self):
        return Block(0, "0", time.time(), "Genesis")

    def try_mine_block(self, difficulty):
        # 如果成功触发挖矿，则创建新块并执行挖矿（满足哈希难度）
        if random.random() < self.mine_success_rate:
            prev_block = self.chain[-1]
            new_block = Block(
                index=prev_block.index + 1,
                prev_hash=prev_block.hash,
                timestamp=time.time(),
                data="Honest"
            )
            new_block.mine(difficulty)
            self.chain.append(new_block)

# 恶意节点类
class MaliciousNode:
    def __init__(self, mine_success_rate):
        self.mine_success_rate = mine_success_rate  # 挖矿成功概率（可调高以模拟攻击优势）
        self.chain = [self.create_genesis_block()]  # 初始化链

    def create_genesis_block(self):
        return Block(0, "0", time.time(), "Genesis")

    def try_mine_block(self, difficulty):
        # 模拟恶意出块，与诚实节点机制相同，仅 data 字段不同
        if random.random() < self.mine_success_rate:
            prev_block = self.chain[-1]
            new_block = Block(
                index=prev_block.index + 1,
                prev_hash=prev_block.hash,
                timestamp=time.time(),
                data="Malicious"
            )
            new_block.mine(difficulty)
            self.chain.append(new_block)

# 统一最长链：所有节点切换到全网最长链副本
def select_chain(nodes):
    max_len = max(len(node.chain) for node in nodes)
    candidates = [node for node in nodes if len(node.chain) == max_len]
    chosen = random.choice(candidates)
    for node in nodes:
        node.chain = chosen.chain.copy()
    return chosen.chain

# 区块链模拟函数，评估恶意链替代主链的概率
def simulate_blockchain(node_count, malicious_rate, success_rate, rounds, difficulty, seed=None):
    if seed is not None:
        random.seed(seed)  # 固定随机种子以保证实验可复现

    honest_count = int(node_count * (1 - malicious_rate))  # 诚实节点数量
    malicious_count = node_count - honest_count            # 恶意节点数量
    threshold = 6  # 当链长度达到此阈值时判断是否结束该轮
    malicious_win_count = 0  # 恶意链替代主链的成功计数

    with tqdm(total=rounds, dynamic_ncols=False) as pbar:
        for _ in range(rounds):
            # 初始化每轮的节点
            honest_nodes = [HonestNode(success_rate) for _ in range(honest_count)]
            malicious_nodes = [MaliciousNode(success_rate) for _ in range(malicious_count)]

            # 不断尝试出块直到任一链达到阈值长度
            while True:
                for node in honest_nodes:
                    node.try_mine_block(difficulty)
                for node in malicious_nodes:
                    node.try_mine_block(difficulty)

                # 选取当前各方的最长链
                chain_honest = select_chain(honest_nodes)
                chain_malicious = select_chain(malicious_nodes)

                len_h = len(chain_honest) - 1  # 去掉创世块
                len_m = len(chain_malicious) - 1

                if len_h > threshold or len_m > threshold:
                    # 若恶意链更长或同长（随机 50% 概率胜出），视为成功
                    if len_m > len_h or (len_m == len_h and random.random() < 0.5):
                        malicious_win_count += 1
                    break  # 本轮结束
            pbar.update(1)

    print(f"Malicious Rate: {malicious_rate}, Percentage of Fork Attack Success: {(malicious_win_count / rounds):.4f}")

if __name__ == "__main__":
    node_count = 100
    malicious_rates = [0.1, 0.2, 0.3, 0.4]  # 恶意节点比例列表
    rounds = 1000
    difficulty = 2
    success_rate = 1e-4
    seed = 42

    # 分别评估不同恶意节点比例下的攻击成功率
    for malicious_rate in malicious_rates:
        simulate_blockchain(node_count, malicious_rate, success_rate, rounds, difficulty, seed=seed)