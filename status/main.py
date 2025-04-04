"""
---------------------------------------------------------------
File name:                  main.py
Author:                     Ignorant-lu
Date created:               2025/04/03
Description:                应用程序入口点
----------------------------------------------------------------

Changed history:            
                            2025/04/03: 初始创建;
----
"""

import sys
import logging

def setup_logging():
    """设置日志系统"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler("status.log"),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger("Hollow-ming")

def main():
    """应用主函数"""
    logger = setup_logging()
    logger.info("Hollow-ming 应用启动")
    
    try:
        # 未来将从这里导入和初始化核心应用
        # from status.core.app import Application
        # app = Application()
        # app.run()
        
        # 临时打印，表示应用已启动
        print("Hollow-ming - 空洞骑士主题系统监控桌宠")
        print("应用正在开发中...")
        print("请查看项目文档了解更多信息")
        
    except Exception as e:
        logger.error(f"应用启动失败: {str(e)}", exc_info=True)
        return 1
    
    logger.info("Hollow-ming 应用正常退出")
    return 0

if __name__ == "__main__":
    sys.exit(main()) 