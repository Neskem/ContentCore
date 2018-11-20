--
-- PostgreSQL database dump
--

-- Dumped from database version 9.5.13
-- Dumped by pg_dump version 9.5.13

SET statement_timeout = 0;
SET lock_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: plpgsql; Type: EXTENSION; Schema: -; Owner: 
--

CREATE EXTENSION IF NOT EXISTS plpgsql WITH SCHEMA pg_catalog;


--
-- Name: EXTENSION plpgsql; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION plpgsql IS 'PL/pgSQL procedural language';


--
-- Name: dpi_pattern_type; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.dpi_pattern_type AS ENUM (
    'cve',
    'keyword'
);


ALTER TYPE public.dpi_pattern_type OWNER TO postgres;

--
-- Name: lib_type; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.lib_type AS ENUM (
    'suspect',
    'unknown'
);


ALTER TYPE public.lib_type OWNER TO postgres;

--
-- Name: rq_status; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.rq_status AS ENUM (
    'pending',
    'requested',
    'done',
    'failed'
);


ALTER TYPE public.rq_status OWNER TO postgres;

--
-- Name: source_type; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.source_type AS ENUM (
    'regular',
    'event'
);


ALTER TYPE public.source_type OWNER TO postgres;

SET default_tablespace = '';

SET default_with_oids = false;

--
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);


ALTER TABLE public.alembic_version OWNER TO postgres;

--
-- Name: device_detailed_info; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.device_detailed_info (
    id integer NOT NULL,
    device_id integer NOT NULL,
    detail jsonb
);


ALTER TABLE public.device_detailed_info OWNER TO postgres;

--
-- Name: device_detailed_info_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.device_detailed_info_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.device_detailed_info_id_seq OWNER TO postgres;

--
-- Name: device_detailed_info_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.device_detailed_info_id_seq OWNED BY public.device_detailed_info.id;


--
-- Name: device_pattern_status; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.device_pattern_status (
    id integer NOT NULL,
    device_id uuid NOT NULL,
    pattern_status character varying(64) NOT NULL,
    pattern_id integer,
    new_pattern_id integer,
    selected_pattern_id integer,
    notified_pattern_id integer,
    deployed_pattern_id integer,
    deployed_error_code integer,
    deployed_error_message character varying(255)
);


ALTER TABLE public.device_pattern_status OWNER TO postgres;

--
-- Name: device_pattern_status_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.device_pattern_status_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.device_pattern_status_id_seq OWNER TO postgres;

--
-- Name: device_pattern_status_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.device_pattern_status_id_seq OWNED BY public.device_pattern_status.id;


--
-- Name: devices; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.devices (
    id integer NOT NULL,
    device_name character varying(255) NOT NULL,
    status smallint,
    _ctime timestamp without time zone,
    _mtime timestamp without time zone,
    locked boolean,
    device_guid character(32),
    hash_id integer,
    collect_detail boolean,
    platfrom_id integer
);


ALTER TABLE public.devices OWNER TO postgres;

--
-- Name: devices_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.devices_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.devices_id_seq OWNER TO postgres;

--
-- Name: devices_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.devices_id_seq OWNED BY public.devices.id;


--
-- Name: dpi_pattern; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.dpi_pattern (
    pattern_id integer NOT NULL,
    pattern_hash character(64),
    library_hash character(64),
    fix_cve_ids text,
    memory_kb integer,
    platform character varying(64),
    _ctime timestamp without time zone,
    _mtime timestamp without time zone
);


ALTER TABLE public.dpi_pattern OWNER TO postgres;

--
-- Name: dpi_pattern_pattern_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.dpi_pattern_pattern_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.dpi_pattern_pattern_id_seq OWNER TO postgres;

--
-- Name: dpi_pattern_pattern_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.dpi_pattern_pattern_id_seq OWNED BY public.dpi_pattern.pattern_id;


--
-- Name: dpi_requests; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.dpi_requests (
    pattern_id integer NOT NULL,
    source public.source_type,
    request_number character varying(32),
    request_status public.rq_status,
    download_link character varying(512),
    checksum character(32),
    session_token character(16),
    _ctime timestamp without time zone DEFAULT now() NOT NULL,
    _dtime timestamp without time zone
);


ALTER TABLE public.dpi_requests OWNER TO postgres;

--
-- Name: dpi_requests_pattern_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.dpi_requests_pattern_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.dpi_requests_pattern_id_seq OWNER TO postgres;

--
-- Name: dpi_requests_pattern_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.dpi_requests_pattern_id_seq OWNED BY public.dpi_requests.pattern_id;


