import time
from configparser import ConfigParser
from telethon.sync import TelegramClient
from telethon.errors import SessionPasswordNeededError, FloodWaitError
from loguru import logger

class ClientPool:
    def __init__(self, config: ConfigParser, pool_size: int = 5, sleep_time: int = 60):
        """
        初始化连接池
        
        Args:
            config (ConfigParser): 配置文件对象
            pool_size (int): 连接池大小，默认为 5
            sleep_time (int): 连接不可用时的休眠时间（秒），默认为 60 秒
        """
        self.config = config
        self.pool_size = pool_size
        self.sleep_time = sleep_time
        self.clients = []
        self._initialize_clients()

    def _initialize_clients(self):
        """
        初始化连接池中的客户端实例
        """
        for i in range(self.pool_size):
            client = {
                "instance": self._create_client(i),
                "is_available": True,
                "available_at": None  # 记录连接恢复时间
            }
            self.clients.append(client)

    def _create_client(self, index: int):
        """
        创建单个 TelegramClient 实例
        
        Args:
            index (int): 客户端索引，用于区分不同的会话
        
        Returns:
            TelegramClient: 创建的客户端实例
        """
        username = self.config.get('TG', 'username')
        phone = self.config.get('TG', 'phone')
        api_id = int(self.config.get('TG', 'api_id'))
        api_hash = self.config.get('TG', 'api_hash')

        # 使用不同的会话名称以支持多实例
        session_name = f"{username}_session_{index}"

        # 创建连接
        client = TelegramClient(session_name, api_id, api_hash)
        client.start()
        logger.info(f"TelegramClient created for {session_name}")

        # 确认授权
        if not client.is_user_authorized():
            client.send_code_request(phone)
            try:
                client.sign_in(phone, input(f'Enter the code for session {index}: '))
            except SessionPasswordNeededError:
                client.sign_in(password=input(f'Enter password for session {index}: '))
        return client

    def get_client(self):
        """
        获取一个可用的客户端实例
        
        Returns:
            TelegramClient: 可用的客户端实例
        """
        while True:
            now = time.time()
            for client in self.clients:
                if client["is_available"] and (client["available_at"] is None or client["available_at"] <= now):
                    client["is_available"] = False  # 标记为不可用
                    logger.info(f"Client {client['instance'].session.filename} acquired.")
                    return client["instance"]

            # 如果没有可用连接，等待一段时间后重试
            logger.warning("No available clients. Waiting for a client to become available...")
            time.sleep(5)

    def release_client(self, client_instance, error=None):
        """
        释放客户端实例，并根据错误情况决定是否休眠
        
        Args:
            client_instance (TelegramClient): 要释放的客户端实例
            error (Exception): 使用过程中发生的错误，如果存在则触发休眠
        """
        for client in self.clients:
            if client["instance"] == client_instance:
                if error:
                    # 如果发生错误，设置休眠时间
                    client["available_at"] = time.time() + self.sleep_time
                    logger.warning(f"Client {client_instance.session.filename} marked as unavailable for {self.sleep_time} seconds due to error.")
                else:
                    # 如果没有错误，直接标记为可用
                    client["is_available"] = True
                    client["available_at"] = None
                    logger.info(f"Client {client_instance.session.filename} released and marked as available.")
                break

    def close_all_clients(self):
        """
        关闭连接池中的所有客户端实例
        """
        for client in self.clients:
            client["instance"].disconnect()
            logger.info(f"TelegramClient disconnected for {client['instance'].session.filename}")
        self.clients = []  # 清空连接池