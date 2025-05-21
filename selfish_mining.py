import hashlib
import time
import random
import copy
from tqdm import tqdm

# 区块类：包含哈希计算与挖矿逻辑
class Block:
    def __init__(self, node_id, data, nonce=0):
        self.node_id = node_id  # 出块者编号（-1: 自私矿工，1: 诚实矿工）
        self.data = data  # 区块内容（用于标记来源）
        self.timestamp = time.time()  # 时间戳
        self.nonce = nonce  # 挖矿过程中使用的随机数
        self.hash = self.calculate_hash()  # 初始计算哈希值

    def calculate_hash(self):
        # 生成区块的 SHA-256 哈希值
        block_string = f"{self.node_id}{self.data}{self.timestamp}{self.nonce}"
        return hashlib.sha256(block_string.encode('utf-8')).hexdigest()

    def mine(self, difficulty):
        # 持续增加 nonce，直到找到符合难度要求的哈希前缀
        target = '0' * difficulty
        while not self.hash.startswith(target):
            self.nonce += 1
            self.hash = self.calculate_hash()
        return self.hash

# 诚实节点类：维护自己的区块链
class HonestNode:
    def __init__(self, node_id):
        self.node_id = node_id
        self.blockchain = [Block(1, "Genesis")]  # 初始创世区块

# 自私矿工类：同时维护私有链和对外广播的公开链
class SelfishNode:
    def __init__(self, node_id):
        self.node_id = node_id
        self.blockchain = [Block(-1, "Genesis")]  # 私有链
        self.public_chain = [Block(-1, "Genesis")]  # 已发布的公开链
        self.private_chain_length = 0  # 尚未发布的区块数量

# 模拟器主类
class BlockchainSimulation:
    def __init__(self, malicious_rate, rounds, seed=None):
        self.malicious_rate = malicious_rate  # 自私矿工出块概率
        self.rounds = rounds  # 总模拟轮数
        self.seed = seed  # 随机种子
        self.honest_nodes = HonestNode(1)
        self.selfish_node = SelfishNode(-1)

    def simulate(self):
        # 主循环入口
        if self.seed is not None:
            random.seed(self.seed)

        with tqdm(total=self.rounds, dynamic_ncols=False) as pbar:
            for _ in range(self.rounds):
                # 每一轮按概率判断由哪个矿工出块
                if random.random() <= self.malicious_rate:
                    self.selfish_miner(self.selfish_node)
                else:
                    self.honest_miner(self.honest_nodes)

                self.select_chain()  # 所有节点同步最长链
                if self.block_count(1) > 0:
                    # 实时更新自私矿工收益比例
                    pbar.set_description(
                        f"The proportion of selfish mining profits: {self.block_count(-1) / (self.block_count(1)+self.block_count(-1)):.4f}")
                pbar.update(1)

        # 最终输出统计信息
        print(f"Malicious Rate: {self.malicious_rate}, Selfish mining profit ratio: {self.block_count(-1) / (self.block_count(1)+self.block_count(-1)):.4f}")
        
    def select_chain(self):
        # 链同步逻辑：所有节点以最长链为准
        if len(self.selfish_node.public_chain) > len(self.honest_nodes.blockchain):
            self.honest_nodes.blockchain = copy.deepcopy(self.selfish_node.public_chain)
        elif len(self.selfish_node.public_chain) < len(self.honest_nodes.blockchain):
            self.selfish_node.public_chain = copy.deepcopy(self.honest_nodes.blockchain)
        else:
            self.honest_nodes.blockchain = copy.deepcopy(self.selfish_node.public_chain)

    def selfish_miner(self, node):
        # 自私矿工成功出块：追加至私有链，不立即广播
        block = Block(-1, "selfish")
        block.mine(2)
        node.blockchain.append(block)
        node.private_chain_length += 1
        delta = len(self.selfish_node.blockchain) - len(self.selfish_node.public_chain)
        # 当已领先2个区块时发布全部私链
        if delta == 0 and node.private_chain_length == 2:
            node.private_chain_length = 0
            node.public_chain = copy.deepcopy(node.blockchain)

    def honest_miner(self, node):
        # 诚实矿工出块：追加到主链
        block = Block(1, "honest")
        block.mine(2)
        node.blockchain.append(block)
        delta = len(self.selfish_node.blockchain) - len(self.selfish_node.public_chain)
        if delta == 0:
            # 自私矿工无领先：放弃攻击，复制诚实链
            self.selfish_node.blockchain = copy.deepcopy(node.blockchain)
            self.selfish_node.private_chain_length = 0
        elif delta == 1:
            # 自私矿工领先1：广播私链，与诚实链竞争
            self.selfish_node.public_chain = copy.deepcopy(self.selfish_node.blockchain)
            self.selfish_node.private_chain_length = 0
            if random.random() < 0.5:
                # 50% 诚实节点认同自私链
                self.selfish_node.public_chain = node.blockchain
                self.selfish_node.blockchain = node.blockchain
            else:
                node.blockchain = self.selfish_node.public_chain
        elif delta == 2:
            # 自私矿工领先2：全部广播
            self.selfish_node.public_chain = copy.deepcopy(self.selfish_node.blockchain)
            self.selfish_node.private_chain_length = 0
        else:
            # 自私矿工领先更多：发布一个区块
            self.selfish_node.public_chain = copy.deepcopy(self.selfish_node.blockchain[:len(self.selfish_node.public_chain) + 1])
            self.selfish_node.private_chain_length -= 2

    def block_count(self, id):
        # 统计最终主链中来自不同节点的出块数
        count = 0
        for block in self.honest_nodes.blockchain:
            if block.node_id == id:
                count += 1
        return count

if __name__ == "__main__":
    malicious_rates = [0.1, 0.2, 0.3, 0.4]  # 自私矿工占比列表
    rounds = 1000  # 每轮模拟次数
    seed = 42  # 随机种子

    for malicious_rate in malicious_rates:
        simulation = BlockchainSimulation(malicious_rate, rounds, seed)
        simulation.simulate()