--
-- Name: dpi_update_status; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.dpi_update_status (
    pattern character varying(64),
    type public.dpi_pattern_type,
    _mtime timestamp without time zone DEFAULT '1970-01-01 00:00:00'::timestamp without time zone NOT NULL
);


ALTER TABLE public.dpi_update_status OWNER TO postgres;

--
-- Name: hash_libraries; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.hash_libraries (
    id integer NOT NULL,
    hash_id integer NOT NULL,
    vendor character varying(255) NOT NULL,
    app character varying(255) NOT NULL,
    version character varying(255) NOT NULL,
    _ctime timestamp without time zone,
    _mtime timestamp without time zone,
    latest_cve json
);


ALTER TABLE public.hash_libraries OWNER TO postgres;

--
-- Name: hash_libraries_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.hash_libraries_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.hash_libraries_id_seq OWNER TO postgres;

--
-- Name: hash_libraries_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.hash_libraries_id_seq OWNED BY public.hash_libraries.id;


--
-- Name: hash_library_file_mapping; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.hash_library_file_mapping (
    hash_libraries_id integer,
    hash_library_files_id integer
);


ALTER TABLE public.hash_library_file_mapping OWNER TO postgres;

--
-- Name: hash_library_files; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.hash_library_files (
    id integer NOT NULL,
    libname character varying(4096) NOT NULL,
    path character varying(4096) NOT NULL,
    hash_id integer NOT NULL,
    _ctime timestamp without time zone,
    _mtime timestamp without time zone
);


ALTER TABLE public.hash_library_files OWNER TO postgres;

--
-- Name: hash_library_files_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.hash_library_files_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.hash_library_files_id_seq OWNER TO postgres;

--
-- Name: hash_library_files_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.hash_library_files_id_seq OWNED BY public.hash_library_files.id;


--
-- Name: job_history; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.job_history (
    id integer NOT NULL,
    hash_id integer,
    has_vulnerability boolean,
    end_time timestamp without time zone,
    _ctime timestamp without time zone,
    _mtime timestamp without time zone,
    type integer
);


ALTER TABLE public.job_history OWNER TO postgres;

--
-- Name: job_history_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.job_history_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.job_history_id_seq OWNER TO postgres;

--
-- Name: job_history_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.job_history_id_seq OWNED BY public.job_history.id;


--
-- Name: known_libraries; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.known_libraries (
    id integer NOT NULL,
    vendor character varying(255) NOT NULL,
    app character varying(255) NOT NULL,
    _ctime timestamp without time zone,
    _mtime timestamp without time zone
);


ALTER TABLE public.known_libraries OWNER TO postgres;

--
-- Name: known_libraries_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.known_libraries_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.known_libraries_id_seq OWNER TO postgres;

--
-- Name: known_libraries_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.known_libraries_id_seq OWNED BY public.known_libraries.id;


--
-- Name: known_library_file_mapping; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.known_library_file_mapping (
    known_libraries_id integer,
    known_library_files_id integer
);


ALTER TABLE public.known_library_file_mapping OWNER TO postgres;

--
-- Name: known_library_files; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.known_library_files (
    id integer NOT NULL,
    libname character varying(255) NOT NULL,
    _ctime timestamp without time zone,
    _mtime timestamp without time zone
);


ALTER TABLE public.known_library_files OWNER TO postgres;

--
-- Name: known_library_files_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.known_library_files_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.known_library_files_id_seq OWNER TO postgres;

--
-- Name: known_library_files_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.known_library_files_id_seq OWNED BY public.known_library_files.id;


--
-- Name: known_library_patterns; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.known_library_patterns (
    id integer NOT NULL,
    lib_type smallint NOT NULL,
    target character varying(255) NOT NULL,
    context json NOT NULL,
    static_type smallint
);


ALTER TABLE public.known_library_patterns OWNER TO postgres;

--
-- Name: known_library_patterns_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.known_library_patterns_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.known_library_patterns_id_seq OWNER TO postgres;

--
-- Name: known_library_patterns_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.known_library_patterns_id_seq OWNED BY public.known_library_patterns.id;


--
-- Name: known_library_version; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.known_library_version (
    version_hash character(64)
);


ALTER TABLE public.known_library_version OWNER TO postgres;

--
-- Name: library_hash; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.library_hash (
    hash_id integer NOT NULL,
    hash character(64)
);


ALTER TABLE public.library_hash OWNER TO postgres;

--
-- Name: library_hash_hash_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.library_hash_hash_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.library_hash_hash_id_seq OWNER TO postgres;

