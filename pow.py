import hashlib
import time
import random
from tqdm import tqdm  # 用于显示进度条

# 区块类：包含哈希计算与挖矿逻辑
class Block:
    def __init__(self, index, prev_hash, timestamp, data, nonce=0):
        self.index = index                  # 区块在链中的索引位置
        self.prev_hash = prev_hash          # 前一个区块的哈希值
        self.timestamp = timestamp          # 区块创建时间
        self.data = data                    # 区块存储的数据（本例中是标记）
        self.nonce = nonce                  # 挖矿过程中的计数器（用于改变哈希输出）
        self.hash = self.calculate_hash()   # 当前区块的哈希值，初始时就计算

    # 使用 SHA-256 计算当前区块的哈希值
    def calculate_hash(self):
        block_string = f"{self.index}{self.prev_hash}{self.timestamp}{self.data}{self.nonce}"
        return hashlib.sha256(block_string.encode('utf-8')).hexdigest()

    # 挖矿函数：不断尝试增加 nonce，使得哈希前缀为指定数量的 0（即满足难度要求）
    def mine(self, difficulty):
        target = '0' * difficulty  # 目标前缀，例如 '000' 表示难度为3
        while not self.hash.startswith(target):
            self.nonce += 1
            self.hash = self.calculate_hash()
        return self.hash  # 返回满足条件的哈希

# 节点类：代表一个诚实节点，包含其本地区块链副本
class Node:
    def __init__(self, mine_success_rate):
        self.mine_success_rate = mine_success_rate  # 每轮尝试出块的概率
        self.chain = [self.create_genesis_block()]  # 初始化时包含创世区块

    # 创建创世区块（第一个区块）
    def create_genesis_block(self):
        return Block(0, "0", time.time(), "Genesis")

    # 每一轮尝试挖出一个新区块，若成功则进行哈希计算并添加到链中
    def try_mine_block(self, difficulty):
        if random.random() < self.mine_success_rate:
            prev_block = self.chain[-1]
            new_block = Block(
                index=prev_block.index + 1,
                prev_hash=prev_block.hash,
                timestamp=time.time(),
                data="Honest"
            )
            new_block.mine(difficulty)
            self.chain.append(new_block)  # 添加成功挖出的新区块

def select_chain(nodes):
    max_len = max(len(node.chain) for node in nodes)  # 找出最长链长度
    candidates = [node for node in nodes if len(node.chain) == max_len]  # 所有拥有最长链的节点
    chosen = random.choice(candidates)  # 随机选一个作为标准链
    for node in nodes:
        node.chain = chosen.chain.copy()  # 所有节点同步为标准链副本
    return chosen.chain  # 返回当前的全网统一链

def simulate_blockchain(node_count, difficulty, rounds, success_rate, seed=None):
    if seed is not None:
        random.seed(seed)  # 固定随机种子，确保结果可重复

    # 初始化所有节点（诚实节点），使用统一出块概率
    nodes = [Node(success_rate) for _ in range(node_count)]
    prev_length = 1  # 初始链长度为1（只有创世块）

    with tqdm(total=rounds) as pbar:  # 使用 tqdm 显示进度
        for r in range(1, rounds + 1):  # 从第1轮开始
            for node in nodes:
                node.try_mine_block(difficulty)  # 每个节点尝试出块（有成功率）

            selected_chain = select_chain(nodes)  # 所有节点统一到最长链
            current_length = len(selected_chain)  # 当前链长度
            growth_rate = (current_length - prev_length) / r  # 当前平均增长率
            pbar.set_description(f"Chain Growth Rate: {growth_rate:.4f}")  # 实时更新增长率
            pbar.update(1)

    # 打印最终增长率（即每轮平均新增区块数）
    final_growth_rate = (current_length - prev_length) / rounds
    print(f"\nFinal Blockchain Growth Rate (Node Count={node_count}, Success Rate={success_rate}) = {final_growth_rate:.6f}")

if __name__ == "__main__":
    node_count1 = 500
    block_success_rate1 = 1e-4
    block_success_rates = [1e-5, 1e-4, 1e-3, 1e-2]
    node_counts = [100, 500, 1000, 2000]
    rounds = 2000
    difficulty = 2
    seed = 42

    for block_success_rate in block_success_rates:
        simulate_blockchain(node_count1, difficulty, rounds, block_success_rate, seed)

    for node_count in node_counts:
        simulate_blockchain(node_count, difficulty, rounds, block_success_rate1, seed)

