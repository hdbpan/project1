import os
import subprocess
from datetime import datetime, timedelta
import gzip
import shutil
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


class BackupManager:
    """数据库备份管理器"""

    def __init__(self):
        self.db_name = os.getenv('MYSQL_DB')
        self.db_user = os.getenv('MYSQL_USER')
        self.db_password = os.getenv('MYSQL_PASSWORD')
        self.db_host = os.getenv('MYSQL_HOST')
        self.backup_dir = Path('backups')
        self.retention_days = 30

        # 创建备份目录
        self.backup_dir.mkdir(exist_ok=True)

    def create_backup(self):
        """创建数据库备份"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = self.backup_dir / f'{self.db_name}_{timestamp}.sql'

        print("=" * 70)
        print(f"开始备份: {datetime.now()}")
        print("=" * 70)

        cmd = [
            'mysqldump',
            f'--user={self.db_user}',
            f'--host={self.db_host}',
            '--single-transaction',
            '--routines',
            '--triggers',
            '--events',
            '--databases', self.db_name,
            f'--result-file={backup_file}'
        ]

        try:
            # 通过环境变量传递密码（更安全）
            env = os.environ.copy()
            env['MYSQL_PWD'] = self.db_password

            subprocess.run(cmd, check=True, capture_output=True, env=env)
            print(f"✓ 备份成功: {backup_file}")

            # 压缩备份文件
            with open(backup_file, 'rb') as f_in:
                with gzip.open(f'{backup_file}.gz', 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            backup_file.unlink()  # 删除未压缩文件
            print(f"✓ 压缩完成: {backup_file}.gz")

        except subprocess.CalledProcessError as e:
            print(f"✗ 备份失败: {e.stderr.decode()}")
            raise