--
-- Name: library_hash_hash_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.library_hash_hash_id_seq OWNED BY public.library_hash.hash_id;


--
-- Name: pattern_history; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.pattern_history (
    id integer NOT NULL,
    device_id uuid NOT NULL,
    pattern_hash character(64),
    _ctime timestamp without time zone
);


ALTER TABLE public.pattern_history OWNER TO postgres;

--
-- Name: pattern_history_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.pattern_history_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.pattern_history_id_seq OWNER TO postgres;

--
-- Name: pattern_history_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.pattern_history_id_seq OWNED BY public.pattern_history.id;


--
-- Name: platforms; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.platforms (
    platform_id integer NOT NULL,
    platform_name character varying(64),
    memory_kb integer
);


ALTER TABLE public.platforms OWNER TO postgres;

--
-- Name: platforms_platform_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.platforms_platform_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.platforms_platform_id_seq OWNER TO postgres;

--
-- Name: platforms_platform_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.platforms_platform_id_seq OWNED BY public.platforms.platform_id;


--
-- Name: schedules; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.schedules (
    id integer NOT NULL,
    enabled boolean,
    hash_id integer NOT NULL,
    minute character varying(10),
    hour character varying(10),
    day_of_month character varying(10),
    month_of_year character varying(10),
    day_of_week character varying(10),
    _ctime timestamp without time zone,
    _mtime timestamp without time zone
);


ALTER TABLE public.schedules OWNER TO postgres;

--
-- Name: schedules_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.schedules_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.schedules_id_seq OWNER TO postgres;

--
-- Name: schedules_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.schedules_id_seq OWNED BY public.schedules.id;


--
-- Name: unknown_hash_libraries; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.unknown_hash_libraries (
    id integer NOT NULL,
    libname character varying(4096) NOT NULL,
    path character varying(4096) NOT NULL,
    raw_version character varying(255),
    hash_id integer,
    type public.lib_type NOT NULL,
    _ctime timestamp without time zone,
    _mtime timestamp without time zone
);


ALTER TABLE public.unknown_hash_libraries OWNER TO postgres;

--
-- Name: unknown_hash_libraries_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.unknown_hash_libraries_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.unknown_hash_libraries_id_seq OWNER TO postgres;

--
-- Name: unknown_hash_libraries_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.unknown_hash_libraries_id_seq OWNED BY public.unknown_hash_libraries.id;


--
-- Name: upload_patterns; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.upload_patterns (
    id integer NOT NULL,
    device_id uuid NOT NULL,
    pattern_hash character(64),
    _ctime timestamp without time zone,
    _mtime timestamp without time zone
);


ALTER TABLE public.upload_patterns OWNER TO postgres;

--
-- Name: upload_patterns_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.upload_patterns_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.upload_patterns_id_seq OWNER TO postgres;

--
-- Name: upload_patterns_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.upload_patterns_id_seq OWNED BY public.upload_patterns.id;


--
-- Name: vender_model_device_mapping; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.vender_model_device_mapping (
    device_id integer NOT NULL,
    vender_key_id integer,
    model_name character varying(64),
    vender character varying(64)
);


ALTER TABLE public.vender_model_device_mapping OWNER TO postgres;

--
-- Name: vulnerabilities; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.vulnerabilities (
    id integer NOT NULL,
    hash_id integer NOT NULL,
    hash_library_id integer,
    hash_library_file_id integer,
    type character varying(20) NOT NULL,
    name character varying(255) NOT NULL,
    _ctime timestamp without time zone,
    _mtime timestamp without time zone
);


ALTER TABLE public.vulnerabilities OWNER TO postgres;

--
-- Name: vulnerabilities_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.vulnerabilities_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.vulnerabilities_id_seq OWNER TO postgres;

