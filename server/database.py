CREATE TABLE IF NOT EXISTS public."Clients"
(
    "ID" numeric NOT NULL DEFAULT 0,
    "Name" text COLLATE pg_catalog."default" NOT NULL,
    "Password" text COLLATE pg_catalog."default" NOT NULL DEFAULT 0,
    "Public Key" text COLLATE pg_catalog."default" NOT NULL DEFAULT 0,
    "Status" boolean NOT NULL,
    "Pending Messages" text[] COLLATE pg_catalog."default" NOT NULL,
    CONSTRAINT "Clients_pkey" PRIMARY KEY ("ID")
)

CREATE TABLE IF NOT EXISTS public."Groups"
(
    "ID" numeric NOT NULL,
    "Name" text COLLATE pg_catalog."default" NOT NULL,
    "Admin ID" numeric NOT NULL,
    "Participants" numeric[] NOT NULL,
    CONSTRAINT "Groups_pkey" PRIMARY KEY ("ID")
)


CREATE TABLE IF NOT EXISTS public."Server Info"
(
    "ID" numeric NOT NULL,
    "IP" text COLLATE pg_catalog."default" NOT NULL,
    "Port" numeric NOT NULL,
    "Load" numeric NOT NULL,
    "Status" boolean NOT NULL,
    CONSTRAINT "Server Info_pkey" PRIMARY KEY ("ID")
)