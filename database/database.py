from connect import connect
(db_conn, db_cur) = connect()


# def create_server():
#     db_cur.execute(f"""
#     CREATE ROLE "Server" WITH
# 	LOGIN
# 	NOSUPERUSER
# 	NOCREATEDB
# 	NOCREATEROLE
# 	INHERIT
# 	NOREPLICATION
# 	CONNECTION LIMIT -1
# 	PASSWORD 'server_pass';
#     """)

# def create_client():
#     db_cur.execute(f"""
#     CREATE ROLE "Client" WITH
# 	LOGIN
# 	NOSUPERUSER
# 	NOCREATEDB
# 	NOCREATEROLE
# 	INHERIT
# 	NOREPLICATION
# 	CONNECTION LIMIT -1
# 	PASSWORD 'client_pass';
#     """)

# def create_balancer():
#     db_cur.execute(f"""
#     CREATE ROLE "Balancer" WITH
# 	LOGIN
# 	NOSUPERUSER
# 	NOCREATEDB
# 	NOCREATEROLE
# 	INHERIT
# 	NOREPLICATION
# 	CONNECTION LIMIT -1
# 	PASSWORD 'balancer_pass';
#     """)

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
            "Load" numeric NOT NULL Default 1,
            "Status" boolean NOT NULL Default false,
            CONSTRAINT "Server Info_pkey" PRIMARY KEY ("ID")
        )"""
        )

def server_add():
    a = open(r'servers.txt','r').read().splitlines()
    for server in a:
        serv = eval(server)
        db_cur.execute(f"""
        INSERT INTO "Server Info" ("ID","IP","Port","Load","Status") VALUES (%s,%s,%s,%s,false);
        """, (serv[0],serv[1],serv[2],serv[3])
        )

# def grant_access():
#     db_cur.execute(
#     f"""
#     GRANT ALL ON TABLE public."Clients" TO "Server";
#     """)
#     db_cur.execute(
#     f"""
#     GRANT SELECT("ID") ON public."Clients" TO "Client";
#     """)
#     db_cur.execute(
#     f"""
#     GRANT SELECT("Public Key") ON public."Clients" TO "Client";
#     """)
#     db_cur.execute(
#     f"""
#     GRANT ALL ON TABLE public."Server Info" TO "Balancer";
#     """)
#     db_cur.execute(
#     f"""
#     GRANT ALL ON TABLE public."Server Info" TO "Server";
#     """)
#     db_cur.execute(
#     f"""
#     GRANT ALL ON TABLE public."Groups" TO "Server";
#     """)
#     db_cur.execute(
#     f"""
#     GRANT SELECT ON TABLE public."Server Info" TO "Client";
#     """)
#     db_cur.execute(
#     f"""
#     GRANT SELECT("Name") ON public."Clients" TO "Client";
#     """)
    
if __name__ == '__main__':
    db_cur.execute("""
    DROP TABLE IF EXISTS "Server Info"
    """)
    db_cur.execute("""
    DROP TABLE IF EXISTS "Clients"
    """)
    db_cur.execute("""
    DROP TABLE IF EXISTS "Groups"
    """)
    server_table()
    client_table()
    group_table()
    # create_server()
    # create_balancer()
    # create_client()
    server_add()
    # grant_access()
    db_conn.commit()
    db_conn.close()
    