--
-- Name: vulnerabilities_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.vulnerabilities_id_seq OWNED BY public.vulnerabilities.id;


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.device_detailed_info ALTER COLUMN id SET DEFAULT nextval('public.device_detailed_info_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.device_pattern_status ALTER COLUMN id SET DEFAULT nextval('public.device_pattern_status_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.devices ALTER COLUMN id SET DEFAULT nextval('public.devices_id_seq'::regclass);


--
-- Name: pattern_id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.dpi_pattern ALTER COLUMN pattern_id SET DEFAULT nextval('public.dpi_pattern_pattern_id_seq'::regclass);


--
-- Name: pattern_id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.dpi_requests ALTER COLUMN pattern_id SET DEFAULT nextval('public.dpi_requests_pattern_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.hash_libraries ALTER COLUMN id SET DEFAULT nextval('public.hash_libraries_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.hash_library_files ALTER COLUMN id SET DEFAULT nextval('public.hash_library_files_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.job_history ALTER COLUMN id SET DEFAULT nextval('public.job_history_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.known_libraries ALTER COLUMN id SET DEFAULT nextval('public.known_libraries_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.known_library_files ALTER COLUMN id SET DEFAULT nextval('public.known_library_files_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.known_library_patterns ALTER COLUMN id SET DEFAULT nextval('public.known_library_patterns_id_seq'::regclass);


--
-- Name: hash_id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.library_hash ALTER COLUMN hash_id SET DEFAULT nextval('public.library_hash_hash_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.pattern_history ALTER COLUMN id SET DEFAULT nextval('public.pattern_history_id_seq'::regclass);


--
-- Name: platform_id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.platforms ALTER COLUMN platform_id SET DEFAULT nextval('public.platforms_platform_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.schedules ALTER COLUMN id SET DEFAULT nextval('public.schedules_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.unknown_hash_libraries ALTER COLUMN id SET DEFAULT nextval('public.unknown_hash_libraries_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.upload_patterns ALTER COLUMN id SET DEFAULT nextval('public.upload_patterns_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.vulnerabilities ALTER COLUMN id SET DEFAULT nextval('public.vulnerabilities_id_seq'::regclass);


--
-- Name: device_detailed_info_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.device_detailed_info
    ADD CONSTRAINT device_detailed_info_pkey PRIMARY KEY (id);


--
-- Name: device_libraries_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.hash_libraries
    ADD CONSTRAINT device_libraries_pkey PRIMARY KEY (id);


--
-- Name: device_library_files_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.hash_library_files
    ADD CONSTRAINT device_library_files_pkey PRIMARY KEY (id);


--
-- Name: device_pattern_status_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.device_pattern_status
    ADD CONSTRAINT device_pattern_status_pkey PRIMARY KEY (id);


--
-- Name: devices_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.devices
    ADD CONSTRAINT devices_pkey PRIMARY KEY (id);


--
-- Name: dpi_pattern_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.dpi_pattern
    ADD CONSTRAINT dpi_pattern_pkey PRIMARY KEY (pattern_id);


--
-- Name: job_history_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.job_history
    ADD CONSTRAINT job_history_pkey PRIMARY KEY (id);


--
-- Name: known_libraries_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.known_libraries
    ADD CONSTRAINT known_libraries_pkey PRIMARY KEY (id);


--
-- Name: known_library_files_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.known_library_files
    ADD CONSTRAINT known_library_files_pkey PRIMARY KEY (id);


--
-- Name: known_library_patterns_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.known_library_patterns
    ADD CONSTRAINT known_library_patterns_pkey PRIMARY KEY (id);


--
-- Name: library_hash_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.library_hash
    ADD CONSTRAINT library_hash_pkey PRIMARY KEY (hash_id);


--
-- Name: pattern_history_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.pattern_history
    ADD CONSTRAINT pattern_history_pkey PRIMARY KEY (id);


--
-- Name: platforms_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.platforms
    ADD CONSTRAINT platforms_pkey PRIMARY KEY (platform_id);


--
-- Name: schedules_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.schedules
    ADD CONSTRAINT schedules_pkey PRIMARY KEY (id);


--
-- Name: unknown_device_libraries_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.unknown_hash_libraries
    ADD CONSTRAINT unknown_device_libraries_pkey PRIMARY KEY (id);


--
-- Name: upload_patterns_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.upload_patterns
    ADD CONSTRAINT upload_patterns_pkey PRIMARY KEY (id);


--
-- Name: vender_model_device_mapping_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.vender_model_device_mapping
    ADD CONSTRAINT vender_model_device_mapping_pkey PRIMARY KEY (device_id);


--
-- Name: vendor_app_unique_constraint; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.known_libraries
    ADD CONSTRAINT vendor_app_unique_constraint UNIQUE (vendor, app);


--
-- Name: vulnerabilities_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.vulnerabilities
    ADD CONSTRAINT vulnerabilities_pkey PRIMARY KEY (id);


--
-- Name: idx_device_detailed_info_device_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_device_detailed_info_device_id ON public.device_detailed_info USING btree (device_id);


--
-- Name: idx_device_libraries_device_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_device_libraries_device_id ON public.hash_libraries USING btree (hash_id);


--
-- Name: idx_device_library_file_mapping_device_libraries_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_device_library_file_mapping_device_libraries_id ON public.hash_library_file_mapping USING btree (hash_libraries_id);


--
-- Name: idx_device_library_file_mapping_device_library_files_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_device_library_file_mapping_device_library_files_id ON public.hash_library_file_mapping USING btree (hash_library_files_id);


--
-- Name: idx_device_library_files_device_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_device_library_files_device_id ON public.hash_library_files USING btree (hash_id);


--
-- Name: idx_device_pattern_status_device_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX idx_device_pattern_status_device_id ON public.device_pattern_status USING btree (device_id);


--
-- Name: idx_devices_device_name; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX idx_devices_device_name ON public.devices USING btree (device_name);


--
-- Name: idx_dpi_requests_pattern_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX idx_dpi_requests_pattern_id ON public.dpi_requests USING btree (pattern_id);


--
-- Name: idx_job_history_has_vulnerability; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_job_history_has_vulnerability ON public.job_history USING btree (has_vulnerability);


--
-- Name: idx_known_library_file_mapping_known_libraries_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_known_library_file_mapping_known_libraries_id ON public.known_library_file_mapping USING btree (known_libraries_id);


--
-- Name: idx_known_library_file_mapping_known_library_files_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_known_library_file_mapping_known_library_files_id ON public.known_library_file_mapping USING btree (known_library_files_id);


--
-- Name: idx_known_library_files_libname; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX idx_known_library_files_libname ON public.known_library_files USING btree (libname);


--
-- Name: idx_lib_device_lib; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_lib_device_lib ON public.hash_libraries USING btree (hash_id, vendor, app, version);


--
-- Name: idx_unknown_device_libraries_device_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_unknown_device_libraries_device_id ON public.unknown_hash_libraries USING btree (hash_id);


--
-- Name: idx_vulnerabilities_device_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_vulnerabilities_device_id ON public.vulnerabilities USING btree (hash_id);


--
-- Name: idx_vulnerabilities_device_library_file_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_vulnerabilities_device_library_file_id ON public.vulnerabilities USING btree (hash_library_file_id);


--
-- Name: idx_vulnerabilities_device_library_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_vulnerabilities_device_library_id ON public.vulnerabilities USING btree (hash_library_id);


--
-- Name: ix_device_detailed_info_device_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_device_detailed_info_device_id ON public.device_detailed_info USING btree (device_id);


--
-- Name: ix_device_libraries_device_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_device_libraries_device_id ON public.hash_libraries USING btree (hash_id);


--
-- Name: ix_device_library_file_mapping_device_libraries_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_device_library_file_mapping_device_libraries_id ON public.hash_library_file_mapping USING btree (hash_libraries_id);


--
-- Name: ix_device_library_file_mapping_device_library_files_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_device_library_file_mapping_device_library_files_id ON public.hash_library_file_mapping USING btree (hash_library_files_id);


--
-- Name: ix_device_library_files_device_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_device_library_files_device_id ON public.hash_library_files USING btree (hash_id);


--
-- Name: ix_device_pattern_status_device_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX ix_device_pattern_status_device_id ON public.device_pattern_status USING btree (device_id);


--
-- Name: ix_devices_device_name; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX ix_devices_device_name ON public.devices USING btree (device_name);


--
-- Name: ix_job_history_has_vulnerability; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_job_history_has_vulnerability ON public.job_history USING btree (has_vulnerability);


--
-- Name: ix_known_library_file_mapping_known_libraries_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_known_library_file_mapping_known_libraries_id ON public.known_library_file_mapping USING btree (known_libraries_id);


--
-- Name: ix_known_library_file_mapping_known_library_files_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_known_library_file_mapping_known_library_files_id ON public.known_library_file_mapping USING btree (known_library_files_id);


--
-- Name: ix_known_library_files_libname; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX ix_known_library_files_libname ON public.known_library_files USING btree (libname);


--
-- Name: ix_unknown_device_libraries_device_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_unknown_device_libraries_device_id ON public.unknown_hash_libraries USING btree (hash_id);


--
-- Name: ix_vulnerabilities_device_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_vulnerabilities_device_id ON public.vulnerabilities USING btree (hash_id);


--
-- Name: ix_vulnerabilities_device_library_file_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_vulnerabilities_device_library_file_id ON public.vulnerabilities USING btree (hash_library_file_id);


--
-- Name: ix_vulnerabilities_device_library_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_vulnerabilities_device_library_id ON public.vulnerabilities USING btree (hash_library_id);


--
-- Name: device_detailed_info_device_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.device_detailed_info
    ADD CONSTRAINT device_detailed_info_device_id_fkey FOREIGN KEY (device_id) REFERENCES public.devices(id);


--
-- Name: device_libraries_hash_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.hash_libraries
    ADD CONSTRAINT device_libraries_hash_id_fkey FOREIGN KEY (hash_id) REFERENCES public.library_hash(hash_id);


--
-- Name: device_library_file_mapping_device_libraries_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.hash_library_file_mapping
    ADD CONSTRAINT device_library_file_mapping_device_libraries_id_fkey FOREIGN KEY (hash_libraries_id) REFERENCES public.hash_libraries(id);


--
-- Name: device_library_file_mapping_device_library_files_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.hash_library_file_mapping
    ADD CONSTRAINT device_library_file_mapping_device_library_files_id_fkey FOREIGN KEY (hash_library_files_id) REFERENCES public.hash_library_files(id);


--
-- Name: device_library_files_hash_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.hash_library_files
    ADD CONSTRAINT device_library_files_hash_id_fkey FOREIGN KEY (hash_id) REFERENCES public.library_hash(hash_id);


--
-- Name: devices_hash_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.devices
    ADD CONSTRAINT devices_hash_id FOREIGN KEY (hash_id) REFERENCES public.library_hash(hash_id);


--
-- Name: devices_platform_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.devices
    ADD CONSTRAINT devices_platform_id_fkey FOREIGN KEY (platfrom_id) REFERENCES public.platforms(platform_id);


--
-- Name: dpi_patterns_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.dpi_pattern
    ADD CONSTRAINT dpi_patterns_fkey FOREIGN KEY (pattern_id) REFERENCES public.dpi_requests(pattern_id);


--
-- Name: job_history_hash_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.job_history
    ADD CONSTRAINT job_history_hash_id_fkey FOREIGN KEY (hash_id) REFERENCES public.library_hash(hash_id);


--
-- Name: known_library_file_mapping_known_libraries_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.known_library_file_mapping
    ADD CONSTRAINT known_library_file_mapping_known_libraries_id_fkey FOREIGN KEY (known_libraries_id) REFERENCES public.known_libraries(id);


--
-- Name: known_library_file_mapping_known_library_files_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.known_library_file_mapping
    ADD CONSTRAINT known_library_file_mapping_known_library_files_id_fkey FOREIGN KEY (known_library_files_id) REFERENCES public.known_library_files(id);


--
-- Name: pattern_history_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.pattern_history
    ADD CONSTRAINT pattern_history_fkey FOREIGN KEY (device_id) REFERENCES public.device_pattern_status(device_id);


--
-- Name: schedules_hash_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.schedules
    ADD CONSTRAINT schedules_hash_id_fkey FOREIGN KEY (hash_id) REFERENCES public.library_hash(hash_id);


--
-- Name: unknown_device_libraries_hash_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.unknown_hash_libraries
    ADD CONSTRAINT unknown_device_libraries_hash_id_fkey FOREIGN KEY (hash_id) REFERENCES public.library_hash(hash_id);


--
-- Name: upload_patterns_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.upload_patterns
    ADD CONSTRAINT upload_patterns_fkey FOREIGN KEY (device_id) REFERENCES public.device_pattern_status(device_id);


--
-- Name: vender_model_device_mapping_devices_device_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.vender_model_device_mapping
    ADD CONSTRAINT vender_model_device_mapping_devices_device_id_fkey FOREIGN KEY (device_id) REFERENCES public.devices(id);


--
-- Name: vulnerabilities_device_library_file_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.vulnerabilities
    ADD CONSTRAINT vulnerabilities_device_library_file_id_fkey FOREIGN KEY (hash_library_file_id) REFERENCES public.hash_library_files(id);


--
-- Name: vulnerabilities_device_library_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.vulnerabilities
    ADD CONSTRAINT vulnerabilities_device_library_id_fkey FOREIGN KEY (hash_library_id) REFERENCES public.hash_libraries(id);


--
-- Name: vulnerabilities_hash_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.vulnerabilities
    ADD CONSTRAINT vulnerabilities_hash_id_fkey FOREIGN KEY (hash_id) REFERENCES public.library_hash(hash_id);


--
-- Name: SCHEMA public; Type: ACL; Schema: -; Owner: postgres
--

REVOKE ALL ON SCHEMA public FROM PUBLIC;
REVOKE ALL ON SCHEMA public FROM postgres;
GRANT ALL ON SCHEMA public TO postgres;
GRANT ALL ON SCHEMA public TO PUBLIC;


--
-- Name: TABLE alembic_version; Type: ACL; Schema: public; Owner: postgres
--

REVOKE ALL ON TABLE public.alembic_version FROM PUBLIC;
REVOKE ALL ON TABLE public.alembic_version FROM postgres;
GRANT ALL ON TABLE public.alembic_version TO postgres;


--
-- Name: TABLE device_detailed_info; Type: ACL; Schema: public; Owner: postgres
--

REVOKE ALL ON TABLE public.device_detailed_info FROM PUBLIC;
REVOKE ALL ON TABLE public.device_detailed_info FROM postgres;
GRANT ALL ON TABLE public.device_detailed_info TO postgres;


--
-- Name: SEQUENCE device_detailed_info_id_seq; Type: ACL; Schema: public; Owner: postgres
--

REVOKE ALL ON SEQUENCE public.device_detailed_info_id_seq FROM PUBLIC;
REVOKE ALL ON SEQUENCE public.device_detailed_info_id_seq FROM postgres;
GRANT ALL ON SEQUENCE public.device_detailed_info_id_seq TO postgres;


--
-- Name: TABLE devices; Type: ACL; Schema: public; Owner: postgres
--

REVOKE ALL ON TABLE public.devices FROM PUBLIC;
REVOKE ALL ON TABLE public.devices FROM postgres;
GRANT ALL ON TABLE public.devices TO postgres;


--
-- Name: SEQUENCE devices_id_seq; Type: ACL; Schema: public; Owner: postgres
--

REVOKE ALL ON SEQUENCE public.devices_id_seq FROM PUBLIC;
REVOKE ALL ON SEQUENCE public.devices_id_seq FROM postgres;
GRANT ALL ON SEQUENCE public.devices_id_seq TO postgres;


--
-- Name: TABLE hash_libraries; Type: ACL; Schema: public; Owner: postgres
--

REVOKE ALL ON TABLE public.hash_libraries FROM PUBLIC;
REVOKE ALL ON TABLE public.hash_libraries FROM postgres;
GRANT ALL ON TABLE public.hash_libraries TO postgres;


--
-- Name: SEQUENCE hash_libraries_id_seq; Type: ACL; Schema: public; Owner: postgres
--

REVOKE ALL ON SEQUENCE public.hash_libraries_id_seq FROM PUBLIC;
REVOKE ALL ON SEQUENCE public.hash_libraries_id_seq FROM postgres;
GRANT ALL ON SEQUENCE public.hash_libraries_id_seq TO postgres;


--
-- Name: TABLE hash_library_file_mapping; Type: ACL; Schema: public; Owner: postgres
--

REVOKE ALL ON TABLE public.hash_library_file_mapping FROM PUBLIC;
REVOKE ALL ON TABLE public.hash_library_file_mapping FROM postgres;
GRANT ALL ON TABLE public.hash_library_file_mapping TO postgres;


--
-- Name: TABLE hash_library_files; Type: ACL; Schema: public; Owner: postgres
--

REVOKE ALL ON TABLE public.hash_library_files FROM PUBLIC;
REVOKE ALL ON TABLE public.hash_library_files FROM postgres;
GRANT ALL ON TABLE public.hash_library_files TO postgres;


--
-- Name: SEQUENCE hash_library_files_id_seq; Type: ACL; Schema: public; Owner: postgres
--

REVOKE ALL ON SEQUENCE public.hash_library_files_id_seq FROM PUBLIC;
REVOKE ALL ON SEQUENCE public.hash_library_files_id_seq FROM postgres;
GRANT ALL ON SEQUENCE public.hash_library_files_id_seq TO postgres;


--
-- Name: TABLE job_history; Type: ACL; Schema: public; Owner: postgres
--

REVOKE ALL ON TABLE public.job_history FROM PUBLIC;
REVOKE ALL ON TABLE public.job_history FROM postgres;
GRANT ALL ON TABLE public.job_history TO postgres;


--
-- Name: SEQUENCE job_history_id_seq; Type: ACL; Schema: public; Owner: postgres
--

REVOKE ALL ON SEQUENCE public.job_history_id_seq FROM PUBLIC;
REVOKE ALL ON SEQUENCE public.job_history_id_seq FROM postgres;
GRANT ALL ON SEQUENCE public.job_history_id_seq TO postgres;


--
-- Name: TABLE known_libraries; Type: ACL; Schema: public; Owner: postgres
--

REVOKE ALL ON TABLE public.known_libraries FROM PUBLIC;
REVOKE ALL ON TABLE public.known_libraries FROM postgres;
GRANT ALL ON TABLE public.known_libraries TO postgres;


--
-- Name: SEQUENCE known_libraries_id_seq; Type: ACL; Schema: public; Owner: postgres
--

REVOKE ALL ON SEQUENCE public.known_libraries_id_seq FROM PUBLIC;
REVOKE ALL ON SEQUENCE public.known_libraries_id_seq FROM postgres;
GRANT ALL ON SEQUENCE public.known_libraries_id_seq TO postgres;


--
-- Name: TABLE known_library_file_mapping; Type: ACL; Schema: public; Owner: postgres
--

REVOKE ALL ON TABLE public.known_library_file_mapping FROM PUBLIC;
REVOKE ALL ON TABLE public.known_library_file_mapping FROM postgres;
GRANT ALL ON TABLE public.known_library_file_mapping TO postgres;


--
-- Name: TABLE known_library_files; Type: ACL; Schema: public; Owner: postgres
--

REVOKE ALL ON TABLE public.known_library_files FROM PUBLIC;
REVOKE ALL ON TABLE public.known_library_files FROM postgres;
GRANT ALL ON TABLE public.known_library_files TO postgres;


--
-- Name: SEQUENCE known_library_files_id_seq; Type: ACL; Schema: public; Owner: postgres
--

REVOKE ALL ON SEQUENCE public.known_library_files_id_seq FROM PUBLIC;
REVOKE ALL ON SEQUENCE public.known_library_files_id_seq FROM postgres;
GRANT ALL ON SEQUENCE public.known_library_files_id_seq TO postgres;


--
-- Name: TABLE known_library_patterns; Type: ACL; Schema: public; Owner: postgres
--

REVOKE ALL ON TABLE public.known_library_patterns FROM PUBLIC;
REVOKE ALL ON TABLE public.known_library_patterns FROM postgres;
GRANT ALL ON TABLE public.known_library_patterns TO postgres;


--
-- Name: SEQUENCE known_library_patterns_id_seq; Type: ACL; Schema: public; Owner: postgres
--

REVOKE ALL ON SEQUENCE public.known_library_patterns_id_seq FROM PUBLIC;
REVOKE ALL ON SEQUENCE public.known_library_patterns_id_seq FROM postgres;
GRANT ALL ON SEQUENCE public.known_library_patterns_id_seq TO postgres;


--
-- Name: TABLE schedules; Type: ACL; Schema: public; Owner: postgres
--

REVOKE ALL ON TABLE public.schedules FROM PUBLIC;
REVOKE ALL ON TABLE public.schedules FROM postgres;
GRANT ALL ON TABLE public.schedules TO postgres;


--
-- Name: SEQUENCE schedules_id_seq; Type: ACL; Schema: public; Owner: postgres
--

REVOKE ALL ON SEQUENCE public.schedules_id_seq FROM PUBLIC;
REVOKE ALL ON SEQUENCE public.schedules_id_seq FROM postgres;
GRANT ALL ON SEQUENCE public.schedules_id_seq TO postgres;


--
-- Name: TABLE unknown_hash_libraries; Type: ACL; Schema: public; Owner: postgres
--

REVOKE ALL ON TABLE public.unknown_hash_libraries FROM PUBLIC;
REVOKE ALL ON TABLE public.unknown_hash_libraries FROM postgres;
GRANT ALL ON TABLE public.unknown_hash_libraries TO postgres;


--
-- Name: SEQUENCE unknown_hash_libraries_id_seq; Type: ACL; Schema: public; Owner: postgres
--

REVOKE ALL ON SEQUENCE public.unknown_hash_libraries_id_seq FROM PUBLIC;
REVOKE ALL ON SEQUENCE public.unknown_hash_libraries_id_seq FROM postgres;
GRANT ALL ON SEQUENCE public.unknown_hash_libraries_id_seq TO postgres;


--
-- Name: TABLE vulnerabilities; Type: ACL; Schema: public; Owner: postgres
--

REVOKE ALL ON TABLE public.vulnerabilities FROM PUBLIC;
REVOKE ALL ON TABLE public.vulnerabilities FROM postgres;
GRANT ALL ON TABLE public.vulnerabilities TO postgres;


--
-- Name: SEQUENCE vulnerabilities_id_seq; Type: ACL; Schema: public; Owner: postgres
--

REVOKE ALL ON SEQUENCE public.vulnerabilities_id_seq FROM PUBLIC;
REVOKE ALL ON SEQUENCE public.vulnerabilities_id_seq FROM postgres;
GRANT ALL ON SEQUENCE public.vulnerabilities_id_seq TO postgres;


--
-- PostgreSQL database dump complete
--

