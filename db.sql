--
-- PostgreSQL database dump
--

-- Dumped from database version 12.13 (Ubuntu 12.13-1.pgdg20.04+1)
-- Dumped by pg_dump version 12.12 (Ubuntu 12.12-0ubuntu0.20.04.1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: Clients; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public."Clients" (
    "ID" integer DEFAULT 0 NOT NULL,
    "Name" text NOT NULL,
    "Password" text DEFAULT 0 NOT NULL,
    "Public Key" text NOT NULL,
    "Status" boolean NOT NULL,
    "Pending Messages" text[]
);


ALTER TABLE public."Clients" OWNER TO postgres;

--
-- Name: Groups; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public."Groups" (
    "ID" integer NOT NULL,
    "Name" text NOT NULL,
    "Admin ID" integer NOT NULL,
    "Participants" integer[] NOT NULL
);


ALTER TABLE public."Groups" OWNER TO postgres;

--
-- Name: Server Info; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public."Server Info" (
    "ID" integer NOT NULL,
    "IP" text NOT NULL,
    "Port" integer NOT NULL,
    "Load" numeric DEFAULT 1 NOT NULL,
    "Status" boolean DEFAULT false NOT NULL
);


ALTER TABLE public."Server Info" OWNER TO postgres;

--
-- Name: Clients Clients_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."Clients"
    ADD CONSTRAINT "Clients_pkey" PRIMARY KEY ("ID");


--
-- Name: Groups Groups_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."Groups"
    ADD CONSTRAINT "Groups_pkey" PRIMARY KEY ("ID");


--
-- Name: Server Info Server Info_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."Server Info"
    ADD CONSTRAINT "Server Info_pkey" PRIMARY KEY ("ID");


--
-- PostgreSQL database dump complete
--


