import pymysql
from dotenv import load_dotenv
import os
from werkzeug.security import generate_password_hash, check_password_hash

load_dotenv()


def check_users():
    """检查数据库中的用户数据"""
    try:
        conn = pymysql.connect(
            host=os.getenv('MYSQL_HOST'),
            port=int(os.getenv('MYSQL_PORT')),
            user=os.getenv('MYSQL_USER'),
            password=os.getenv('MYSQL_PASSWORD'),
            database=os.getenv('MYSQL_DB'),
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )

        print("=" * 60)
        print("检查用户数据")
        print("=" * 60)

        with conn.cursor() as cursor:
            # 查询admin用户
            cursor.execute("SELECT * FROM user WHERE username = 'admin'")
            admin = cursor.fetchone()

            if admin:
                print(f"✓ 找到admin用户")
                print(f"  user_id: {admin['user_id']}")
                print(f"  username: {admin['username']}")
                print(f"  role: {admin['role']}")
                print(f"  status: {admin['status']}")
                print(f"  password_hash: {admin['password_hash'][:50]}...")
                print()

                # 测试密码验证
                test_password = '123456'
                is_valid = check_password_hash(admin['password_hash'], test_password)
                print(f"密码 '{test_password}' 验证结果: {is_valid}")
                print()

                if not is_valid:
                    print("⚠ 密码验证失败！需要更新密码hash")
                    print("正在生成新的密码hash...")
                    new_hash = generate_password_hash('123456')
                    print(f"新的hash: {new_hash}")
                    print()

                    # 询问是否更新
                    response = input("是否更新admin密码为 '123456'? (y/n): ")
                    if response.lower() == 'y':
                        cursor.execute(
                            "UPDATE user SET password_hash = %s WHERE username = 'admin'",
                            (new_hash,)
                        )
                        conn.commit()
                        print("✓ 密码已更新！")

                        # 再次验证
                        is_valid = check_password_hash(new_hash, test_password)
                        print(f"验证新密码: {is_valid}")
                else:
                    print("✓ 密码验证成功！")
            else:
                print("✗ 未找到admin用户")
                print("正在创建admin用户...")

                password_hash = generate_password_hash('123456')
                cursor.execute("""
                    INSERT INTO user (username, password_hash, phone, role, status)
                    VALUES ('admin', %s, '13800138000', 'admin', 1)
                """, (password_hash,))
                conn.commit()
                print("✓ admin用户创建成功！")

            print()
            print("=" * 60)
            print("检查其他用户")
            print("=" * 60)

            # 检查user001
            cursor.execute("SELECT * FROM user WHERE username = 'user001'")
            user001 = cursor.fetchone()

            if user001:
                print(f"✓ 找到user001")
                test_valid = check_password_hash(user001['password_hash'], '123456')
                print(f"密码验证: {test_valid}")

                if not test_valid:
                    print("⚠ user001密码也需要更新")
                    response = input("是否更新所有顾客用户密码为 '123456'? (y/n): ")
                    if response.lower() == 'y':
                        new_hash = generate_password_hash('123456')
                        cursor.execute(
                            "UPDATE user SET password_hash = %s WHERE role = 'customer'",
                            (new_hash,)
                        )
                        conn.commit()
                        affected = cursor.rowcount
                        print(f"✓ 已更新 {affected} 个用户的密码")

            # 统计
            cursor.execute("SELECT COUNT(*) as count FROM user")
            total = cursor.fetchone()['count']
            print(f"\n数据库中共有 {total} 个用户")

        conn.close()

    except Exception as e:
        print(f"✗ 错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    check_users()
