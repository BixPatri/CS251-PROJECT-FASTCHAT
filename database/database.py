from connect import connect
(db_conn, db_cur) = connect()

def client_table():
    db_cur.execute(
        """CREATE TABLE IF NOT EXISTS "Clients"
        (
            "ID" integer NOT NULL DEFAULT 0,
            "Name" text NOT NULL,
            "Password" text NOT NULL DEFAULT 0,
            "Public Key" text NOT NULL,
            "Status" boolean NOT NULL,
            "Pending Messages" text[],
            CONSTRAINT "Clients_pkey" PRIMARY KEY ("ID")
        )"""
        )

def group_table():
    db_cur.execute(
        """CREATE TABLE IF NOT EXISTS "Groups"
        (
            "ID" integer NOT NULL,
            "Name" text NOT NULL,
            "Admin ID" integer NOT NULL,
            "Participants" integer[] NOT NULL,
            CONSTRAINT "Groups_pkey" PRIMARY KEY ("ID")
        )"""
        )

def server_table():
    db_cur.execute(
        """CREATE TABLE IF NOT EXISTS "Server Info"
        (
            "ID" integer NOT NULL,
            "IP" text NOT NULL,
            "Port" integer NOT NULL,
            "Load" integer NOT NULL Default 0,
            "Status" boolean NOT NULL Default false,
            CONSTRAINT "Server Info_pkey" PRIMARY KEY ("ID")
        )"""
        )

def server_add():
    a = open(r'servers.txt','r').read().splitlines()
    for server in a:
        serv = eval(server)
        db_cur.execute(f"""
        INSERT INTO "Server Info" ("ID","IP","Port","Load","Status") VALUES (%s,%s,%s,0,false);
        """, (serv[0],serv[1],serv[2])
        )
    
if __name__ == '__main__':
    db_cur.execute(f"""
        DROP TABLE IF EXISTS "Server Info";
        """
        )
    db_cur.execute(f"""
        DROP TABLE IF EXISTS "Clients";
        """
        )
    db_cur.execute(f"""
        DROP TABLE IF EXISTS "Groups";
        """
        )
    server_table()
    client_table()
    group_table()
    server_add()
    db_conn.commit()
    db_conn.close()
    
