import logging

def setup_logging(level=logging.INFO):
    """
    配置全局日志记录器。

    Args:
        level: 日志记录级别 (例如 logging.INFO, logging.DEBUG)。
    """
    # 获取根记录器
    root_logger = logging.getLogger()
    
    # 如果根记录器已有处理器，则先移除，避免重复添加，确保basicConfig是干净的开始
    # 这在脚本或应用中多次调用setup_logging或与其他日志配置冲突时尤其重要
    if root_logger.hasHandlers():
        for handler in root_logger.handlers[:]: # 使用切片复制列表进行迭代，因为我们正在修改列表
            root_logger.removeHandler(handler)
            
    # 配置basicConfig
    # 这将为根记录器添加一个默认的StreamHandler（到控制台）
    # 如果没有其他配置，这将是唯一的处理器
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    logging.info("日志记录已通过 setup_logging 初始化。")
