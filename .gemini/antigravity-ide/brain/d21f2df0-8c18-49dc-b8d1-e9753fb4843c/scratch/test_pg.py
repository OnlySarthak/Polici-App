import asyncpg
import asyncio

async def test_conn(user, password, db):
    try:
        conn = await asyncpg.connect(user=user, password=password, database=db, host='localhost')
        print(f"Success! user={user}, password={password}, db={db}")
        await conn.close()
        return True
    except Exception as e:
        return False

async def main():
    users = ['postgres', 'user', 'Sarthaka']
    passwords = ['postgres', 'password', '', '1234', 'admin', 'root', '123456', '12345678', 'sarthak', 'sarthak123', 'insurance', 'insurance_db', 'onlysarthak', 'Sarthak@123', 'Sarthaka@123']
    dbs = ['insurance_db', 'postgres']
    for user in users:
        for password in passwords:
            for db in dbs:
                if await test_conn(user, password, db):
                    print(f"FOUND WORKING CREDENTIALS: {user} / {password} on {db}")
                    return

if __name__ == '__main__':
    asyncio.run(main())
